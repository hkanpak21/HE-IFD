# Malicious security: what is impossible, and what replaces it

Working note, 2026-07-30. Not paper text yet. It replaces the bare assumption in
`sections/security.tex` under "Why the assumption is needed".

## The problem, restated

Threshold decryption is a protocol the clients run on a ciphertext that the
serving party **presents**. The prescribed ciphertext holds one label. A
malicious coalition can present a different ciphertext, such as a row of the
encrypted head, and collect the honest client's share for that instead.

The current text calls this an assumption and states the single-slot mask as a
mitigation. That is weak. The stronger reading is that the strict functionality
is **not realizable**, and the paper should prove it rather than assume around
it.

## Part 1. The strict functionality is not realizable

`F` returns labels and nothing else. An honest client would have to refuse a
request whose plaintext is not a prescribed label. It cannot.

**Proposition 1 (no plaintext gate from a ciphertext).**
Let honest client `h` decide by a polynomial-time predicate `D` on its view
whether to contribute its key-switching share for a presented ciphertext `c`.
Suppose the rest of `h`'s view is independent of the plaintext under `c`. If the
scheme is IND-CPA against an adversary holding `N-1` key shares, then for every
pair of plaintexts `m0` and `m1`,

    | Pr[D(view with Enc(m0)) = 1] - Pr[D(view with Enc(m1)) = 1] | <= negl(lambda).

*Proof.* A gap gives an IND-CPA distinguisher that holds one key share. One is
at most `N-1`, so the assumed IND-CPA security applies directly. **QED**

**What it says.** The honest client releases its share for both plaintexts or
for neither. It cannot release for a label and refuse for a head row. No
protocol of this message pattern realizes `F` against a malicious serving party.
The assumption in the current draft is therefore necessary, not convenient.

**What it does not say.** The proposition constrains predicates on the
*plaintext*. A predicate on the *ciphertext* escapes it, and Part 3 uses that.

## Part 2. The functionality that is realizable

Replace `F` with a functionality whose answers are slots rather than labels.

**`F_mask`.** Same setup, training and selection as `F`. Serving changes.

    On (evaluate, E, P) from the serving party, where E is an arithmetic circuit
    over the stored encrypted values and the public parameters:
      if the total allowance is spent, return bottom;
      otherwise charge one unit, evaluate E, and return the value in the
      designated slot of E's output to party P alone.

An honest query is the special case in which `E` is the prescribed serving
circuit and `P` is the querier. The label appears in the designated slot, so
`F_mask` and `F` agree on honest behaviour. A deviating request is a different
`E`, and it returns one scalar of the coalition's choosing.

**Theorem 3 (realization, with abort).** Assume multiparty CKKS is IND-CPA
against an adversary holding `N-1` key shares, and assume every upload carries a
proof of knowledge of its plaintext. Then the protocol with the single-slot mask
realizes `F_mask` with abort, against a malicious adversary corrupting the
server, the serving party and up to `N-1` clients.

*Proof sketch.* The simulator extracts the corrupted clients' displacements from
the proofs of knowledge and sends them to `F_mask`. It simulates the honest
clients' uploads as encryptions of zero, indistinguishable by the hybrid of
Theorem 1. For each presented ciphertext it reads the circuit `E` from the
adversary's evaluation transcript, forwards `(evaluate, E, P)` to `F_mask`,
receives the slot value, and simulates the key-switching transcript on it. An
honest client that receives a malformed message aborts, and the simulator aborts
in the same case. **QED**

**Why the mask is binding with a single honest client.** Every client multiplies
the presented ciphertext by the same public single-slot mask before it computes
its share. Shares computed on different ciphertexts do not combine: the sum
decrypts to noise. One honest client therefore forces every successful
decryption to be of a masked ciphertext. The coalition cannot skip the mask, it
can only choose the circuit that fills the slot.

**Corollary (the allowance still binds).** Each charged request returns one slot,
so `Q_tot` requests return at most `Q_tot` scalars. The shared head holds `C*d`
parameters. A slot carries about 40 bits at our parameters, so a request returns
at most a small constant number of parameters' worth of information. Recovering
the head therefore costs on the order of `C*d` requests, which is the order
Section 5.6 measures for label-only extraction. **Deviating buys a constant
factor and not a change of order.**

## Part 3. Closing the gap by recomputation

Proposition 1 blocks predicates on the plaintext. It does not block a client that
checks **where the ciphertext came from**.

**Proposition 2 (the serving circuit is publicly recomputable).** The serving
circuit is a deterministic function of values every client can hold: the
encrypted head, the encrypted query, the evaluation keys and the public
parameters. Addition, ciphertext multiplication with relinearization, rescaling,
rotation and the comparison circuits are all deterministic. Bootstrapping is
deterministic because the protocol restores levels under collectively generated
bootstrapping keys rather than by collective refresh. A client can therefore
recompute the prescribed output ciphertext and compare it, as a string, with the
one presented.

This is worth stating in the paper for a second reason. The choice of
single-key bootstrapping over collective refresh was made in Section 5.4 to save
510 MiB of traffic per query. That choice is what makes the serving circuit
deterministic, and therefore verifiable. The traffic argument and the security
argument select the same design.

**Theorem 4 (verification realizes the strict functionality).** If every client
recomputes the serving circuit and contributes its share only on a match, then
the protocol realizes `F` with abort against the same adversary.

*Cost.* One full serving evaluation per verifying client per query. Section 5.4
puts that under two minutes at a hundred classes on one CPU core, plus the 2.0
MiB query ciphertext delivered to each verifier.

## Part 4. Spot-checking, and why it is nearly free here

Full verification is affordable but not cheap. Random verification is, and the
structure of the attack makes it strong.

**Theorem 5 (compounding deterrence).** Let each honest client verify each
request independently with probability `p`. An adversary that makes `k`
deviating requests escapes detection with probability at most `(1-p)^(h k)`,
where `h >= 1` is the number of honest clients. By the corollary of Part 2,
recovering the head needs `k` on the order of `C*d`. The campaign is therefore
detected except with probability negligible in `C*d`.

The threat model's binding case is a coalition of `N-1`, so `h = 1`. Even then:

| task | `C*d` | `p = 0.001` | `p = 0.01` |
|---|---|---|---|
| AG-News   | 3 072  | 4.6e-2  | 3.9e-14  |
| DBpedia   | 10 752 | 2.1e-5  | 1.2e-47  |
| Banking77 | 59 136 | 2.0e-26 | 7.6e-259 |

Read the cells as the probability that a full extraction campaign goes
unnoticed. At a one percent check rate the expected overhead is one percent of a
serving evaluation per query, which is about 1.2 s at a hundred classes, and
0.02 MiB of extra traffic against the 5.0 MiB the query already costs.

**The asymmetry is the point.** One deviating request is cheap to hide and worth
almost nothing, because it returns one scalar. A campaign worth running needs
thousands of requests, and thousands of independent checks at any positive rate
are not survivable. The defence is cheap exactly because the attack is long.

## What to put in the paper

Replace the "Why the assumption is needed" and "Bounding a deviating request"
paragraphs with:

1. Proposition 1 and its two-line proof. The strict functionality is out of
   reach, and this is a property of encryption rather than of our design.
2. `F_mask`, Theorem 3 and the corollary. This is the guarantee we actually
   deliver, stated as a simulation result rather than a game.
3. Proposition 2, Theorem 4 and Theorem 5 as the closing options, with their
   measured costs. Say plainly that we did not implement them.

**What this still does not give.** Correctness. A malicious client that uploads a
crafted displacement biases the shared head, and none of the above detects it.
That stays in the limitations, where it already is.

**One assumption is new.** Theorem 3 needs a proof of knowledge of the plaintext
on each upload, so that the simulator can extract. Sigma protocols for RLWE
ciphertexts are standard and cheap. We do not implement one, and the paper must
say so.

**Question to settle.** Whether to keep the content game of Definition 2 beside
Theorem 3. Theorem 3 is stronger and standard. The game is easier to read. Two
statements of the same guarantee may cost more space than they earn.
