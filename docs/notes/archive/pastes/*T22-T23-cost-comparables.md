# T22 and T23. Published comparables for the cost figures

Written 2026-08-19. Answers the meeting of 2026-08-07, which asked for a
published number beside the 5 MiB per query and beside the per-query latency.

Nothing under `docs/paper/` was edited. Everything below is a paste block.

Every competitor number is copied from `comparators/REPORTED_RESULTS.md`. Every
one of our numbers names the record it came from.

---

## Part 1. T22. The expansion factor, worked

### Inputs

| quantity | value | file |
|---|---|---|
| ring degree of the communication table | $2^{14}$, so $8{,}192$ slots | `results/fhe_serve/cost_grid.json`, `log_n: 14`, `slots: 8192` |
| ciphertext at full level | 2,097,582 bytes | `results/fhe_serve/comm_cost.json`, `ciphertext_bytes_full_level` |
| ciphertext at level 1 | 524,622 bytes | same file, `ciphertext_bytes_level_1` |
| key-switch share at level 1 | 262,168 bytes | same file, `key_switch_share_bytes_level_1` |
| feature dimension $d$ | 768 | `docs/paper/sections/experiments.tex` line 620, "769 queries here", which is $d+1$. RoBERTa-base and ViT-B/16 both give 768 |
| Hyb-Agg plaintext, uplink, factor | 524,288 bytes, 6.3 MB, about 12 | `comparators/REPORTED_RESULTS.md` section 15, paper lines 876-895, verbatim |
| Hyb-Agg at small dimension | about 24 near $d \approx 4{,}095$ | same section, paper lines 888-890, verbatim |

### The plaintext being protected

The client uploads its feature vector. In Hyb-Agg's own currency, 8-byte doubles,

```
768 x 8 = 6,144 bytes
```

The answer that comes back is one class index. As a double that is 8 bytes.

### The arithmetic

Uplink, which is the quantity Hyb-Agg measures:

```
2,097,582 / 6,144  =  341.4 x
```

Whole query, matching the 5.0 MiB row of Table VII:

```
uploaded query          2,097,582
returned label            524,622
ten key-switch shares   2,621,680   (10 x 262,168)
                        ---------
total                   5,243,884 bytes  =  5.0010 MiB      <- Table VII agrees

plaintext protected     6,144 + 8 = 6,152 bytes

5,243,884 / 6,152  =  852.4 x
```

Slot occupancy:

```
768 / 8,192 = 9.4 per cent of the slots are used
```

The batched floor, which is arithmetic on the two records above and not a
measurement:

```
full ciphertext plaintext   8,192 x 8 = 65,536 bytes
2,097,582 / 65,536  =  32.0 x   (uplink)
5,243,884 / 65,544  =  80.0 x   (whole query)
```

Hyb-Agg's own check reproduces from their quoted figures, so the two ratios are
computed the same way:

```
6,300,000 / 524,288 = 12.0 x
```

### What this says, honestly

Our uplink expands by **341 times**, against Hyb-Agg's 12. The whole query
expands by 852 times. Neither number is flattering and neither should be hidden.

The cause is not the protocol. It is that a CKKS ciphertext at a given ring
degree costs a fixed number of bytes whatever it carries, and our query fills
9.4 per cent of the slots. Hyb-Agg documents the same effect in its own paper and
reports about 24 near $d \approx 4{,}095$ for exactly this reason. Their 12 is
measured at $d = 65{,}536$, a vector that fills the ciphertext. Ours is measured
at $d = 768$.

**Would batching close the gap.** Filling all 8,192 slots would put the uplink
factor at 32, which is within a factor of three of Hyb-Agg. **We did not measure
that.** The serving measurement answers one query at a time, and packing several
queries into one ciphertext interacts with the rotation structure of the argmax
tournament, which we have not tested. The 32 above is arithmetic on the ciphertext
size and the slot count, nothing more.

**Do not use a flattering denominator.** Two are available and both should be
refused. Encoding the features as float32 gives 3,072 bytes and a factor of 683,
which is worse. Using the full slot capacity as the denominator gives 32, which
measures a protocol we do not run.

---

## Part 2. T22 paste block

**File** `docs/paper/sections/experiments.tex`.
**Roughly line 524.** This is an insertion, not a replacement.

Place the new text **between** these two existing sentences, which are the last
sentence of the communication paragraph and the opening of the next paragraph.

```
before   ...One key generation of
         $15.5$\,MiB therefore replaces $510$\,MiB on every subsequent query.

         \paragraph{Correctness} The decrypted result matches the plaintext computation to
```

**Recommended text, three sentences.**

```latex
A ciphertext at ring degree $2^{14}$ occupies $2.0$\,MiB whatever it carries, so
uploading a $768$ dimension feature vector expands the $6{,}144$ bytes it takes in
plaintext by a factor of $341$, and it fills $768$ of the $8{,}192$ slots the ring
provides. Hyb-Agg reports about $12$ for a vector that fills its ciphertext, and
about $24$ near dimension $4{,}095$, where the unused slots begin to
dominate~\cite{kemmaka2025hybagg}. Filling all $8{,}192$ slots would put our factor
at $32$, and we do not measure a batched arrangement.
```

**Shorter variant, one sentence, if the PIs want the smallest possible change.**
I advise against this one. It states the unflattering ratio and drops the reason.

```latex
A ciphertext at ring degree $2^{14}$ occupies $2.0$\,MiB whatever it carries, so
the uploaded query expands a $768$ dimension feature vector by a factor of $341$,
where Hyb-Agg reports about $12$ for a vector that fills its
ciphertext~\cite{kemmaka2025hybagg}.
```

`kemmaka2025hybagg` is already in `refs.bib` at line 658 and is already cited in
`related.tex` at line 74, so no bibliography change is needed.

**POSEIDON is not used here.** `comparators/REPORTED_RESULTS.md` section 8 marks
its 0.38 communication figure as "likely GB" under a heading that says the column
semantics are a user-verified interpretive reading and still need caption
transcription. The unit is not confirmed, so the number cannot enter the paper.

---

## Part 3. T23. The latency comparison, checked

### Their numbers, from `comparators/REPORTED_RESULTS.md` section 16

Table 2, NN20, Scenario 3, verbatim.

| parties | latency (s) | throughput (samples/s) |
|---|---|---|
| 3 | 245.58 | 1.19 |
| 5 | 238.15 | 1.22 |
| 10 | 278.19 | 1.05 |
| 20 | 354.17 | 0.82 |

Figure 5, amortized per sample with distributed bootstrapping, 0.84 / 0.82 / 0.95
/ 1.21 s at 3 / 5 / 10 / 20 parties.

Hardware, paper Section 6.1, verbatim: local cluster, 20 ms network delay, 1 Gbps,
Ubuntu 22.04, **12-core Intel Xeon E5-2680 2.5 GHz, 256 GB RAM**.

### The thing that must not be left out

Latency times throughput is constant across all four rows.

```
245.58 x 1.19 = 292.2
238.15 x 1.22 = 290.5
278.19 x 1.05 = 292.1
354.17 x 0.82 = 290.4
```

**Their reported latency covers a batch of about 292 samples.** Putting our
$31.5$\,s beside their $245.58$\,s without saying so would overstate our result by
roughly two orders of magnitude. Their per-sample figure at ten parties is about
$0.95$\,s. Ours is $31.5$\,s for one query at four classes.

### Our numbers

$31.5$\,s at four classes and $113.2$\,s at a hundred, at $\Nc = 10$ and ring
degree $2^{15}$, from `results/fhe_serve/cost_grid.json` and
`results/fhe_serve/argmax_tournament.csv`. Single threaded and unbatched, which
`experiments.tex` line 384 already states as "on one core".

### Hardware, ours

Not comparable, and we cannot state ours precisely. `results/fhe_serve/README.md`
says the runs used the VALAR `t4_ai` partition on the CPU path with no GPU. No CPU
model, clock or core count is recorded anywhere in the repository. The paper says
"a commodity CPU" and "on one core". So the honest statement in the paper is the
core count, one against twelve, and not the machine.

### Where the work sits

Their latency covers a twenty-layer convolutional network evaluated end to end
under encryption on a handwritten-digit task. Ours covers one linear map plus an
encrypted argmax, and they run no argmax at all, since they return the score
vector. The two systems pay in different places. A straight latency ranking is
not meaningful and should not be attempted.

### The interface difference, priced from our own record

`docs/paper/sections/experiments.tex` line 620 states that a logit interface is
recovered exactly in $769$ queries against $1.2\times10^{4}$ to $2.0\times10^{5}$
for labels, from `results/extraction_budget/results.csv`. So the label interface
costs an adversary between 16 and 260 times more than the score vector they
return.

---

## Part 4. T23 paste block

**File** `docs/paper/sections/experiments.tex`.
**Roughly line 390.** This is an insertion, not a replacement.

Place the new text **between** these two existing sentences, at the end of the
"What one query costs, end to end" paragraph and before the paragraph on levers.

```
before   The tournament costs about $16$\,s per round and needs
         $\lceil\log_2\Cc\rceil$ rounds, against the fourteenfold larger sequential fold.

         Three levers apply to that figure, and they differ in what they move.
```

**Recommended text, two sentences.** It carries the batching, the amortization,
the core count and the interface, so nothing is left implicit.

```latex
Against the closest published system, slytHErin evaluates a twenty-layer network
under the same multiparty arrangement in $245.58$\,s at three parties and
$354.17$\,s at twenty, batched on twelve cores and returning the score
vector~\cite{intoci2023slytherin}, where our $31.5$\,s and $113.2$\,s cover one
unbatched query on one core and return only the label, which \cref{sec:exp-leak}
shows costs an adversary between $16$ and $260$ times more to recover. Their batch
amortizes to about $0.95$\,s per sample at ten parties, and their cost lies in the
network where ours lies in the argmax, so the two figures size the setting rather
than rank the systems.
```

**Longer variant, three sentences,** if the PIs want the machines named.

```latex
slytHErin is the closest published system, since it also holds the model under a
multiparty CKKS key, never decrypts it, and key-switches only to the
querier~\cite{intoci2023slytherin}. It evaluates a twenty-layer network in
$245.58$\,s at three parties and $354.17$\,s at twenty, batched on twelve cores
and returning the score vector, where we evaluate one linear map and an encrypted
argmax in $31.5$\,s at four classes and $113.2$\,s at a hundred, unbatched on one
core and returning only the label, which \cref{sec:exp-leak} shows costs an
adversary between $16$ and $260$ times more to recover. Their batch amortizes to
about $0.95$\,s per sample at ten parties, and the two machines are not the same,
so the pair sizes the setting rather than ranking the systems.
```

`intoci2023slytherin` is already in `refs.bib` at line 1065 and is already cited
in `related.tex` at line 188, so no bibliography change is needed.

**Overlap to check.** `related.tex` lines 185 to 197 already state both
differences in words, that slytHErin evaluates the whole network and that it
returns the score vector, and it already points at `\cref{sec:exp-leak}`. The
paste above repeats that in order to carry the numbers. If the PIs find the
repetition heavy, the fix is to cut the mechanism from the experiments sentence
and keep only the numbers and the two caveats.

---

## Part 5. Does each comparison help us

### T22, the expansion factor. **Neutral, and helpful only if framed correctly.**

As a bare ratio it hurts. 341 against 12 reads badly.

As a property of the scheme it helps, and it answers the comment that was
actually made. The meeting said 5 MiB "looks sketchy", meaning it looked like a
number we chose. The framing above shows it is the price of one ciphertext at a
given ring degree, that Hyb-Agg's own paper reports the same effect at small
dimension, and that our factor sits where their analysis predicts a small vector
would sit. That converts 5 MiB from a suspicious choice into an unavoidable unit.

Recommendation. Include the three-sentence version. Do not include the one
sentence version, which states the ratio and withholds the reason.

### T23, the latency. **Mixed, and it hurts if the batching is dropped.**

It helps in two ways. It shows a published system in the same trust model, which
answers any reviewer who thinks encrypted serving under a multiparty key is
untried. And our interface is strictly harder to attack, which our own Section 5.6
prices at 16 to 260 times.

It hurts in one way that the PIs should see clearly. Their published latency
covers a batch of about 292 samples, so their real per-sample cost is about
$0.95$\,s at ten parties against our $31.5$\,s. On throughput we are about 33
times behind, doing far less network work. Anyone who reads slytHErin will find
this, so the paper should state it before a reviewer does.

Recommendation. Include the recommended two-sentence version, which concedes the
amortized figure. If the PIs would rather not concede it, the honest alternative
is to drop the comparison entirely rather than quote the batch latency alone.

---

## Part 6. What I could not verify

1. **The ring degree of Table VII.** The communication table is stated at ring
   degree $2^{14}$, and `comm_cost.json` only records `log_n: 14`. The argmax runs
   at $2^{15}$, per `argmax_tournament.csv`. If the query ciphertext has to live in
   the deeper chain that the argmax consumes, the uplink is larger than 2.0 MiB
   and the expansion factor above is a lower bound. No record holds the
   ring degree $2^{15}$ communication figures, so this cannot be settled from
   `results/`. **This is the one item I would check before the paste goes in.**
2. **The key-switch share row.** Table VII's 2.5 MiB uses
   `key_switch_share_bytes_level_1`, 262,168 bytes each. `cost_grid.json` also
   holds `key_switch_share_bytes_total` of 20,975,820 at the same setting, which is
   ten full-level ciphertexts. The level-1 choice looks right, since the key switch
   acts on the level-1 label ciphertext, but the two records differ by a factor of
   eight on that row and the paper does not say which it used. A reviewer comparing
   the two files would ask.
3. **The 15.5 MiB of bootstrapping key material and the 49 s to generate it**,
   which the paragraph directly above my T22 insertion states, have no record under
   `results/`. I searched `results/fhe_serve`, `results/fhe_gpu` and
   `results/fhe_freeze_a`. Outside the scope of T22, flagged because the new text
   sits next to it.
4. **Our CPU.** No model, clock or core count is recorded anywhere. Only "VALAR
   `t4_ai`, CPU path" in `results/fhe_serve/README.md`. The paste therefore says
   "on one core" and does not name the machine.
5. **POSEIDON's 0.38 communication figure.** Unit not confirmed.
   `comparators/REPORTED_RESULTS.md` marks it "likely GB" and flags the whole
   column reading as needing caption transcription. Not used.
6. **slytHErin's batch size of about 292** is derived by me from their Table 2,
   latency times throughput, not stated verbatim in their paper. The paste blocks
   avoid it and quote their amortized per-sample figure instead, which is verbatim
   from Figure 5.
