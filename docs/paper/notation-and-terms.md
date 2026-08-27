# Notation and terms

Rewritten 2026-08-23. The version before this one described the distillation
protocol that the pivot of 2026-07-26 replaced, and it would have given a reader
the wrong mental model. `docs/paper/sections/method.tex` is authoritative for the
protocol and `docs/CONTEXT.md` is authoritative for which word names which thing.

The submission does not print a notation table. The table moved to a `\tronly`
block on 2026-08-23 to buy a page, so the technical report prints it and the
submission defines every symbol at first use instead. This file is where a symbol
is looked up without opening either document.

## Symbols

Every macro below is defined in `docs/paper/sections/preamble.tex` and shared by
both documents. Write the macro, never the raw symbol, so a change reaches both.

| Macro | Symbol | Meaning |
|---|---|---|
| `\Nc` | $N$ | number of participating clients |
| `\Dj`, `\nj` | $\mathcal{D}_j$, $n_j$ | client $j$'s dataset and its size |
| `\Cc` | $C$ | number of classes |
| | $n_{j,c}$ | examples of class $c$ held by client $j$ |
| | $\alpha$ | Dirichlet concentration, the label-skew parameter |
| `\featx` | $\varphi$ | the frozen public backbone, never trained and never encrypted |
| | $A_j$ | client $j$'s adapter, trained locally and never transmitted |
| | $\varphi_j$ | client $j$'s feature map, the backbone composed with $A_j$ |
| `\thz` | $\theta_0$ | the public initialiser of the classifier head |
| | $h_j$ | client $j$'s trained head |
| `\disp` | $\Delta_j$ | the head displacement $h_j - \theta_0$, the only thing a client uploads |
| | $g_j$ | client $j$'s per-class counts, the coverage weight |
| `\wj` | $w_j$ | sample weight $n_j / \sum_i n_i$ |
| `\thstar` | $\theta^\star$ | the shared head, held only as a ciphertext |
| `\tc` | $t$ | the decryption threshold, $t$-out-of-$N$ |
| `\Fhe` | $\mathcal{F}$ | the ideal functionality |
| `\Leak` | $\mathcal{L}$ | the leakage $\mathcal{F}$ allows |
| `\Dset` | $\{\mathcal{D}_j\}$ | all client datasets |
| `\negl` | $\mathrm{negl}$ | a negligible function |
| | $Q$ | the per-client query allowance |

## The four accuracies the paper argues in

The paper reports four quantities per task and compares them by name. Only the
first is servable under the threat model.

| Macro | Symbol | What it is |
|---|---|---|
| `\Asel` | $A_{\mathrm{sel}}$ | the arrangement the estimator selects, which is what a deployment gets |
| `\Aloc` | $A_{\mathrm{loc}}$ | a client alone, its own adapter and its own head, no federation |
| `\Adis` | $A_{\mathrm{dis}}$ | the disclosed model, adapter and head both aggregated and decrypted |
| `\Apool` | $A_{\mathrm{pool}}$ | one model on the union of the clients' data |

Two differences carry the argument. $A_{\mathrm{dis}} - A_{\mathrm{sel}}$ is the
price of never disclosing a model, measured at $0.03$ to $0.14$.
$A_{\mathrm{pool}} - A_{\mathrm{dis}}$ is the price of the partition.

## The two servable arrangements

Both cost the same to serve and the federation picks between them without
decrypting either.

| Name in prose | What it is | Name in the records |
|---|---|---|
| the shared head | the shared head over the bare public backbone | `A_headonly` |
| the personal adapter | the shared head over each client's own adapter | `B_personal` |

`sel_gp_rarefill` in the records is the estimator that chooses between them.
`current` in the records is the disclosed model, which is $A_{\mathrm{dis}}$.
`local` is $A_{\mathrm{loc}}$. None of those record names appears in the paper.

## Symbols that are gone

These were in the file before this rewrite and belong to the retired distillation
protocol. If one appears in a draft, the draft predates the pivot.

| Gone | It used to mean |
|---|---|
| $t_j$ | client $j$'s local teacher |
| $K$, $\tau$ | bounded distillation steps and the temperature |
| $K_{\mathrm{pc}}$ | samples per class per client in the alignment set |
| "shared loss basin" | what $\theta_0$ was called when Phase 0 built it |
| $f_\theta$, $h_\psi$ | the student model and its head |

`\teacher`, `\Ksteps`, `\temp`, `\Kpc`, `\KL`, `\model` and `\head` are still
declared in the preamble and are used by nothing. They are harmless and left
alone, because deleting a macro is a change to a file the PIs have read.

## Terms

`docs/CONTEXT.md` is the authority. The four that are broken most often:

- **the server**, one entity that merges the heads and answers queries. Never
  "the serving party" and never "the aggregation server". They were two parties
  until 2026-08-23 and neither theorem ever used the distinction.
- **the head**, not the model. The federation shares a classifier head. The
  adapter never leaves the client.
- **confidentiality** is what encryption gives a ciphertext. **Privacy** is about
  the training data and what an adversary learns about it.
- **semi-honest**, never "honest-but-curious", in every section.
