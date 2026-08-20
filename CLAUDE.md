# CLAUDE.md — operational notes for the HE-IFD repo

Read this first when you (Claude) attach to this repo. It tells you how the user wants to work, what the current method actually is, and what NOT to do.

## If you are a context-zero agent (ralph / AFK) picking up an issue

You have no conversation history. Your ground truth, in order:

0. **`docs/notes/PI_notes/`** — if your task touches the paper at all, read the
   README there and the current dated file FIRST. The PIs are reviewing on
   Overleaf, and that folder records every comment, why it was made, and the
   replacement text agreed. The section text does not explain itself; those
   notes do.
1. **`docs/plan/paper-rewrite.md`** — the current plan: the paper's flow, the
   figure and table standard, the voice rules, and the experiments still
   outstanding. Read it fully.
2. **`docs/paper/sections/method.tex`** — the method as it actually stands. This
   is authoritative for the protocol.
3. **This file** — operations: how to run compute, where things live, what not to
   touch.
4. **`docs/issues/<your-issue>.md`** — your task, if one was assigned.

If a document disagrees with `method.tex`, the document is stale. Anything under
`docs/archive/` is superseded by definition and must not be mined for
methodology.

## Source of truth (updated 2026-08-06)

- **PI review of the paper** -> **`docs/notes/PI_notes/`**. Read the README and
  the current dated file before editing any section they cover. Replacement text
  is proposed in chat and pasted into Overleaf by the user, never applied to
  `docs/paper/` locally.
- **Method and protocol** -> **`docs/paper/sections/method.tex`**.
- **Security claims** -> **`docs/paper/sections/security.tex`**, with the
  reasoning in `docs/notes/malicious-security.md`.
- **Plan, standards, outstanding experiments** -> **`docs/plan/paper-rewrite.md`**.
- **Numbers.** Every figure in the paper traces to one of these:

| paper element | record |
|---|---|
| Table II, five-task accuracy | `results/personal_adapter*/stratified/results.csv` |
| Table II, pooled column | `results/centralised_ceiling/results.csv`, `matched_total` rows |
| Table III, client-count row | `results/personal_adapter/nsweep.csv` |
| Table III, skew and local-step rows | `results/personal_adapter/sensitivity.csv` |
| Table IV, matched CIFAR-10 | `results/personal_adapter_vision/cifar10_matched.csv` |
| Table VI and Figure 4, cost | `results/fhe_serve/cost_grid.json` |
| the argmax and query totals | `results/fhe_serve/argmax_tournament.csv` |
| Table VII, communication | `results/fhe_serve/comm_grid.json`, the `serving` chain at `log_n` 15 |
| the bootstrapping key size and its generation time | `results/fhe_serve/btp_keys.json` |
| Table VIII, extraction | `results/extraction_budget/results.csv` |
| the extraction scaling law | `results/extraction_scale/results.csv` |
| the noise-defence note | `results/extraction_defence/results.csv` |

**Deprecated. Do NOT mine for methodology, equations, or threat model:**
- `docs/archive/` — superseded notes and issue briefs, kept only for provenance.
- `src/v1/`, `src/v2/`, `archive/` — earlier simulations.
- **`FL_TDSC/` — REJECTED TDSC SUBMISSION.** The protocol there (encrypted
  intermediate-feature distillation, polynomial activations, server-side encrypted
  SGD) is not the current method. Historical and audit-only.
- `comparators/` — vendored upstream code for citation and audit; many vendors
  have stale APIs and are not runnable. Cite `comparators/REPORTED_RESULTS.md`.

## The current method (what we are actually doing)

One-shot federated fine-tuning under **multiparty CKKS** in which **the model is
never disclosed**. Resubmitting to **IEEE TNSE** (rejected from TDSC; shared
reviewer pool, so every TDSC concern is live). Decided with the PIs on
**2026-07-15**: one method throughout the paper, with release discussed only as a
reference point.

- Every client fine-tunes on the **same frozen public backbone**: a low-rank
  adapter with its down-projection frozen, plus a classifier head.
- **The adapter is trained locally and never transmitted.** Only the **head
  displacement** is encrypted and uploaded, once. Because no aggregate of the
  adapters is ever formed, a coalition of N-1 clients has no sum to invert.
- The server forms a **coverage-weighted head merge**: clients holding a class
  decide its row. The denominator is the vector of per-class totals and is
  **inverted under encryption**, never decrypted, since a coalition that learned
  it would recover the remaining client's class histogram.
- **The result is never decrypted.** Queries are answered under encryption: the
  client computes its own features and encrypts them, the serving party applies
  the encrypted head and takes the argmax under encryption, and a quorum
  key-switches the label to the querier alone.
- Two arrangements are servable, the shared head with and without each client's
  own adapter. The federation chooses between them **without decrypting either**,
  using a global-prior estimator that decrypts one value.

**"One-shot" means no intermediate training artifact is ever exposed.** It is not
a claim that the parties stop communicating. Key generation precedes the protocol
and serving costs traffic per query; both are accounted for in the paper. Never
say the protocol is silent after training.

**Describe it faithfully.** The shared object is the *head*, not the model. Never
write that clients receive a model, and never write that they learn "nothing at
all": they learn the labels they ask for, bounded by a query allowance, which is
an economic bound and not cryptographic hardness.

**The shared object is a trained linear map after the last nonlinearity.** A
classifier head is one such map. A decoder's vocabulary projection is another.
The construction fixes the *position* of the map, not the task. Say this when
scope comes up, and say we evaluate classification only, because we do.

**Current state (2026-08-02). The paper is with the PIs.** It is 21 pages,
compiles clean, and the user has moved it to Overleaf. **Do not edit
`docs/paper/` without explicit direction.** Local edits will diverge from the
Overleaf copy the PIs are reading.

What the paper now contains, all measured and all sourced from records in
`results/`:

- A separate security section: an ideal functionality, a semi-honest theorem, a
  content game for input privacy, an impossibility result showing the strict
  functionality is out of reach against a deviating serving party, and a
  subsection of extensions that would recover it.
- Accuracy on five tasks, with four quantities per task: selected, alone,
  disclosed and pooled. The paper argues in that notation.
- CIFAR-10 on the DENSE and FedAUXfdp partitions, under the actual protocol.
- Cryptographic cost over the full grid of ring degree and client count, with
  the per-query total stated in seconds.
- Extraction cost, the scaling law, and the separation between fidelity and
  knowledge of client data.

See `docs/plan/security-program.md` for the security and journal work, and
`docs/plan/paper-rewrite.md` for the paper flow and what is still outstanding.

## Venue (decided 2026-07-29)

Target **journals**, not conferences. The three candidates differ, and the TDSC
rejection matters differently to each.

- **IEEE TNSE** is the cleanest. Its one-resubmission rule covers TNSE's own
  rejections only, so the TDSC rejection does not block it.
- **IEEE TIFS** costs more. Signal Processing Society policy allows one
  resubmission of a manuscript rejected by *any* journal, requires disclosing
  the rejection, and requires verbatim quotation of every previous review with
  responses. It also states a 13-page limit. We are at 19.
- **IEEE TDSC** publishes no resubmission policy. Ask the editorial office
  before assuming either way.

## The plan

`docs/plan/security-program.md` holds the security proofs, the journal rules,
and the generation scope. `docs/plan/paper-rewrite.md` holds the paper flow and
the figure and table standard. Paper writing is done with the user (HITL); all
compute is AFK.

## The workflow

The user develops on a local machine (Mac/Linux/Windows) and runs all compute on the **VALAR** HPC cluster:

1. **Local machine**: edit source (`src/`, `jobs/*.sh`, `comparators/`), read results (`results/<case>/`), inspect papers, write issues/PRD, commit to git.
2. **VALAR login node** (`ai*.kuvalar.ku.edu.tr`): submit Slurm jobs (`sbatch jobs/*.sh`), monitor (`squeue`, `sacct`), read result JSONs, do git ops, **pre-fetch model weights/datasets** (login node has internet; compute nodes do not). **No Python compute on the login node, ever.**
3. **VALAR compute node** (allocated by `sbatch`): runs the actual Python — training, distillation, FHE, data generation.

When Claude runs **on the VALAR side** (repo at `/scratch/hkanpak21/HE_IFD`), treat yourself as on the login node and submit all compute via `sbatch`.

## Colab notebooks (the user's primary run path when the VALAR queue is backed up)

The user runs compute on **Google Colab** (driven from VS Code) when the VALAR GPU queue is congested, and
collects results by **pasting cell outputs straight into CSV files** — NOT via git / Drive / VS Code
Explorer round-trips (those are unreliable in their setup). When authoring Colab notebooks
(`notebooks/colab_*.ipynb`), follow these rules:

- **ONE merged notebook, not one per issue.** Put all issues/experiments in a single notebook with clear
  section headers (`# ISSUE 026`, etc.). The user does not want to switch environments between notebooks;
  each section is self-contained but shares the setup. Do not proliferate separate `colab_<issue>.ipynb`
  files — merge them.
- **Every results cell prints CSV that is ready to paste directly into a `.csv` file.** Plain
  comma-separated rows with ONE header line, ONE table per cell, **no markdown pipes/formatting and no prose
  mixed into the CSV block**. The user copies the cell output verbatim into `results/<case>/<name>.csv`. Use
  the column order of the matching `src/report.py` / `mia/report.py` table. Canonical formats:
    - **sweep / accuracy:** `backbone,N,alpha,method,seed,acc,theta0_acc,mean_teacher,best_teacher,oracle,status`
    - **λ-verify (026):** `backbone,N,alpha,method,seed,lambda,acc`  — one row per λ
    - **MIA (021/028):** `backbone,N,alpha,method,seed,surface,attack,tpr_at_0.1pct,tpr_at_1pct,auc`
  Implement as `print(df.to_csv(index=False))` or a manual `print(",".join(...))` loop — header once, then
  rows, copy-paste-clean. (Keep a human-readable table too if useful, but the CSV block is the deliverable.)
- **Robust setup, never `git pull`.** Clone if absent, then `git fetch origin master` +
  `git checkout origin/master -- src mia jobs tests` (refresh CODE only). A plain `git pull` aborts because
  the runs leave `results/` dirty, so code fixes silently fail to land.
- **One-shot, reliable environment** so the user can establish it fast: `pip install` the few non-Colab deps
  (`transformers datasets timm`), pre-download datasets (`download=True`; the `src/` loaders are
  `download=False` for VALAR), optional HF token via `getpass` (public assets do not require it). Do NOT set
  `HF_HUB_OFFLINE` (VALAR-only). Newer `datasets` needs namespaced HF ids (`fancyzhx/ag_news`).
- A zip/git-push export cell is a fine fallback, but the **paste-CSV-from-cell-output path is primary**.

## GOLDEN RULE

**Never run `python` on the login node** if the script imports torch, tenseal, transformers, or anything that does training, FHE, model loading, or data generation. The only allowed `python` on the login node:

- syntax checks (`python -c "import ast; ast.parse(open(f).read())"`)
- text-only utilities (`tools/pdf_extract.py` — pure pypdf, no compute)
- `argparse --help` to verify a CLI

Everything else goes through `sbatch jobs/<wrapper>.sh` (preferred) or a short `srun --partition=t4_ai --account=comx29 ...` (< 5-min sanity checks only).

## VALAR networking — pre-fetch on the login node

Compute nodes have **slow/no internet**. Before any sweep that needs pretrained weights or a HF dataset:

- **Pretrained backbones** (ViT-B/32, ResNet-18, DistilBERT, GPT-2): trigger the download once on the **login node** so it lands in the HF/torch cache (`~/.cache/huggingface`, `~/.cache/torch`), then load offline on compute nodes (`HF_HUB_OFFLINE=1` / `local_files_only=True`).
- **HF datasets** (e.g. AG News): same — `load_dataset` once on the login node to populate `~/.cache/huggingface/datasets`, then load offline in the job.
- **Vision datasets** (MNIST/FMNIST/CIFAR-10): already cached under `data/` with `download=False` — see Datasets.

## Conda environment

Single env: **`he_ofl`** (`/home/hkanpak21/.conda/envs/he_ofl`). Has `torch 2.3.0+cu121`, `torchvision`, `tenseal 0.3.16`, `transformers`/`datasets` (verify), `numpy`, `pypdf`, `termcolor`, `xgboost`, `pydicom`, `opacus`. New dep: `pip install --quiet <pkg>` from the login node is fine. Avoid `conda install` (base env is read-only).

## VALAR facts that cost time to rediscover (verified 2026-08-20)

**The `ai` partition opened on 2026-08-20 and it changes how work is planned.**
The old `comx29` and `t4_ai` route still works, and everything written before
this date assumes it. Prefer `ai`.

- **Use account `ai`, QOS `ai`, partition `ai`.** Verified by a real job, 1583143,
  which ran on `ai07`. The old `comx29` and `t4_ai` association also still exists.
- **The QOS `ai` allows 8 GPUs, 240 CPUs and 350G of memory per user, with 8
  running jobs and 50 queued.** Eight GPU jobs run at once, where `comx29`
  allowed one.
- **The `ai` partition has no time limit.** `MaxTime=UNLIMITED`. The three hour
  rule below applies to `t4_ai` and to nothing on `ai`. Resumable jobs are still
  worth writing, because a preempted job restarts, but the wall clock no longer
  forces the split.
- **176 GPUs over 22 nodes: 72 `ampere_a40`, 64 `tesla_t4`, 32 `tesla_v100`, 8
  `rtx_a6000`.** A bare `--gres=gpu:1` takes whatever is free and will often give
  a T4. Ask for the card by name, `--gres=gpu:ampere_a40:1`, when the run is long
  enough for it to matter. An A40 holds 48G against the T4's 15G.
- `OverSubscribe=YES:4` and `PreemptMode=REQUEUE` on `ai`. A job can be requeued,
  so checkpointing still earns its keep.
- **`sbatch --test-only` lies.** It reports a start time for partitions the QOS
  cannot use. It does not check the QOS-partition association. Submit a real
  job to find out.
- **A job with no `--gres` runs without consuming a GPU slot.** Use this for
  CPU-only work, such as the Lattigo cost jobs, so it runs beside training.
- `short` caps at 2 hours. `t4_ai` allows 8. `mid` allows 1 day and `long` 7,
  but neither took the `comx29` account.
- Go lives behind `module load go/1.24.4`, not on the default PATH.
- The system GCC is 8.5 and has no `<concepts>`. A C++20 toolchain (GCC 11.4)
  sits in the `thor310` conda env at `/home/hkanpak21/.conda/envs/thor310/bin`.

## Script gotchas

- **`jobs/vision_matched.py` is the PRE-PIVOT pipeline. Its numbers are
  disclosed models.** `agg_count_head` calls `agg_plain` first, which merges the
  adapter as well as the head, and only then overrides the head rows. So every
  candidate it produces is the model this protocol declines to build. It has no
  shared-head arrangement, no personal-adapter arrangement, and no client-alone
  mode, and it selects by the held-out client vote that the paper rejects. Use
  it for nothing the paper claims. Corrected 2026-08-02, after it nearly put
  disclosed-model figures into Section 5.3.
- **`jobs/personal_adapter_vision.py` is the correct vision pipeline**, and it is
  parameterised despite the hardcoded `DATASETS`. `main()` takes dataset names
  and seeds as positional arguments, and reads `PA_N`, `PA_ALPHA` and `PA_K` from
  the environment. Run a matched partition with
  `PA_N=5 PA_ALPHA=0.1 sbatch jobs/personal_adapter_vision.sh cifar10 42`.
  About 22 min per cell on a T4 for CIFAR-10, 43 min for CIFAR-100.
  **Its per-dataset JSON name carries no N or alpha**, so parallel configs
  overwrite it. The authoritative output is the CSV block printed to the `.out`
  log, which is what `results/personal_adapter_vision/cifar10_matched.csv` was
  built from.
- **`fhe` has `-cost-grid`**, which measures every protocol operation over the
  cross product of ring degree and client count in one run. Prefer it to
  `-ring-sweep` and `-protocol-cost`, which each cover one axis and whose
  single-run timings do not agree with each other. CPU-only: submit
  `jobs/fhe_cost_grid.sh`, which has no `--gres` and so runs beside a GPU job.
- **`jobs/vision_matched.py` holds the matched peer stages** (`dense`,
  `fedaux`, `fedsd2c`, `s6`) and is resumable: it writes one JSON per cell and
  skips finished cells. Its wrapper overrides `--stage` with the array index,
  and `STAGE_ORDER` maps index to stage.
- **`jobs/personal_adapter_test.py` checkpoints each client** under
  `results/personal_adapter/ckpt/`. A cell that exceeds the wall clock resumes
  instead of restarting. This is what makes N=50 reachable.
- `vision_matched.py` uses an older selection rule (fisher / count-head). The
  paper's rule is the global-prior estimator in `personal_adapter_test.py`. Do
  not mix the two pipelines' numbers.

## Slurm template (use for new sbatch wrappers)

```bash
#!/bin/bash
#SBATCH --partition=ai
#SBATCH --account=ai
#SBATCH --qos=ai
#SBATCH --gres=gpu:ampere_a40:1  # or gpu:tesla_t4:1 for short work; bare gpu:1 gets whatever is free
#SBATCH --cpus-per-task=8
#SBATCH --mem=24G              # bump to 64G+ for TenSEAL / multiparty CKKS work
#SBATCH --time=12:00:00        # the ai partition has no cap; t4_ai still caps at 8h
#SBATCH --job-name=<name>
#SBATCH --output=/scratch/hkanpak21/HE_IFD/results/<case>/runs/<name>_%j.out
#SBATCH --error=/scratch/hkanpak21/HE_IFD/results/<case>/runs/<name>_%j.err

set -euo pipefail
cd /scratch/hkanpak21/HE_IFD
source /opt/ohpc/pub/compiler/conda3/latest/etc/profile.d/conda.sh
conda activate he_ofl
export HF_HUB_OFFLINE=1           # for jobs using pre-fetched HF weights/datasets
exec srun python -u -m src.<entrypoint> "$@"   # flat src/ package (post-consolidation)
```

The Lattigo (Go) real-FHE job is the exception — it builds/runs a Go binary, may use a CPU partition (no GPU needed), and lives under `fhe/`.

**Job time limits.** The `ai` partition has none, so a long sweep can run as one
job. `t4_ai` caps at 8 hours and `short` at 2. Keep sweeps resumable anyway
(`sweep.py` skips completed cells, and cell subsets are selectable through env
vars or a job-array index), because `ai` preempts by requeue. A sweep that dies
should resume, not restart.

## Datasets

Vision datasets pre-fetched under `data/` (gitignored), load with `download=False`:

```
data/MNIST/raw/
data/FashionMNIST/raw/
data/cifar-10-batches-py/
data/cifar-10-python.tar.gz
```

Text: **AG News** is a HF dataset — pre-fetch on the login node (see networking note), it is not under `data/`.

## Repo layout

```
src/                                 # SINGLE flat package (post-consolidation; no v1/v2)
  data.py        loaders + Dirichlet partition + probe extraction + feature cache
  backbones.py   frozen extractors (ResNet/ViT/DistilBERT/GPT-2) + from-scratch nets + shared init
  teacher.py     per-client teacher training + seed-keyed disk cache
  phase0.py      alignment builders {no-Phase0, raw_union, dp_averaged}; averaging-variant DP math; θ₀
  distill.py     local_distill_trajectory: bounded K-step KL → cumulative displacement Δ = θ_K − θ₀
  aggregate.py   server linear combine (sample-weighted) + naive-average baseline; FHE-compatible
  evaluate.py    IID acc, M3 (teacher-vs-aggregate), M4 (OOD-class), standalone θ₀ acc, teacher refs
  protocol.py    run one (dataset, backbone, N, α, K, method, seed) cell → CellResult
  sweep.py       resumable CLI over the grid; per-cell JSON
  report.py      results/<case>/ writer (README + results.csv + partition_diagnostic.jsonl)

fhe/                                 # Lattigo (Go) real-FHE validation (M2)
mia/                                 # membership-inference attack suite (M2)

jobs/                                # sbatch wrappers — the ONLY entrypoints that run python
docs/
  README.md                            what lives where
  paper/                               the manuscript (main.tex, sections/, figures/)
    sections/security.tex              ideal functionality + both theorems
    figures/drawio/                    editable figure sources
  plan/paper-rewrite.md                THE PLAN: flow, standards, voice, experiments
  plan/security-program.md             security proofs, journal rules, generation scope
  notes/extraction-attack.md           the attack, the four defence cases, literature
  notes/generation-scope.md            autoregressive scope, costs, Gumbel sampling
  notes/malicious-security.md          the impossibility, the realizable functionality,
                                       recomputation and spot-checking
  design/                              why a decision was made
  issues/                              per-task agent briefs
  notes/                               walkthroughs and session records
  archive/                             superseded, provenance only
comparators/
  REPORTED_RESULTS.md                  per-paper extracted tables, paper-verbatim
  fedmd/ feddf/ dense/ coboosting/ feddiff/ fedkt/ poseidon/   audit-only

results/<case>/                      # case = <method>_<model>_<dataset>_<axis> (no version prefix)
  README.md                            3-sentence description + auto-populated table
  results.csv                          long-form rows (auto)
  partition_diagnostic.jsonl           per-client per-class counts (auto)
  cell_*.json                          per-cell results
  runs/*.{out,err}                     Slurm logs

archive/                             # retired src/v1, src/v2, old paper drafts (provenance)
data/                                # gitignored — datasets on VALAR scratch
cache/                               # gitignored — teacher checkpoints, regenerable from seed
tools/                               # gitignored — local-only utilities (pdf_extract.py etc.)
results/colab_results/               # the authoritative notebook + exported tables/figures
```

## When asked to "run X" / "sweep Y"

1. Locate or write `jobs/<X>.sh` using the template above. Pre-fetch any weights/datasets on the login node first.
2. `sbatch jobs/<X>.sh`. Capture the `<jobid>`.
3. If monitoring live, use the Monitor tool with `tail -F .out` and a grep filter keeping `[sweep] ok|FAIL`, `Traceback`, `OOM`, `CUDA`, `RuntimeError` — drop `it/s` tqdm noise.
4. When the job finishes, read `results/<case>/cell_*.json` + the auto-written `results/<case>/README.md`.
5. Never `tail -F` a slurm log on the login node directly (fine inside a Monitor task — that's a managed background).

## When asked to "add a new experiment"

1. Case slug: `<method>_<model>_<dataset>_<axis>` (e.g. `heifd_vit_cifar10_dp-sweep`). No version prefix.
2. Create `results/<case>/` with a placeholder `README.md`; the auto-writer populates the table.
3. Entrypoint importable as `src.<module>`.
4. Write `jobs/<case>.sh` from the template. Submit.

## When asked to "compare against X"

1. Check `comparators/REPORTED_RESULTS.md` first — many published numbers are already extracted, paper-verbatim.
2. Vendored upstream is at `comparators/<vendor>/`; many have stale APIs. We **cite** published numbers, we do not re-run vendor code. Run HE-IFD on the matched setup and place our number beside theirs.
3. Primary peer group = DP one-shot FL (FedAUXfdp, FedDiff, FedKT). HE anchor = POSEIDON. Plaintext (DENSE/Co-Boosting/FuseFL) = ceiling reference only.

## Things to NOT do

- **Never `python ...` on the login node** for training/FHE/model-loading. Submit via `sbatch`.
- **Never download on a compute node.** Pre-fetch weights/datasets on the login node (see networking note).
- **Never re-download cached datasets.** Use `download=False`.
- **Never commit big binaries.** Datasets, checkpoints, slurm logs are gitignored. Add new heavy artefacts to `.gitignore` before committing.
- **Never invent numbers from prior papers.** Use `tools/pdf_extract.py` and quote verbatim. The old `REPORTED_RESULTS.md` was full of LLM-recollection errors that the user caught.
- **Never describe the shared object as a model.** The federation shares a
  classifier *head*. The adapter never leaves the client.
- **Never say the model is released or decrypted.** It is not, at any point.
- **Never say clients learn "nothing at all."** They learn the labels they query.
- **Never commit LaTeX build artifacts.** `.aux`, `.log`, `.out`, `.blg`, `.bbl`
  are gitignored; `main.pdf` stays tracked.
- **Never edit `FL_TDSC/*.tex` or the paper without explicit user direction.** Paper writing is HITL.

## Common operations cheatsheet

| Task | Command |
|---|---|
| Submit a sweep | `sbatch jobs/<case>.sh` |
| Watch queue | `squeue -u hkanpak21 -o "%.10i %.18j %.8T %.10M %R"` |
| Recent history | `sacct -X -u hkanpak21 --starttime=$(date -d '6 hours ago' +%FT%T) -o JobID,JobName,State,Elapsed,ExitCode` |
| Tail a running job | `tail -F results/<case>/runs/<name>_<jobid>.out` |
| Cancel a job | `scancel <jobid>` |
| PDF inspection | `python tools/pdf_extract.py <pdf> "<keywords>" --context 2` |

## Local-side workflow

```sh
# on local machine
git clone https://github.com/hkanpak21/HE-IFD.git
cd HE-IFD
git add -p && git commit -m "..."
git push origin master

# on VALAR (via ssh)
cd /scratch/hkanpak21/HE_IFD && git pull
sbatch jobs/<case>.sh
# when a job lands: git add results/<case>/ && git commit && git push
```

## Git remote

Origin is **`https://github.com/hkanpak21/HE-IFD.git`** (set up 2026-05-21).

### Auth on VALAR (configured 2026-05-21)

Credentials at `~/.git-credentials` (mode 600), via `git config --global credential.helper store` + a PAT the user left at `/scratch/hkanpak21/HE_IFD/git_token.txt` (gitignored). Future `git pull`/`push` from VALAR work silently. **Do NOT echo or commit the token.**

### Auth setup options (reference / future machines)

**Option A — SSH key (recommended for HPC):**
```sh
ssh-keygen -t ed25519 -C "hkanpak21@valar" -f ~/.ssh/id_ed25519
cat ~/.ssh/id_ed25519.pub                                            # paste into https://github.com/settings/keys
ssh -T git@github.com
cd /scratch/hkanpak21/HE_IFD && git remote set-url origin git@github.com:hkanpak21/HE-IFD.git
git push -u origin master
```
**Option B — PAT (HTTPS):** `git config --global credential.helper 'cache --timeout=86400'` then `git push -u origin master` (paste PAT as password).
**Option C — `gh` CLI:** not installed on VALAR; skip unless you install the Go binary manually.

### From local machine

Standard HTTPS-with-credential-helper or SSH key.

## Rsync alternative (if GitHub auth is painful)

```sh
# pull VALAR -> local
rsync -avz --exclude '.git/' --exclude 'data/' --exclude 'cache/' \
  hkanpak21@valar:/scratch/hkanpak21/HE_IFD/ ~/projects/HE-IFD/
# push local -> VALAR
rsync -avz --exclude '.git/' --exclude 'data/' --exclude 'cache/' \
  ~/projects/HE-IFD/ hkanpak21@valar:/scratch/hkanpak21/HE_IFD/
```
Faster iteration, but loses PR/diff review and bypasses local git history. Use only as a fast experimental loop, with periodic pushes to GitHub for backup.
