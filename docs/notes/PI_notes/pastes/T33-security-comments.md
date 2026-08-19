# T33. Sinem Sav's comments on Section IV. Find and replace list

Answers items **T17**, **T18** and **T19** of `docs/plan/paper-todo-2026-08-19.md`,
which carry Sav's Overleaf comments of 17 August, 11:19 am to 11:24 am.

Nothing here is applied to `docs/paper/`. Each entry gives the file, the
approximate line, the current text verbatim, and the replacement. Every `FIND`
block was machine-checked to occur exactly once in the file it names. Paste in
file order.

## What changes

| what | where |
|---|---|
| the threshold assumption moves out of Section IV into `sec:mhe` | S1, M1 |
| the section roadmap loses the moved subsection and the word "fixes" | S1 |
| "No party receives $\thstar$" moves from Outputs into the store | S3, S4 |
| the functionality body is simplified, step 1 renamed | S5 |
| ELSA and FULLSA cited for the form of the functionality | S2, B1 |
| "describes what a trusted party would do" rephrased | S2 |
| the phase-signal justification moves below the float | S2, S6 |
| two question headings become noun phrases | S15, S16 |
| shortening pass over the rest of Section IV | S7 to S14 |
| "separates into three cases" made plain (not my file) | X1 |

## Counts

Counted in source words, meaning whitespace-separated tokens of the `.tex`
files, so LaTeX commands count too. Measured by applying every block below to a
copy of each file.

| what | count |
|---|---|
| Section IV up to `sec:malicious-ext`, now | 1633 words |
| the same region after these blocks | 1443 words |
| removed from that region | 190 words |
| of which the relocated threshold subsection | 127 words |
| net shortening of the region, move set aside | 63 words |
| added to `sec:mhe` by the move | 127 words |
| net change to the manuscript | 65 words shorter |
| gross words cut across the sixteen blocks | 218 |
| gross words added across the sixteen blocks | 26 |
| antithesis sites removed while shortening | 5 |
| `FIND` anchors that occur exactly once | 19 of 19 |
| cross-references broken | 0 |

Read the two numbers separately. The move is neutral to the page count and takes
127 words off Section IV, which is what Sav asked for. The shortening pass cuts
218 words of prose and puts 26 back, of which 22 are the ELSA and FULLSA
sentence that T18 requires and the rest is the store clause of **S3**. The
manuscript ends 65 words shorter, which is about four lines of a column.

That is a modest number and it is deliberate. Section IV is a theorem, two
proofs and a proposition, and the passages that look cuttable are the ones a
reviewer reads hardest. Section E lists the three cuts that would have saved
more and changed what is proved.

## Claims checked and left alone

Nothing below weakens a claim. Three shortenings were considered and rejected
for that reason, and they are listed at the end.

---

# A. `sections/security.tex`

## S1. The roadmap, and the relocation of the threshold assumption, lines 4 to 33

Answers T17 (Sav, 11:20 am, "this is more like a preliminary") and T19's
"fixes" (Sav, 11:19 am). The three paragraphs deleted here are pasted into
`sections/method.tex` by **M1** with only their two pointers changed. Section IV
then opens on the ideal functionality, which is what the section is for.

FIND

```latex
This section states what the protocol guarantees. \Cref{sec:threshold} fixes the
threshold assumption. \Cref{sec:ideal} gives an ideal functionality.
\Cref{sec:semihonest} proves that the protocol realizes it against semi-honest
parties. \Cref{sec:malicious} bounds what a malicious client coalition learns
about an honest client's data. \Cref{sec:malicious-ext} explains why the serving
party is assumed honest and what would remove that assumption.
\Cref{sec:inherent} separates the guarantees the cryptography provides from the
leakage the task itself carries.

\subsection{The Threshold Assumption}
\label{sec:threshold}

The construction is stated for a $\tc$-out-of-$\Nc$ threshold CKKS scheme with
$2\le\tc\le\Nc$. Encryption is under a single collective public key. Decryption
requires partial decryption shares from at least $\tc$ clients, and any set of at
most $\tc-1$ clients learns nothing about a plaintext. Key generation,
key switching and collective refresh are the threshold protocols of the same
scheme.

Two consequences follow, and the protocol uses both. Any $\tc$ clients form a
quorum, so serving does not require every client to be online. Any $\tc-1$
clients are powerless against a ciphertext, so $\tc-1$ is the corruption bound
throughout this section.

Our implementation instantiates $\tc=\Nc$, which is the setting the multiparty
CKKS library provides, and the measurements of \cref{sec:exp-cost} are taken
there. Every statement below holds for general $\tc$.

\subsection{The Ideal Functionality}
\label{sec:ideal}
```

REPLACE

```latex
This section states what the protocol guarantees. \Cref{sec:ideal} gives an
ideal functionality. \Cref{sec:semihonest} proves that the protocol realizes it
against semi-honest parties. \Cref{sec:malicious} bounds what a malicious client
coalition learns about an honest client's data. \Cref{sec:malicious-ext} shows
that the serving party must be honest and what would remove that requirement.
\Cref{sec:inherent} separates what the cryptography guarantees from what the
task itself leaks.

\subsection{The Ideal Functionality}
\label{sec:ideal}
```

**Cross-reference audit for `sec:threshold`.** One reference exists in the whole
manuscript, `\Cref{sec:threshold}` at `security.tex` line 4, and this block
deletes it. `\label{sec:threshold}` is therefore not carried into
`method.tex`, because a label nothing points at is a warning waiting to happen.
Anything that later needs to point at the threshold text points at
`sec:mhe`. Checked across `main.tex` and all six section files, with no
`\nameref` anywhere and no section title quoted in prose.

Two soft references survive the move and stay correct as they stand.
`related.tex` line 80 already says "The threshold structure of \cref{sec:mhe}",
which becomes more accurate after the move, not less. `experiments.tex` line 700
says "\Cref{sec:security} states the protocol for a $\tc$-out-of-$\Nc$
threshold", which still holds, since every theorem in Section IV is stated for
general $\tc$. Changing it to `sec:mhe` would also be defensible and I did not
propose it, because it is not broken.

## S2. The opening of `sec:ideal`, around line 35

Answers T19b (Sav, 11:20 am, "informal, rephrase"), T19c (Sav, 11:21 am, "is
this info required for Section C?") and T18.3 and T18.4, the citation. The
phase-signal sentence is not cut, it moves below the float, where the leakage
field it explains has already been read. See **S6**.

FIND

```latex
\Cref{func:ideal} describes what a trusted party would do, so that the protocol
can be measured against it. The server and the serving party are entities outside
the functionality rather than part of it, so that either may be considered
corrupt. The functionality signals the end of each phase with an explicit
message, because the parties need to know when to proceed and that signal is
itself observable.
```

REPLACE

```latex
\Cref{func:ideal} defines the ideal functionality $\Fhe$ against which the
protocol is measured. The server and the serving party are entities outside
$\Fhe$, so either may be corrupt. The form of the functionality follows the
secure aggregation functionality of ELSA~\cite{rathee2023elsa}, and placing the
aggregator outside it follows FULLSA~\cite{karakoc2024fullsa}.
```

**On the phase-signal judgement.** It stays in the paper. The signals are part
of $\Fhe$, they appear in every step, and they appear in the leakage field, so
the reader needs to know why they are there. Sav's complaint is about position,
not content. At the head of the subsection the sentence explains a field the
reader has not seen. Below the float it sits next to the only other leakage
remark, which is where the same question arises. Cutting it would leave the
leakage field unexplained, so it moves rather than goes.

## S3. The Parameters field of Functionality 1, around line 50

Answers T18.1 (Sav, 11:22 am, "then this is not the output. it is a
requirement"). She is right. In the ELSA and FULLSA form the fact that $\Fhe$
withholds a stored value is a property of the store, and the Outputs field lists
only what parties receive. The meaning is unchanged, and it is now stated once
instead of twice.

FIND

```latex
$\Cc$. The parties are clients $P_1,\dots,P_{\Nc}$, an aggregation server $S$ and
a serving party $V$, none of which is part of $\Fhe$. The functionality holds a
counter $q_j$ for each client, each initialised to $0$, and a store that is
initially empty.
```

REPLACE

```latex
$\Cc$. The parties are clients $P_1,\dots,P_{\Nc}$, an aggregation server $S$ and
a serving party $V$, none of which is part of $\Fhe$. The functionality holds a
counter $q_j$ for each client, each initialised to $0$, and a store that is
initially empty and that $\Fhe$ never sends to any party.
```

## S4. The Outputs field of Functionality 1, around line 57

The other half of T18.1. Paste **S3** and **S4** together or neither.

FIND

```latex
\noindent\textbf{\emph{Outputs.}} No party receives $\thstar$. Every party
receives the selected index $a^{\star}$ and the phase signals. Client $P_j$
receives one label for each of its first $Q$ queries, and $\bot$ afterwards.
```

REPLACE

```latex
\noindent\textbf{\emph{Outputs.}} Every party receives the selected index
$a^{\star}$ and the phase signals. Client $P_j$ receives one label for each of
its first $Q$ queries, and $\bot$ afterwards.
```

## S5. Steps 1 and 2 of Functionality 1, around line 63

Answers T18.2, the meeting's "merge training and aggregation", read as the
direction of 2026-08-19 says to read it, as a wording pass. Step 1 already does
both, so its name now says so. "to $S$, to $V$ and to every client" is exactly
"to every party" by the Parameters field, so the short form loses nothing. Step
1 no longer says "send it to no party", because **S3** now says that of the
whole store.

FIND

```latex
\item \emph{Training.} On $(\mathsf{Train},\Dj)$ from every client, run the local
  training of \cref{alg:train} on each $\Dj$, form the shared head $\thstar$ of
  \cref{eq:aggregate}, store it, and send it to no party. Send
  $(\mathsf{Done},\mathsf{train})$ to $S$, to $V$ and to every client.
\item \emph{Selection.} On $(\mathsf{Select})$ from $S$, evaluate the estimator
  of \cref{eq:estimator} for both servable arrangements and send the index
  $a^{\star}$ of the larger to every party. Send
  $(\mathsf{Done},\mathsf{select})$ to $S$, to $V$ and to every client.
```

REPLACE

```latex
\item \emph{Training and aggregation.} On $(\mathsf{Train},\Dj)$ from every
  client, run the local training of \cref{alg:train} on each $\Dj$ and store the
  shared head $\thstar$ of \cref{eq:aggregate}. Send
  $(\mathsf{Done},\mathsf{train})$ to every party.
\item \emph{Selection.} On $(\mathsf{Select})$ from $S$, evaluate the estimator
  of \cref{eq:estimator} for both servable arrangements, send the index
  $a^{\star}$ of the larger to every party, and send
  $(\mathsf{Done},\mathsf{select})$ to every party.
```

Step 3 is not touched. It is the only step whose message pattern is not uniform,
since the label goes to $P_j$ alone and the signal goes to $V$ alone, and that
asymmetry is the point of the design.

## S6. The two remarks after the float, around line 83

Receives the phase-signal sentence from **S2**, and shortens the three-properties
paragraph.

FIND

```latex
The sample counts sit in the leakage because the protocol uses them as public
scalars, and we prove security relative to that.

Three properties of $\Fhe$ deserve statement, because they are what the protocol
must reproduce. No party ever holds $\thstar$. The only value the whole
federation learns is one index. A client learns the labels it asks for, and
nothing else, up to its allowance.
```

REPLACE

```latex
The sample counts sit in the leakage because the protocol uses them as public
scalars. The phase signals sit there because the parties need them to know when
to proceed and anyone watching the network sees them. We prove security relative
to both.

Three properties of $\Fhe$ are what the protocol must reproduce. No party ever
holds $\thstar$. The only value the whole federation learns is one index. A
client learns the labels it asks for, up to its allowance, and nothing else.
```

## S7. After the semi-honest definition, around line 111

Shortening. "by construction" and "resulting" carry nothing.

FIND

```latex
The simulator receives the answers because the protocol delivers them by
construction. A definition that withheld them would be unachievable, and the
resulting theorem would say nothing about a system that answers questions.
```

REPLACE

```latex
The simulator receives the answers because the protocol delivers them. A
definition that withheld them would be unachievable, and the theorem would say
nothing about a system that answers questions.
```

## S8. The Setup part of the proof sketch, around line 128

Shortening only.

FIND

```latex
\emph{Setup.} The simulator runs the distributed key generation with the
corrupted parties, playing the honest clients on uniformly chosen shares. The
transcript of that protocol is simulatable by the security of the key-generation
protocol, and the resulting collective public key is distributed identically.
```

REPLACE

```latex
\emph{Setup.} The simulator runs the distributed key generation with the
corrupted parties, playing the honest clients on uniformly chosen shares. That
transcript is simulatable by the security of the key-generation protocol, and
the collective public key is distributed identically.
```

## S9. The Training part of the proof sketch, around line 135

Shortening only. The dropped clause "the number and position of these
invocations are public and" is already implied by "fixed points in the circuit
that do not depend on any plaintext", which is the sentence that does the work.

FIND

```latex
argument replaces the honest ciphertexts one at a time, and each neighbouring
pair of hybrids is indistinguishable by IND-CPA against $\tc-1$ shares, which is
the assumption of the theorem.

The server's additions and its multiplication by the reciprocal are
deterministic functions of those ciphertexts and of public scalars, so the
simulator computes them as the server does. The encrypted reciprocal is not such
a function. Its inversion circuit consumes levels and restores them by collective
refresh, and a collective refresh is an interactive protocol in which the
participating clients contribute fresh randomness. The simulator therefore
invokes the simulator of the refresh protocol for each of the two refreshes,
playing the honest clients on that protocol's simulated shares. Both refreshes
occur at fixed points in the circuit that do not depend on any plaintext, so the
number and position of these invocations are public and the simulator knows them
in advance.
```

REPLACE

```latex
argument replaces the honest ciphertexts one at a time, and each neighbouring
pair of hybrids is indistinguishable by IND-CPA against $\tc-1$ shares, the
assumption of the theorem.

The server's additions and its multiplication by the reciprocal are
deterministic functions of those ciphertexts and of public scalars, so the
simulator computes them as the server does. The encrypted reciprocal is not such
a function. Its inversion circuit consumes levels and restores them by
collective refresh, an interactive protocol in which the participating clients
contribute fresh randomness. The simulator therefore invokes the simulator of
the refresh protocol for each of the two refreshes, playing the honest clients
on that protocol's simulated shares. Both refreshes sit at fixed points in the
circuit that do not depend on any plaintext, so the simulator knows their number
and position in advance.
```

## S10. The Selection and serving part of the proof sketch, around line 150

Shortening only.

FIND

```latex
\emph{Selection and serving.} The selection step decrypts one value. The
simulator takes that index from $\Leak$ and produces the collective
key-switching transcript for it by the simulator of the key-switching protocol.
```

REPLACE

```latex
\emph{Selection and serving.} The selection step decrypts one value. The
simulator takes that index from $\Leak$ and produces the collective
key-switching transcript for it from that protocol's simulator.
```

## S11. The opening of `sec:malicious`, around line 168

Shortening, and it removes an antithesis of the kind the meeting banned,
"necessary rather than convenient". The new sentence says the same thing by
naming what `sec:malicious-ext` proves.

FIND

```latex
\Cref{thm:semihonest} assumes every party follows the protocol. We now let the
clients deviate. The server and the serving party remain honest, and
\cref{sec:malicious-ext} explains why that assumption is necessary rather than
convenient. We bound what a deviating coalition learns about the data of a
client that does not deviate. We do not claim correctness. A client that uploads
a crafted displacement can bias the shared head, and \cref{sec:scope} discusses
that separately.
```

REPLACE

```latex
\Cref{thm:semihonest} assumes every party follows the protocol. We now let the
clients deviate, and \cref{sec:malicious-ext} shows why the server and the
serving party must stay honest. We bound what a deviating coalition learns about
the data of a client that does not deviate. We do not claim correctness. A
client that uploads a crafted displacement can bias the shared head, and
\cref{sec:scope} discusses that.
```

## S12. After the content game, around line 190

Removes an antithesis. The second sentence already says why the restriction is
necessary, so "rather than cosmetic" was arguing with a reader who has not
objected yet.

FIND

```latex
The equal-size restriction is necessary rather than cosmetic. The per-client
sample counts are public, so an adversary free to choose datasets of different
sizes reads the answer off the counts without attacking anything.
```

REPLACE

```latex
The equal-size restriction is necessary. The per-client sample counts are
public, so an adversary free to choose datasets of different sizes reads the
answer off the counts without attacking anything.
```

## S13. The proof of the input-privacy theorem, around line 213

One antithesis removed and five words cut. The bound is stated in the same
words as before, because it is what the theorem asserts.

FIND

```latex
The serving party is honest, so every ciphertext presented for key switching is
the prescribed output of \cref{alg:serve} on a query, and its plaintext is a
label rather than a value of the coalition's choosing. Deviating in the uploaded
values does not help either, because the adversary already chooses those values
in the real protocol and they carry no dependence on $b$. Deviating in the
contributed shares does not help, because a share that is not the prescribed one
makes the reconstruction fail, which aborts the query and returns nothing.

What remains is the answers. These do depend on $b$, because $\thstar$ depends
on client $h$'s displacement. The dependence is exactly the dependence of a
prediction interface on its training data, and it is bounded by what
$Q_{\mathrm{tot}}$ label queries reveal, which is $\delta(Q_{\mathrm{tot}})$ by
definition.
```

REPLACE

```latex
The serving party is honest, so every ciphertext presented for key switching is
the prescribed output of \cref{alg:serve} on a query, and its plaintext is a
label the coalition does not choose. Deviating in the uploaded values does not
help either, because the adversary already chooses those values in the real
protocol and they carry no dependence on $b$. Deviating in the contributed
shares does not help, because a share that is not the prescribed one makes the
reconstruction fail, which aborts the query and returns nothing.

What remains is the answers. These do depend on $b$, because $\thstar$ depends
on client $h$'s displacement. That is the dependence of any prediction interface
on its training data, and it is bounded by what $Q_{\mathrm{tot}}$ label queries
reveal, which is $\delta(Q_{\mathrm{tot}})$ by definition.
```

## S14. The remark after the theorem, around line 228

Removes the last antithesis in the shortened region. "whatever the size of the
federation" carries what "rather than with the federation" carried, and it
carries it positively.

FIND

```latex
The bound scales with the corruption threshold rather than with the federation.
A coalition of $\tc-1$ clients commands $(\tc-1)Q$ queries, so a deployment that
lowers $\tc$ lowers the query budget an adversary can assemble, at the cost of
making decryption easier to reach.
```

REPLACE

```latex
The bound scales with the corruption threshold. A coalition of $\tc-1$ clients
commands $(\tc-1)Q$ queries whatever the size of the federation, so a deployment
that lowers $\tc$ lowers the query budget an adversary can assemble, at the cost
of making decryption easier to reach.
```

## S15. First heading, line 234

Answers T19a (Sav, 11:23 am, the "Why blabla makes blabla" titles). Noun phrase,
and it names what the subsection proves rather than the question it answers.

FIND

```latex
\subsection{Why the Serving Party Is Assumed Honest}
\label{sec:malicious-ext}
```

REPLACE

```latex
\subsection{Necessity of an Honest Serving Party}
\label{sec:malicious-ext}
```

## S16. Second heading, line 290

The other question in disguise. `sec:inherent` is about leakage that belongs to
the functionality rather than to our instantiation of it, which the subsection
itself says twice, so the heading can say it once.

FIND

```latex
\subsection{What the Cryptography Does Not Cover}
\label{sec:inherent}
```

REPLACE

```latex
\subsection{Leakage Inherent to the Functionality}
\label{sec:inherent}
```

**Cross-reference audit for both headings.** No `\nameref` exists in the
manuscript and neither title is quoted anywhere, so the two labels carry every
reference and neither label changes. Nothing breaks. Three places describe these
subsections in prose and all three keep reading correctly: `security.tex` line 8
and line 10, both rewritten by **S1**, and `method.tex` line 414, which says
"\Cref{sec:malicious-ext} explains why that last assumption cannot be dropped"
and needs no change.

---

# B. `docs/paper/refs.bib`

## B1. Cite FULLSA, and add ELSA

Answers T18.3 and T18.4. `karakoc2024fullsa` currently carries a comment saying
it is uncited on purpose, and **S2** is what makes it cited, so the comment has
to go with it. The comment is replaced rather than deleted, because the reason
for citing is worth recording next to a self-citation.

`rathee2023elsa` is new. It was not in the bib. Author list, title, venue and
year verified on 2026-08-20 against the DBLP record `conf/sp/RatheeSWP23` and
the IACR ePrint entry 2022/1695. Checklist form, so no url, no doi, no note, and
the short venue name.

FIND

```latex
% UNCITED ON PURPOSE. This paper was read as the format precedent for the ideal
% functionality of Section IV and as background on the malicious-aggregator
% boundary. Neither use warrants a citation: formatting is not citable, and the
% boundary claim in that paper is attributed by its own authors to RoFL, so
% citing it here would be second-hand. It is also a self-citation, since Kupcu is
% an author of this manuscript. Cite it only if it becomes load-bearing.
@inproceedings{karakoc2024fullsa,
  title     = {Fault Tolerant and Malicious Secure Federated Learning},
  author    = {Karako{\c{c}}, Ferhat and K{\"u}p{\c{c}}{\"u}, Alptekin and {\"O}nen, Melek},
  booktitle = {Cryptology and Network Security (CANS)},
  year      = {2024},
  doi       = {10.1007/978-981-97-8016-7_4}}
```

REPLACE

```latex
% CITED in Section IV. FULLSA takes the ideal functionality of ELSA and places
% the aggregator outside it, so that a malicious aggregator can be considered.
% That is what this manuscript does with the server and the serving party, so
% the citation is load-bearing. It is a self-citation, since Kupcu is an
% author of this manuscript.
@inproceedings{karakoc2024fullsa,
  title     = {Fault Tolerant and Malicious Secure Federated Learning},
  author    = {Karako{\c{c}}, Ferhat and K{\"u}p{\c{c}}{\"u}, Alptekin and {\"O}nen, Melek},
  booktitle = {CANS},
  year      = {2024}}

% The functionality form FULLSA follows and that Section IV follows in turn.
% Authors, title, venue and year verified 2026-08-20 against DBLP
% conf/sp/RatheeSWP23 and IACR ePrint 2022/1695.
@inproceedings{rathee2023elsa,
  title     = {{ELSA}: Secure Aggregation for Federated Learning with Malicious Actors},
  author    = {Rathee, Mayank and Shen, Conghao and Wagh, Sameer and Popa, Raluca Ada},
  booktitle = {IEEE S\&P},
  year      = {2023}}
```

The `doi` line and the long `booktitle` go because the writing checklist says
DOIs are removed and conference names appear in short form. That is the only
change to the entry beyond the comment. If you would rather keep the entry
untouched and only replace the comment, drop the last three lines of the FIND
block and the matching lines of the REPLACE block.

---

# C. `sections/method.tex`. One insertion, into `sec:mhe`

## M1. The threshold assumption arrives, around line 122

This is the destination of **S1**. The three paragraphs are the deleted ones
word for word, with two pointers changed, because the point is relocation and
not rewriting.

- "throughout this section" becomes "throughout \cref{sec:security}".
- "Every statement below" becomes "Every statement in \cref{sec:security}".

Nothing else changes. No heading is added, because the material is scheme
background and `sec:mhe` is where the scheme is described. `\tc` is used for the
first time in the manuscript here, three hundred lines before its first use in
`sec:threat`, so it is now defined before it is used.

This is an insertion. The FIND block is the last sentence of the subsection as
it stands, and the new text goes after it and before the commented-out paragraph
that follows.

FIND

```latex
The second is a collective refresh,
which restores a depleted level budget and plays the role bootstrapping plays in
the single-key setting.
```

REPLACE

```latex
The second is a collective refresh,
which restores a depleted level budget and plays the role bootstrapping plays in
the single-key setting.

The construction is stated for a $\tc$-out-of-$\Nc$ threshold CKKS scheme with
$2\le\tc\le\Nc$. Encryption is under a single collective public key. Decryption
requires partial decryption shares from at least $\tc$ clients, and any set of at
most $\tc-1$ clients learns nothing about a plaintext. Key generation,
key switching and collective refresh are the threshold protocols of the same
scheme.

Two consequences follow, and the protocol uses both. Any $\tc$ clients form a
quorum, so serving does not require every client to be online. Any $\tc-1$
clients are powerless against a ciphertext, so $\tc-1$ is the corruption bound
throughout \cref{sec:security}.

Our implementation instantiates $\tc=\Nc$, which is the setting the multiparty
CKKS library provides, and the measurements of \cref{sec:exp-cost} are taken
there. Every statement in \cref{sec:security} holds for general $\tc$.
```

Labels used here and verified to exist. `sec:security` at `security.tex` line 2,
`sec:exp-cost` at `experiments.tex` line 336.

### One duplication this move creates, for whoever owns `method.tex`

I did not fix it, because I own one insertion into `sec:mhe` and nothing else in
that file. After **M1**, the `Collusion among clients` paragraph of `sec:threat`
around line 423 repeats two facts that now appear earlier in the same section.

```latex
\paragraph{Collusion among clients} Decryption is $\tc$-out-of-$\Nc$, so any
coalition of fewer than $\tc$ clients, including one that acts together with the
server, cannot decrypt. Our implementation sets $\tc=\Nc$, which is the largest
value the parameter takes and therefore the strongest collusion resistance the
structure admits. The design is arranged so that no
```

The first sentence restates the threshold, and the second restates the
instantiation. Cutting both and starting the paragraph at "The design is
arranged so that no arithmetic shortcut evades it" would take about 45 words off
the method and lose nothing, since `sec:mhe` now carries both facts and
`experiments.tex` line 700 carries the availability trade-off. That is a
suggestion for the method owner, not a paste.

---

# D. Not my file. `sections/experiments.tex`

## X1. "separates into three cases", line 210

Answers T19d, Sav's "???" of 17 August, 11:24 am. **The sentence is in
`sections/experiments.tex`, not in `security.tex` and not in `related.tex`.** It
sits in `sec:exp-peers`, at the end of the paragraph headed "The comparison that
does hold". Another agent owns that file, so this block is offered and not
claimed.

The sentence is unclear because it announces three cases and never names them.
The three paragraphs that follow are the three cases, in this order: DENSE and
FedDF, which protect nothing, FedAUXfdp, which protects with differential
privacy, and ours, which protects cryptographically. Naming the three in the
announcing sentence is the whole fix.

FIND

```latex
cancels. Read that way the peer group separates into three cases.
```

REPLACE

```latex
cancels. Read that way the peer group falls into three cases. A method either
leaves the contribution unprotected, protects it with differential privacy, or
protects it cryptographically.
```

---

# E. Shortenings considered and rejected

Three cuts would have saved words and changed what is proved, so they are not in
the list.

1. **The `\emph{Setup.}` part of the semi-honest proof, cut entirely.** It is
   the shortest of the three parts and reads like boilerplate. It is not. The
   simulator has to produce a key-generation transcript before it can produce
   anything else, and the theorem's assumption is IND-CPA against $\tc-1$ key
   shares, which only means something once the key is collectively generated.
   Cutting the part would leave the collective public key unexplained in the one
   place the proof needs it.

2. **The two sentences on collective refresh in the Training part.** They are
   the longest passage in the proof and they look like implementation detail.
   They are the only place the proof handles a step that is not a deterministic
   function of the ciphertexts, which is exactly where a reviewer looks for a
   hole. **S9** shortens them and keeps them.

3. **"We do not claim correctness" and the sentence after it, in `sec:malicious`.**
   Removing them shortens the opening and turns an input-privacy theorem into
   something a reader could take for a robustness theorem. The disclaimer is the
   reason the theorem is honest. Kept.

One more thing was left alone deliberately. `sec:malicious-ext` opens "That
assumption is not a convenience, and the reason is worth stating", which reads
slightly redundant once the heading says `Necessity of an Honest Serving Party`.
Sav's shortening request stops at that heading, so the body is out of scope and I
did not touch it. If it is wanted, the smallest fix is to delete "That assumption
is not a convenience, and" and start the sentence at "The reason is worth
stating".
