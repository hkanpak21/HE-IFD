# Changes to carry into Overleaf, 2026-09-06

Eleven of the twelve items discussed. Item 6 (ELSA and FULLSA) was decided to
stay as it is. Every change below is in `docs/paper/sections/`.

The submission is ten pages after these changes, and `bash scripts/gates.sh`
reports zero rewritten paragraphs in both documents.

Search for the OLD text, replace with the NEW text. Where a block says
"report only", it is inside `\tronly{...}` and does not appear in the
submission.

---

## 1. `intro.tex` — softer word

OLD

    One-shot protocols end by handing the final model to every participant, which is
    unacceptable when the model may not be distributed at all.

NEW

    One-shot protocols end by handing the final model to every participant, which
    rules them out when the model may not be distributed at all.

---

## 2, 3. `intro.tex` — why the selection rule exists

In the third contribution bullet, "A selection rule that runs under encryption".

OLD

    shared head over the bare public backbone. Each client scoring both on its own held-out data and voting estimates the

NEW

    shared head over the bare public backbone. The two fail for opposite reasons, the
      shared head when few clients hold a class and the personal adapter when a
      client's representation drifts too far. Which failure binds depends on the task
      and on the partition, so the federation must measure both. Each client scoring both on its own held-out data and voting estimates the

Two sentences added. The version that blamed thin class counts alone was
rejected, because the DBpedia sweep and the twelve CIFAR-10 cells go the other
way: there, thin coverage favours the shared head.

---

## 4. `method.tex` — shorter cost sentence

OLD

    dimension and not by the backbone behind it. Communication

NEW

    dimension. Communication

Pure deletion. The point survives in the introduction, which already says the
cost of the cryptography does not grow with the backbone.

---

## 5a. `method.tex` — split the long sentence

OLD

    The trained
    quantity that is shared must therefore attach after the last nonlinearity, and in
    a transformer, the only such point is the final linear map. That is the head.

NEW

    The trained
    quantity that is shared must therefore attach after the last nonlinearity. In a
    transformer, the only such point is the final linear map.

---

## 5b. `method.tex` — what happens if the map sits earlier

In the `\paperonly{...}` Scope paragraph that follows.

OLD

    another. We evaluate
    classification only.}

NEW

    another. Placing the map earlier forces the client either to evaluate the
    nonlinearities above it under encryption or to decrypt an intermediate value,
    which hands back the numbers the serving path withholds. We evaluate
    classification only.}

---

## 6. `security.tex` — no change

The ELSA and FULLSA citations stay. Both are cited only for the shape of the
functionality, which is standard, and the sentence already says so. FULLSA is
Karakoc, Kupcu and Onen, CANS 2024.

---

## 7. `experiments.tex` — cite the frozen down-projection

OLD

    with its down-projection frozen at a shared public initialisation,

NEW

    with its down-projection frozen at a shared public initialisation~\cite{sun2024ffalora},

FFA-LoRA was already cited for this construction in Related Work.

---

## 8. `experiments.tex` — Table 1 caption

OLD

    The servable columns are the two arrangements the protocol answers queries from.
    The reference columns are not servable under the threat model of
    \cref{sec:threat}. The estimator selects per seed, so the selected accuracy is
    $0.669$ on AG-News, $0.756$ on CIFAR-100, and the bolded value
    elsewhere.

NEW

    The servable columns are the two arrangements the protocol answers queries from,
    and bold marks the better one. The reference columns are not servable under the
    threat model of \cref{sec:threat}. Alone is one client's own model with no
    federation, disclosed is the merged model this protocol declines to build, and
    pooled is centralised training on the union of the data.

The per-seed sentence is gone. Those two accuracies are not reported in the
submission at all now, and the report carries them.

---

## 9. `experiments.tex` — Section D, the selection rule

Replaces the whole `\paperonly{...}` block at the top of
"Accuracy of the Selection Rule".

OLD

    \paperonly{Scoring both arrangements under the federation's own class prior, letting
    the shared arrangement pool evidence across clients and scoring the personal
    arrangement's unobserved classes at zero, selects correctly in $12$ of $15$ cells.
    Filling the unobserved classes from each client's rarest classes instead of with
    zero selects correctly in $13$. \trsee{sec:experiments} reports the estimator against the held-out vote on every cell.}

NEW

    \paperonly{The natural procedure is for each client to measure both arrangements
    on data it held back and vote. It estimates the wrong quantity. The shared
    arrangement is one model, so pooled measurements track its global accuracy, while
    client $j$ can measure the personal arrangement only on its own distribution,
    which is the one its own model was fitted to. The vote is therefore optimistic for
    the personal arrangement and picks correctly in $8$ of $27$ cells. The estimator
    of \cref{eq:estimator} scores both under the federation's own class prior and
    picks correctly in $23$, or $24$ when unobserved classes are filled from each
    client's rarest classes rather than with zero. A wrong choice gives up $0.470$ of
    accuracy under the vote and $0.021$ under the estimator.
    \trsee{sec:experiments} reports every cell.}

The counts move from 15 cells to all 27, matching the report's table, and the
regret is now stated. Promoting the report's table into the submission was
rejected: it does not fit in ten pages.

---

## 10. `experiments.tex` — what a high-fidelity copy does not give

In the `\paperonly{...}` extraction paragraph.

OLD

    allowance from $\Cc$, $d$ and the fidelity it concedes. \trsee{sec:experiments} gives the extraction study in full.}

NEW

    allowance from $\Cc$, $d$ and the fidelity it concedes. A copy at that fidelity
    reproduces the served model's decisions, and published membership attacks against
    it and against the head in plaintext both sit at chance. \trsee{sec:experiments} gives the extraction study in full.}

Records: `results/mia_extracted/results.csv`, `results/row_leakage/results.csv`,
`results/oslo_serving/results.csv`.

---

## 12. `experiments.tex` — report only, does not affect Overleaf

A new `\tronly{...}` paragraph after "Linearity of the shared quantity" in
Scope and Limitations. It gives the dichotomy for sharing a map inside the
backbone: either the client decrypts an intermediate, which is a linear oracle
recovering the shared weights in d queries and is priced at 769 answers against
the 1.2e4 to 2.0e5 that labels demand, or every nonlinearity above the site runs
homomorphically. It also notes that several maps at one position cost neither,
since parallel maps after the last nonlinearity add rows and no depth.

---

## Gate state after these changes

    1  submission 10 pages, report 24
    3  rewritten 0, submission
    3b rewritten 0, report
    6  both compile, cite=0 ref=0 overfull=0 err=0
    7  3 errors, all pre-existing false positives
    8  fig_protocol 5 spans, known
    9  the arXiv placeholder is still in refs.bib, by design
