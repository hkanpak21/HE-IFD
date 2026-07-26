// Command fhe-poc is a self-contained proof-of-concept that runs the HE-IFD
// protocol's ONLY server-side cryptographic operation
//
//	θ = θ₀ + Σ_i w_i · Δ_i ,   w_i = n_i / Σ_j n_j
//
// end-to-end under multiparty CKKS, and validates it against the plaintext
// float64 computation. It demonstrates:
//
//  1. DKG     — N parties each sample a secret key sk_i (ideal secret = Σ sk_i)
//     and jointly generate a collective public key (CKG protocol)
//     over a common reference polynomial. No single party holds the
//     decryption key.
//  2. Encrypt — each client encodes its cumulative displacement Δ_i (a length-d
//     float64 vector, chunked across ciphertexts of N_slots = ring/2)
//     and encrypts under the collective public key.
//  3. Aggregate (server, the only crypto op) — the server computes
//     θ₀ + Σ_i w_i·Δ_i using ONLY
//     plaintext-scalar × ciphertext   (the w_i scaling)  and
//     ciphertext + ciphertext         (accumulation, + θ₀ as plaintext).
//     Multiplicative depth = 1 (one PT×CT level consumed, one Rescale).
//     No ciphertext×ciphertext, no relinearization, no bootstrapping.
//  4. Threshold decrypt — the parties run a collective key-switch (CKS) from the
//     joint key to a zero target key, producing a ciphertext that
//     decrypts (decodes) to the result. No single party can decrypt
//     alone; a quorum (here all N, the N-out-of-N access structure)
//     is required.
//
// It then reports correctness (relative L2 error vs the plaintext reference)
// and the communication / ciphertext cost (ring degree, scale, depth,
// ciphertext count, bytes per ciphertext, total upload/download bytes, timings).
//
// Run:  go run .  [-d 5130] [-n 5] [-logn 14]
package main

import (
	"crypto/rand"
	"encoding/json"
	"flag"
	"fmt"
	"math"
	mrand "math/rand"
	"os"
	"time"

	"github.com/tuneinsight/lattigo/v6/core/rlwe"
	"github.com/tuneinsight/lattigo/v6/multiparty"
	"github.com/tuneinsight/lattigo/v6/ring"
	"github.com/tuneinsight/lattigo/v6/schemes/ckks"
	"github.com/tuneinsight/lattigo/v6/utils/sampling"
)

// config is one PoC scenario.
type config struct {
	d    int // head parameter dimension (length of each Δ_i)
	n    int // number of clients
	logN int // log2 ring degree
}

// result captures the validated correctness + cost numbers for one scenario.
type result struct {
	Scenario       string  `json:"scenario"`
	LattigoVersion string  `json:"lattigo_version"`
	D              int     `json:"d_head_params"`
	N              int     `json:"n_clients"`
	LogN           int     `json:"log_ring_degree"`
	RingDegree     int     `json:"ring_degree"`
	Slots          int     `json:"slots_per_ciphertext"`
	CtPerClient    int     `json:"ciphertexts_per_client"`
	LogScale       int     `json:"log_scale"`
	MultDepth      int     `json:"multiplicative_depth_used"`
	BytesPerCt     int     `json:"bytes_per_ciphertext_fresh"`
	UploadBytes    int     `json:"total_upload_bytes"`        // N clients × Δ ciphertexts
	DownloadBytes  int     `json:"total_download_bytes"`      // final result ciphertexts → all clients
	DecShareBytes  int     `json:"decrypt_share_bytes_total"` // CKS shares (threshold-decrypt traffic)
	RelL2Error     float64 `json:"relative_l2_error"`
	MaxAbsError    float64 `json:"max_abs_error"`
	Passed         bool    `json:"passed_1e-3"`
	EncryptMs      float64 `json:"client_encrypt_ms_total"`
	AggregateMs    float64 `json:"server_aggregate_ms"`
	DecryptMs      float64 `json:"threshold_decrypt_ms"`
	DkgMs          float64 `json:"dkg_keygen_ms"`
}

const lattigoVersion = "github.com/tuneinsight/lattigo/v6 v6.2.0"

func check(err error) {
	if err != nil {
		panic(err)
	}
}

func main() {
	var (
		dFlag               = flag.Int("d", 0, "single-scenario head dimension (0 = run default suite)")
		nFlag               = flag.Int("n", 0, "single-scenario client count")
		logNFlag            = flag.Int("logn", 14, "log2 ring degree")
		jsonOut             = flag.String("json", "", "optional path to write results JSON")
		serveFlag           = flag.Bool("serve", false, "run the Serve-mode encrypted-inference cost benchmark (collective refresh + threshold decrypt) instead of the Release-mode aggregation suite")
		serveArgmaxFlag     = flag.Bool("serve-argmax", false, "run the Serve-mode encrypted-argmax cost benchmark over C classes (collective-refresh-backed sign circuit)")
		serveTournamentFlag = flag.Bool("serve-tournament", false, "run the Serve-mode LOG-DEPTH tournament argmax (SIMD-packed rotate-and-Max; the QuickMax optimization)")
		commCostFlag        = flag.Bool("comm-cost", false, "measure the communication the protocol needs: key-generation shares, ciphertexts, key-switching shares, and refresh shares")
		protocolCostFlag    = flag.Bool("protocol-cost", false, "measure the operations the encrypted-serving protocol adds: ciphertext-by-ciphertext head application, encrypted reciprocal for the head merge, key switch to the querier, and selection scoring")
	)
	flag.Parse()

	// Serve mode (encrypted inference): measure the per-query cost atoms Release
	// mode does not pay — the collective refresh (multiparty bootstrap) and the
	// threshold decrypt. See serve.go.
	if *serveFlag {
		runServeSuite(*jsonOut)
		return
	}
	// Serve-mode ARGMAX (Job 2): full encrypted argmax over C classes, its
	// bootstraps wired to collective refreshes. See serve_argmax.go.
	if *serveArgmaxFlag {
		runArgmaxSuite(*jsonOut)
		return
	}
	// Serve-mode TOURNAMENT argmax (Job 3): log-depth SIMD-packed rotate-and-Max,
	// the QuickMax optimization. See serve_tournament.go.
	if *serveTournamentFlag {
		runTournamentSuite(*jsonOut)
		return
	}
	// The operations encrypted serving adds over Release-mode aggregation.
	// See protocol_cost.go.
	if *protocolCostFlag {
		runProtocolCost(*jsonOut)
		return
	}
	// Communication accounting, so that "one-shot" can be stated precisely.
	if *commCostFlag {
		runCommCost(*jsonOut)
		return
	}

	var scenarios []config
	if *dFlag > 0 && *nFlag > 0 {
		scenarios = []config{{d: *dFlag, n: *nFlag, logN: *logNFlag}}
	} else {
		// Default suite: head dims for a 512→10 head (d≈5130) and a 768→10
		// head (d≈7700), each at N∈{5,10}.
		scenarios = []config{
			{d: 5130, n: 5, logN: *logNFlag},
			{d: 5130, n: 10, logN: *logNFlag},
			{d: 7700, n: 5, logN: *logNFlag},
			{d: 7700, n: 10, logN: *logNFlag},
		}
	}

	results := make([]result, 0, len(scenarios))
	allPass := true
	for _, c := range scenarios {
		r := run(c)
		results = append(results, r)
		allPass = allPass && r.Passed
		printResult(r)
	}

	if *jsonOut != "" {
		b, err := json.MarshalIndent(results, "", "  ")
		check(err)
		check(os.WriteFile(*jsonOut, b, 0o644))
		fmt.Printf("\nwrote %s\n", *jsonOut)
	}

	if !allPass {
		fmt.Println("\nFAIL: at least one scenario exceeded the 1e-3 relative L2 bound")
		os.Exit(1)
	}
	fmt.Println("\nALL SCENARIOS PASSED (relative L2 ≤ 1e-3)")
}

// run executes one full DKG → encrypt → aggregate → threshold-decrypt cycle and
// validates it against the plaintext reference.
func run(c config) result {
	// ---- CKKS parameters --------------------------------------------------
	// LogQ chain: one 55-bit prime + a single 45-bit prime is sufficient — we
	// consume exactly one multiplicative level (the PT×CT scalar multiply,
	// followed by one Rescale). Depth = 1. P is the key-switch prime, needed by
	// the collective key-switch (decryption) step.
	params, err := ckks.NewParametersFromLiteral(ckks.ParametersLiteral{
		LogN:            c.logN,
		LogQ:            []int{55, 45},
		LogP:            []int{61},
		LogDefaultScale: 45,
	})
	check(err)

	slots := params.MaxSlots() // N/2 for the standard (conjugate-invariant off) ring
	ctPerClient := (c.d + slots - 1) / slots

	// ---- synthetic protocol inputs ---------------------------------------
	// Realistic magnitudes: cumulative displacements Δ_i are small (~1e-2),
	// θ₀ is O(1). Sample sizes n_i drive the weights w_i.
	rng := mrand.New(mrand.NewSource(20260529))
	theta0 := make([]float64, c.d)
	for j := range theta0 {
		theta0[j] = rng.NormFloat64() * 0.3
	}
	deltas := make([][]float64, c.n)
	sampleSizes := make([]int, c.n)
	for i := 0; i < c.n; i++ {
		deltas[i] = make([]float64, c.d)
		for j := 0; j < c.d; j++ {
			deltas[i][j] = rng.NormFloat64() * 0.02
		}
		sampleSizes[i] = 100 + rng.Intn(900) // heterogeneous client data sizes
	}
	totalSamples := 0
	for _, s := range sampleSizes {
		totalSamples += s
	}
	weights := make([]float64, c.n)
	for i := range weights {
		weights[i] = float64(sampleSizes[i]) / float64(totalSamples)
	}

	// ---- plaintext reference: θ = θ₀ + Σ_i w_i·Δ_i ------------------------
	ref := make([]float64, c.d)
	copy(ref, theta0)
	for i := 0; i < c.n; i++ {
		w := weights[i]
		for j := 0; j < c.d; j++ {
			ref[j] += w * deltas[i][j]
		}
	}

	// ---- shared CRS (common reference string) -----------------------------
	prng, err := sampling.NewKeyedPRNG([]byte("he-ifd-fhe-poc-crs"))
	check(err)
	crs := prng

	encoder := ckks.NewEncoder(params)

	// =======================================================================
	// 1. DKG: N parties sample sk_i, jointly build the collective public key.
	//    Ideal secret key s = Σ_i sk_i (never reconstructed in the clear).
	// =======================================================================
	tDkg := time.Now()
	kgen := rlwe.NewKeyGenerator(params)
	sks := make([]*rlwe.SecretKey, c.n)
	for i := 0; i < c.n; i++ {
		sks[i] = kgen.GenSecretKeyNew()
	}

	ckg := multiparty.NewPublicKeyGenProtocol(params)
	ckgCRP := ckg.SampleCRP(crs)
	ckgCombined := ckg.AllocateShare()
	for i := 0; i < c.n; i++ {
		share := ckg.AllocateShare()
		ckg.GenShare(sks[i], ckgCRP, &share)
		if i == 0 {
			ckgCombined = share
		} else {
			ckg.AggregateShares(share, ckgCombined, &ckgCombined)
		}
	}
	collectivePK := rlwe.NewPublicKey(params)
	ckg.GenPublicKey(ckgCombined, ckgCRP, collectivePK)
	dkgMs := float64(time.Since(tDkg).Microseconds()) / 1000.0

	encryptor := rlwe.NewEncryptor(params, collectivePK)

	// =======================================================================
	// 2. ENCRYPT: each client encrypts its Δ_i as ctPerClient ciphertexts.
	// =======================================================================
	encDeltas := make([][]*rlwe.Ciphertext, c.n) // encDeltas[i][chunk]
	var encryptMs float64
	t0 := time.Now()
	for i := 0; i < c.n; i++ {
		encDeltas[i] = encryptVector(params, encoder, encryptor, deltas[i], slots, ctPerClient)
	}
	encryptMs = float64(time.Since(t0).Microseconds()) / 1000.0

	bytesPerCt := encDeltas[0][0].BinarySize()

	// =======================================================================
	// 3. AGGREGATE (server, the ONLY crypto op):  θ₀ + Σ_i w_i·Δ_i
	//    PT-scalar × CT  (the w_i multiply, +1 level, then Rescale)
	//    CT + CT         (accumulation across clients, and adding θ₀ plaintext)
	//    Multiplicative depth used = 1.
	// =======================================================================
	evaluator := ckks.NewEvaluator(params, nil) // nil eval keys: no relin needed
	t0 = time.Now()
	aggCts := make([]*rlwe.Ciphertext, ctPerClient)
	for chunk := 0; chunk < ctPerClient; chunk++ {
		var acc *rlwe.Ciphertext
		for i := 0; i < c.n; i++ {
			// PT(scalar w_i) × CT  — depth 1.
			scaled, err := evaluator.MulNew(encDeltas[i][chunk], weights[i])
			check(err)
			check(evaluator.Rescale(scaled, scaled)) // consume the level, restore scale
			if i == 0 {
				acc = scaled
			} else {
				check(evaluator.Add(acc, scaled, acc)) // CT + CT
			}
		}
		// + θ₀ chunk as a plaintext (PT + CT), encoded at the post-rescale scale/level.
		theta0Chunk := chunkSlice(theta0, chunk, slots)
		pt := ckks.NewPlaintext(params, acc.Level())
		pt.Scale = acc.Scale
		check(encoder.Encode(theta0Chunk, pt))
		check(evaluator.Add(acc, pt, acc))
		aggCts[chunk] = acc
	}
	aggregateMs := float64(time.Since(t0).Microseconds()) / 1000.0
	multDepth := params.MaxLevel() - aggCts[0].Level() // levels consumed = 1

	// =======================================================================
	// 4. THRESHOLD DECRYPT: collective key-switch from the joint key to a zero
	//    target key. Each party contributes a CKS share built from sk_i; the
	//    aggregate switches the ciphertext to be decryptable under sk_zero = 0
	//    (i.e. the masked plaintext can be decoded directly). No single party
	//    can do this alone — all N shares are required (N-out-of-N).
	// =======================================================================
	// Smudging noise for the collective key-switch. The canonical choice (the
	// library's own multiparty tests) is 8×the fresh-encryption noise: large
	// enough to statistically hide each party's secret-key contribution, small
	// enough that the decoded result keeps full float64-grade precision.
	sigmaSmudging := 8 * rlwe.DefaultNoise
	cks, err := multiparty.NewKeySwitchProtocol(params, ring.DiscreteGaussian{Sigma: sigmaSmudging, Bound: 6 * sigmaSmudging})
	check(err)
	zeroSk := rlwe.NewSecretKey(params) // sk_output = 0
	decShareBytes := 0
	t0 = time.Now()
	result := make([]float64, 0, c.d)
	for chunk := 0; chunk < ctPerClient; chunk++ {
		ct := aggCts[chunk]
		combined := cks.AllocateShare(ct.Level())
		for i := 0; i < c.n; i++ {
			share := cks.AllocateShare(ct.Level())
			cks.GenShare(sks[i], zeroSk, ct, &share)
			if chunk == 0 {
				decShareBytes += share.BinarySize()
			}
			if i == 0 {
				combined = share
			} else {
				check(cks.AggregateShares(share, combined, &combined))
			}
		}
		switched := ckks.NewCiphertext(params, 1, ct.Level())
		cks.KeySwitch(ct, combined, switched)
		// switched is now decryptable under sk_output = 0: decode directly.
		dec := rlwe.NewDecryptor(params, zeroSk)
		pt := dec.DecryptNew(switched)
		vals := make([]float64, slots)
		check(encoder.Decode(pt, vals))
		take := slots
		if remaining := c.d - chunk*slots; remaining < slots {
			take = remaining
		}
		result = append(result, vals[:take]...)
	}
	decryptMs := float64(time.Since(t0).Microseconds()) / 1000.0

	// ---- validation: relative L2 error vs plaintext reference -------------
	var num, den, maxAbs float64
	for j := 0; j < c.d; j++ {
		e := result[j] - ref[j]
		num += e * e
		den += ref[j] * ref[j]
		if a := math.Abs(e); a > maxAbs {
			maxAbs = a
		}
	}
	relL2 := math.Sqrt(num) / math.Sqrt(den)

	uploadBytes := c.n * ctPerClient * bytesPerCt
	downloadBytes := c.n * ctPerClient * bytesPerCt // result broadcast to all N clients

	return result_(c, params, slots, ctPerClient, bytesPerCt, uploadBytes,
		downloadBytes, decShareBytes*ctPerClient, relL2, maxAbs, multDepth,
		encryptMs, aggregateMs, decryptMs, dkgMs)
}

// result_ assembles the result struct (kept separate to keep run() readable).
func result_(c config, params ckks.Parameters, slots, ctPerClient, bytesPerCt,
	uploadBytes, downloadBytes, decShareBytes int, relL2, maxAbs float64,
	multDepth int, encMs, aggMs, decMs, dkgMs float64) result {
	return result{
		Scenario:       fmt.Sprintf("d=%d N=%d logN=%d", c.d, c.n, c.logN),
		LattigoVersion: lattigoVersion,
		D:              c.d,
		N:              c.n,
		LogN:           c.logN,
		RingDegree:     params.N(),
		Slots:          slots,
		CtPerClient:    ctPerClient,
		LogScale:       int(math.Round(math.Log2(params.DefaultScale().Float64()))),
		MultDepth:      multDepth,
		BytesPerCt:     bytesPerCt,
		UploadBytes:    uploadBytes,
		DownloadBytes:  downloadBytes,
		DecShareBytes:  decShareBytes,
		RelL2Error:     relL2,
		MaxAbsError:    maxAbs,
		Passed:         relL2 <= 1e-3,
		EncryptMs:      encMs,
		AggregateMs:    aggMs,
		DecryptMs:      decMs,
		DkgMs:          dkgMs,
	}
}

// encryptVector encodes v (length d) into ctPerClient CKKS ciphertexts of `slots`
// slots each, encrypted under the collective public key.
func encryptVector(params ckks.Parameters, encoder *ckks.Encoder, enc *rlwe.Encryptor,
	v []float64, slots, ctPerClient int) []*rlwe.Ciphertext {
	cts := make([]*rlwe.Ciphertext, ctPerClient)
	for chunk := 0; chunk < ctPerClient; chunk++ {
		pt := ckks.NewPlaintext(params, params.MaxLevel())
		check(encoder.Encode(chunkSlice(v, chunk, slots), pt))
		ct, err := enc.EncryptNew(pt)
		check(err)
		cts[chunk] = ct
	}
	return cts
}

// chunkSlice returns the `chunk`-th window of `slots` values from v, zero-padded
// if v runs out.
func chunkSlice(v []float64, chunk, slots int) []float64 {
	out := make([]float64, slots)
	start := chunk * slots
	for j := 0; j < slots && start+j < len(v); j++ {
		out[j] = v[start+j]
	}
	return out
}

func printResult(r result) {
	fmt.Printf("\n── scenario %s ──────────────────────────────\n", r.Scenario)
	fmt.Printf("  ring degree           : %d (logN=%d), %d slots/ct\n", r.RingDegree, r.LogN, r.Slots)
	fmt.Printf("  log2 scale            : %d\n", r.LogScale)
	fmt.Printf("  multiplicative depth  : %d\n", r.MultDepth)
	fmt.Printf("  ciphertexts/client    : %d  (d=%d over %d slots)\n", r.CtPerClient, r.D, r.Slots)
	fmt.Printf("  bytes/ciphertext      : %s\n", human(r.BytesPerCt))
	fmt.Printf("  total upload (N=%d)    : %s\n", r.N, human(r.UploadBytes))
	fmt.Printf("  total download (N=%d)  : %s\n", r.N, human(r.DownloadBytes))
	fmt.Printf("  decrypt-share traffic : %s\n", human(r.DecShareBytes))
	fmt.Printf("  DKG keygen time       : %.1f ms\n", r.DkgMs)
	fmt.Printf("  encrypt time (all i)  : %.1f ms\n", r.EncryptMs)
	fmt.Printf("  server aggregate time : %.1f ms\n", r.AggregateMs)
	fmt.Printf("  threshold decrypt time: %.1f ms\n", r.DecryptMs)
	fmt.Printf("  relative L2 error     : %.3e   (max abs %.3e)\n", r.RelL2Error, r.MaxAbsError)
	fmt.Printf("  PASS (≤1e-3)          : %v\n", r.Passed)
}

func human(b int) string {
	const u = 1024.0
	f := float64(b)
	switch {
	case f >= u*u:
		return fmt.Sprintf("%.2f MiB (%d B)", f/(u*u), b)
	case f >= u:
		return fmt.Sprintf("%.2f KiB (%d B)", f/u, b)
	default:
		return fmt.Sprintf("%d B", b)
	}
}

// ensure crypto/rand is linked (collective protocols draw secure randomness via
// the keyed PRNG above; this keeps the import explicit for auditors).
var _ = rand.Reader
