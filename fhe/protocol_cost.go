// protocol_cost.go — the operations the encrypted-serving protocol needs that the
// Release-mode aggregation never paid for. Four of them are new:
//
//  1. HEAD APPLICATION under a private query. The client encrypts its features,
//     so the head is applied ciphertext-by-ciphertext, not plaintext-by-ciphertext.
//     Costs one relinearization and one rescale on top of the multiply. This is
//     what buys query privacy: the serving party never sees phi(x), so it cannot
//     invert the features back to the client's input.
//
//  2. RECIPROCAL under encryption. The count-weighted head merge divides by the
//     per-class totals. Decrypting that denominator would let a coalition of N-1
//     clients subtract its own counts and recover the honest client's class
//     histogram exactly, so the division has to happen under encryption. Lattigo's
//     inversion circuit over the positive domain, with its bootstraps served by
//     collective refreshes. Paid once at aggregation, never per query.
//
//  3. KEY SWITCH TO THE QUERIER. The label must reach the client that asked and
//     nobody else. Switching to the querier's public key lets the other clients
//     contribute decryption shares without learning the answer.
//
//  4. SELECTION SCORING. One plaintext-mask multiply to pick out the logit of the
//     true class, then one comparison against the encrypted maximum. The client
//     knows its own label, so the mask is public and the multiply stays at depth
//     one. Summing the indicators and decrypting a single scalar is what lets the
//     federation choose between candidates without seeing either of them.
//
// Rates are measured per operation and every reported configuration is computed
// from them, which is how the Release-mode costs were reported.
package main

import (
	"encoding/json"
	"fmt"
	"math"
	"math/rand"
	"os"
	"time"

	"github.com/tuneinsight/lattigo/v6/circuits/ckks/inverse"
	"github.com/tuneinsight/lattigo/v6/circuits/ckks/minimax"
	"github.com/tuneinsight/lattigo/v6/core/rlwe"
	"github.com/tuneinsight/lattigo/v6/multiparty"
	"github.com/tuneinsight/lattigo/v6/multiparty/mpckks"
	"github.com/tuneinsight/lattigo/v6/ring"
	"github.com/tuneinsight/lattigo/v6/schemes/ckks"
	"github.com/tuneinsight/lattigo/v6/utils/sampling"
)

type protoResult struct {
	N           int     `json:"n_parties"`
	LogN        int     `json:"log_n"`
	Slots       int     `json:"slots"`
	CtxCtMs     float64 `json:"ct_x_ct_mul_relin_rescale_ms"`
	PtxCtMs     float64 `json:"pt_x_ct_mul_rescale_ms"`
	RecipMs     float64 `json:"encrypted_reciprocal_ms"`
	RecipIters  int     `json:"reciprocal_refreshes"`
	RecipRelErr float64 `json:"reciprocal_rel_err"`
	PCKSMs      float64 `json:"key_switch_to_querier_ms"`
	PCKSBytes   int     `json:"key_switch_share_bytes_total"`
	MaskMs      float64 `json:"selection_mask_ms"`
	AddMs       float64 `json:"ciphertext_add_ms"`
	RotMs       float64 `json:"rotation_ms"`
}

// ---------------------------------------------------------------------------

func runProtocolCost(jsonPath string) {
	fmt.Println("=== encrypted-serving protocol: per-operation cost ===")
	fmt.Println()
	var out []protoResult
	for _, n := range []int{5, 10, 20} {
		r := measureProtocol(n, 14)
		fmt.Printf("  measuring the encrypted reciprocal at N=%d ...\n", n)
		r.RecipMs, r.RecipIters, r.RecipRelErr = measureReciprocal(n, 15)
		out = append(out, r)
		printProto(r)
	}

	fmt.Println()
	fmt.Println("n_parties,log_n,slots,ct_x_ct_ms,pt_x_ct_ms,reciprocal_ms,reciprocal_refreshes,reciprocal_rel_err,key_switch_querier_ms,key_switch_bytes,selection_mask_ms,add_ms,rotation_ms")
	for _, r := range out {
		fmt.Printf("%d,%d,%d,%.3f,%.3f,%.2f,%d,%.3e,%.2f,%d,%.3f,%.4f,%.3f\n",
			r.N, r.LogN, r.Slots, r.CtxCtMs, r.PtxCtMs, r.RecipMs, r.RecipIters,
			r.RecipRelErr, r.PCKSMs, r.PCKSBytes, r.MaskMs, r.AddMs, r.RotMs)
	}
	if jsonPath != "" {
		b, _ := json.MarshalIndent(out, "", "  ")
		check(os.WriteFile(jsonPath, b, 0o644))
		fmt.Printf("\nwrote %s\n", jsonPath)
	}
}

func printProto(r protoResult) {
	fmt.Printf("N=%d  (ring 2^%d, %d slots)\n", r.N, r.LogN, r.Slots)
	fmt.Printf("  head applied to an encrypted query : %.3f ms   (ct x ct, relin + rescale)\n", r.CtxCtMs)
	fmt.Printf("  head applied to a plaintext query  : %.3f ms   (pt x ct, for contrast)\n", r.PtxCtMs)
	fmt.Printf("  reciprocal under encryption        : %.2f ms   (%d collective refreshes, rel err %.2e)\n",
		r.RecipMs, r.RecipIters, r.RecipRelErr)
	fmt.Printf("  key switch to the querier          : %.2f ms   (%s of shares)\n", r.PCKSMs, human(r.PCKSBytes))
	fmt.Printf("  selection mask + accumulate        : %.3f ms\n", r.MaskMs)
	fmt.Printf("  ciphertext addition                : %.4f ms\n", r.AddMs)
	fmt.Println()
}

// ---------------------------------------------------------------------------

func measureProtocol(n, logN int) protoResult {
	params, err := ckks.NewParametersFromLiteral(ckks.ParametersLiteral{
		LogN:            logN,
		LogQ:            []int{55, 45, 45, 45, 45, 45, 45, 45},
		LogP:            []int{61},
		LogDefaultScale: 45,
	})
	check(err)
	slots := params.MaxSlots()

	// --- distributed key generation: collective public key + evaluation keys ---
	kgen := rlwe.NewKeyGenerator(params)
	sks := make([]*rlwe.SecretKey, n)
	for i := range sks {
		sks[i] = kgen.GenSecretKeyNew()
	}
	crs, err := sampling.NewKeyedPRNG([]byte("he-oft-protocol-cost"))
	check(err)

	ckg := multiparty.NewPublicKeyGenProtocol(params)
	ckgCRP := ckg.SampleCRP(crs)
	var combined multiparty.PublicKeyGenShare
	for i := 0; i < n; i++ {
		share := ckg.AllocateShare()
		ckg.GenShare(sks[i], ckgCRP, &share)
		if i == 0 {
			combined = share
		} else {
			ckg.AggregateShares(share, combined, &combined)
		}
	}
	pk := rlwe.NewPublicKey(params)
	ckg.GenPublicKey(combined, ckgCRP, pk)

	// The ideal secret exists only for the correctness checks below; the protocol
	// never forms it. Relinearization keys would be generated collectively in a
	// deployment, which costs a one-time round and does not change per-op timings.
	idealSk := rlwe.NewSecretKey(params)
	ringQP := params.RingQP()
	for i := 0; i < n; i++ {
		ringQP.Add(idealSk.Value, sks[i].Value, idealSk.Value)
	}
	ikgen := rlwe.NewKeyGenerator(params)
	rlk := ikgen.GenRelinearizationKeyNew(idealSk)
	gks := ikgen.GenGaloisKeysNew([]uint64{params.GaloisElement(1)}, idealSk)
	evk := rlwe.NewMemEvaluationKeySet(rlk, gks...)

	enc := rlwe.NewEncryptor(params, pk)
	ecd := ckks.NewEncoder(params)
	eval := ckks.NewEvaluator(params, evk)

	rng := rand.New(rand.NewSource(1))
	vecA := make([]float64, slots)
	vecB := make([]float64, slots)
	for i := range vecA {
		vecA[i] = rng.Float64()*2 - 1
		vecB[i] = rng.Float64()*2 - 1
	}
	ptA := ckks.NewPlaintext(params, params.MaxLevel())
	ptB := ckks.NewPlaintext(params, params.MaxLevel())
	check(ecd.Encode(vecA, ptA))
	check(ecd.Encode(vecB, ptB))
	ctA, err := enc.EncryptNew(ptA)
	check(err)
	ctB, err := enc.EncryptNew(ptB)
	check(err)

	const reps = 20

	// --- 1. head applied to an ENCRYPTED query: ct x ct + relin + rescale -----
	t0 := time.Now()
	for i := 0; i < reps; i++ {
		p, err := eval.MulRelinNew(ctA, ctB)
		check(err)
		check(eval.Rescale(p, p))
	}
	ctxct := ms(time.Since(t0)) / reps

	// --- head applied to a PLAINTEXT query, for contrast ----------------------
	t0 = time.Now()
	for i := 0; i < reps; i++ {
		p, err := eval.MulNew(ctA, ptB)
		check(err)
		check(eval.Rescale(p, p))
	}
	ptxct := ms(time.Since(t0)) / reps

	// --- ciphertext addition and rotation ------------------------------------
	t0 = time.Now()
	for i := 0; i < reps; i++ {
		_, err := eval.AddNew(ctA, ctB)
		check(err)
	}
	addMs := ms(time.Since(t0)) / reps

	t0 = time.Now()
	for i := 0; i < reps; i++ {
		_, err := eval.RotateNew(ctA, 1)
		check(err)
	}
	rotMs := ms(time.Since(t0)) / reps

	// --- 3. key switch to the querier's public key ---------------------------
	// Every client contributes a share, but the result is re-encrypted under the
	// asking client's key, so only that client can decrypt the label.
	querierSk := kgen.GenSecretKeyNew()
	querierPk := kgen.GenPublicKeyNew(querierSk)
	pcks, err := multiparty.NewPublicKeySwitchProtocol(params,
		ring.DiscreteGaussian{Sigma: 8 * rlwe.DefaultNoise, Bound: 48 * rlwe.DefaultNoise})
	check(err)
	pcksBytes := 0
	t0 = time.Now()
	var pcksAgg multiparty.PublicKeySwitchShare
	for i := 0; i < n; i++ {
		share := pcks.AllocateShare(ctA.Level())
		pcks.GenShare(sks[i], querierPk, ctA, &share)
		if i == 0 {
			pcksAgg = share
			pcksBytes = share.BinarySize() * n
		} else {
			check(pcks.AggregateShares(share, pcksAgg, &pcksAgg))
		}
	}
	switched := ckks.NewCiphertext(params, 1, ctA.Level())
	pcks.KeySwitch(ctA, pcksAgg, switched)
	pcksMs := ms(time.Since(t0))

	// --- 4. selection scoring: plaintext mask, then accumulate ---------------
	// The client knows its own label, so the one-hot mask is public and the
	// multiply stays at depth one.
	mask := make([]float64, slots)
	for i := range mask {
		if i%16 == 0 {
			mask[i] = 1
		}
	}
	ptM := ckks.NewPlaintext(params, ctA.Level())
	check(ecd.Encode(mask, ptM))
	acc, err := eval.MulNew(ctA, ptM)
	check(err)
	t0 = time.Now()
	for i := 0; i < reps; i++ {
		p, err := eval.MulNew(ctA, ptM)
		check(err)
		check(eval.Add(acc, p, acc))
	}
	maskMs := ms(time.Since(t0)) / reps

	return protoResult{
		N: n, LogN: logN, Slots: slots,
		CtxCtMs: ctxct, PtxCtMs: ptxct,
		PCKSMs: pcksMs, PCKSBytes: pcksBytes,
		MaskMs: maskMs, AddMs: addMs, RotMs: rotMs,
	}
}

// ---------------------------------------------------------------------------
// The encrypted reciprocal, measured on the deep chain the sign circuit needs.
//
// The count-weighted head merge divides the accumulated numerator by the
// per-class totals. Those totals are the sum of every client's per-class count,
// so decrypting them would let a coalition of N-1 clients subtract its own
// counts and read the remaining client's class histogram. The division is
// therefore evaluated under encryption, with Lattigo's inversion circuit over
// the positive domain, and its bootstraps are collective refreshes.
//
// This is a one-time cost at aggregation. It is not paid per query.
func measureReciprocal(n, logN int) (float64, int, float64) {
	logQ := []int{55}
	for i := 0; i < 14; i++ {
		logQ = append(logQ, 45)
	}
	params, err := ckks.NewParametersFromLiteral(ckks.ParametersLiteral{
		LogN: logN, LogQ: logQ, LogP: []int{61, 61}, LogDefaultScale: 45,
	})
	check(err)

	kgen := rlwe.NewKeyGenerator(params)
	sks := make([]*rlwe.SecretKey, n)
	for i := range sks {
		sks[i] = kgen.GenSecretKeyNew()
	}
	crs, err := sampling.NewKeyedPRNG([]byte("he-oft-reciprocal"))
	check(err)

	ckg := multiparty.NewPublicKeyGenProtocol(params)
	ckgCRP := ckg.SampleCRP(crs)
	var combined multiparty.PublicKeyGenShare
	for i := 0; i < n; i++ {
		share := ckg.AllocateShare()
		ckg.GenShare(sks[i], ckgCRP, &share)
		if i == 0 {
			combined = share
		} else {
			ckg.AggregateShares(share, combined, &combined)
		}
	}
	pk := rlwe.NewPublicKey(params)
	ckg.GenPublicKey(combined, ckgCRP, pk)

	idealSk := rlwe.NewSecretKey(params)
	ringQP := params.RingQP()
	for i := 0; i < n; i++ {
		ringQP.Add(idealSk.Value, sks[i].Value, idealSk.Value)
	}
	ikgen := rlwe.NewKeyGenerator(params)
	rlk := ikgen.GenRelinearizationKeyNew(idealSk)
	evk := rlwe.NewMemEvaluationKeySet(rlk)

	minLevel, logBound, ok := mpckks.GetMinimumLevelForRefresh(128, params.DefaultScale(), n, params.Q())
	if !ok {
		panic("no valid refresh level for the reciprocal chain")
	}
	rfp, err := mpckks.NewRefreshProtocol(params, uint(params.LogDefaultScale()), params.Xe())
	check(err)
	btp := &collectiveBootstrapper{
		params: params, sks: sks, rfp: rfp, crs: crs,
		minLevel: minLevel, logBound: logBound,
	}

	enc := rlwe.NewEncryptor(params, pk)
	dec := rlwe.NewDecryptor(params, idealSk)
	ecd := ckks.NewEncoder(params)
	eval := ckks.NewEvaluator(params, evk)
	invEval := inverse.NewEvaluator(params, minimax.NewEvaluator(params, eval, btp))

	// Per-class totals, rescaled by the public federation size into (2^-6, 1].
	// The total number of examples is public, since the per-client sample counts
	// are public, so this normalisation reveals no per-class value.
	slots := params.MaxSlots()
	rng := rand.New(rand.NewSource(7))
	den := make([]float64, slots)
	for i := range den {
		den[i] = 0.02 + 0.97*rng.Float64()
	}
	pt := ckks.NewPlaintext(params, params.MaxLevel())
	check(ecd.Encode(den, pt))
	ct, err := enc.EncryptNew(pt)
	check(err)

	t0 := time.Now()
	inv, err := invEval.EvaluatePositiveDomainNew(ct, -6.0, 0.0)
	check(err)
	elapsed := ms(time.Since(t0))

	got := make([]float64, slots)
	check(ecd.Decode(dec.DecryptNew(inv), got))
	var num, dnm float64
	for i := 0; i < 2048; i++ {
		want := 1.0 / den[i]
		num += (got[i] - want) * (got[i] - want)
		dnm += want * want
	}
	return elapsed, btp.count, math.Sqrt(num) / math.Sqrt(dnm)
}
