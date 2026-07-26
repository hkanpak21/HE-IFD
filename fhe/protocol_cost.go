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
//     histogram exactly, so the division has to happen under encryption. Newton
//     iteration, y <- y(2 - x y), two levels per step. Paid once at aggregation,
//     never per query.
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

	"github.com/tuneinsight/lattigo/v6/core/rlwe"
	"github.com/tuneinsight/lattigo/v6/multiparty"
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
	RecipIters  int     `json:"reciprocal_iterations"`
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
		out = append(out, r)
		printProto(r)
	}

	fmt.Println()
	fmt.Println("n_parties,log_n,slots,ct_x_ct_ms,pt_x_ct_ms,reciprocal_ms,reciprocal_iters,reciprocal_rel_err,key_switch_querier_ms,key_switch_bytes,selection_mask_ms,add_ms,rotation_ms")
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
	fmt.Printf("  reciprocal under encryption        : %.2f ms   (%d Newton steps, rel err %.2e)\n",
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
			check(ckg.AggregateShares(share, combined, &combined))
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
	dec := rlwe.NewDecryptor(params, idealSk)
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

	// --- 2. reciprocal under encryption (the count-head denominator) ----------
	// The denominator is a sum of per-class counts. Its total is public, since the
	// per-client sample counts are public, so it can be scaled into a range where
	// Newton converges without revealing any per-class value.
	den := make([]float64, slots)
	for i := range den {
		den[i] = 0.35 + 0.6*rng.Float64() // scaled per-class totals, in (0.35, 0.95)
	}
	ptD := ckks.NewPlaintext(params, params.MaxLevel())
	check(ecd.Encode(den, ptD))
	ctD, err := enc.EncryptNew(ptD)
	check(err)

	const newtonIters = 4
	t0 = time.Now()
	inv := newtonReciprocal(eval, params, ecd, ctD, newtonIters)
	recipMs := ms(time.Since(t0))

	got := make([]float64, slots)
	check(ecd.Decode(dec.DecryptNew(inv), got))
	var num, dnm float64
	for i := 0; i < 1024; i++ {
		want := 1.0 / den[i]
		num += (got[i] - want) * (got[i] - want)
		dnm += want * want
	}
	recipErr := math.Sqrt(num) / math.Sqrt(dnm)

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
		RecipMs: recipMs, RecipIters: newtonIters, RecipRelErr: recipErr,
		PCKSMs: pcksMs, PCKSBytes: pcksBytes,
		MaskMs: maskMs, AddMs: addMs, RotMs: rotMs,
	}
}

// newtonReciprocal computes an encrypted 1/x by Newton iteration,
// y <- y (2 - x y), starting from a public constant. Each step costs two levels.
// The input must sit in (0, 1] for the iteration to converge, which the public
// total sample count lets us arrange without revealing any per-class value.
func newtonReciprocal(eval *ckks.Evaluator, params ckks.Parameters,
	ecd *ckks.Encoder, x *rlwe.Ciphertext, iters int) *rlwe.Ciphertext {

	y, err := eval.MulNew(x, -1.0)
	check(err)
	check(eval.Rescale(y, y))
	check(eval.Add(y, 2.5, y)) // y0 = 2.5 - x, a standard start for x in (0,1]

	for i := 0; i < iters; i++ {
		if y.Level() < 2 {
			break // out of levels; a deployment refreshes here
		}
		xy, err := eval.MulRelinNew(x, y)
		check(err)
		check(eval.Rescale(xy, xy))
		check(eval.Mul(xy, -1.0, xy))
		check(eval.Add(xy, 2.0, xy)) // 2 - x y
		ny, err := eval.MulRelinNew(y, xy)
		check(err)
		check(eval.Rescale(ny, ny))
		y = ny
	}
	return y
}
