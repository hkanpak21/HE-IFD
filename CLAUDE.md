# CLAUDE.md — operational notes for the HE-IFD repo

Read this first when you (Claude) attach to this repo. It tells you how the user wants to work and what NOT to do.

## Deprecated material lives in this repo — be paranoid

This repository has accumulated **deprecated implementations, deprecated methodology drafts, and deprecated paper sections** that the user has explicitly retired. They are kept on disk for audit and provenance, **not** because they describe the current method. If you treat them as authoritative you will describe the wrong protocol, build on the wrong code, and reproduce numbers that were rejected.

Current source of truth (2026-05-21):
- **Methodology / protocol** → `src/v1/` (plaintext simulation of the *current* one-shot linear-aggregation design) plus whatever the user confirms in conversation.
- **Results** → `results/v1_he-ifd_mlp_mnist_n-sweep/` and any newer cases that follow the same `results/<case>/` convention.

Known-deprecated locations (do **not** mine these for methodology, equations, threat model, or experiment design):
- `FL_TDSC/archive/` — old methodology / experiments sections from the rejected draft. The earlier protocol there (encrypted ensemble target, encrypted SGD on the server, β/λ confidence-boost, encrypted-feature distillation, ViT/LeNet polynomial-activation stack) is **not** what we now do. The current protocol is: clients distil locally on `P ∪ D_i` against their own teachers, ship one encrypted per-layer parameter delta, server does only `θ₀ + (1/N)·Σ ΔW_i`, threshold-decrypt.
- `comparators/` — vendored upstream code (FedMD, FedDF, DENSE, etc.) for citation/audit; many vendors have stale APIs and are not runnable. Numbers we cite come from `comparators/REPORTED_RESULTS.md`, which is verbatim from the published papers.
- Anything else under `FL_TDSC/` outside `main.tex`, `methodology.tex`, `experiments.tex` (the *non-archive* copies) — older drafts will live in git history; do not resurrect them without explicit user direction.

**Rule of thumb.** If a file's content disagrees with `src/v1/` or with what the user just said in this conversation, the file is wrong, not the conversation. Ask before relying on it. The Overleaf-style `methodology.tex` and `experiments.tex` at the root of `FL_TDSC/` will be rewritten in a separate intentional pass to match the current code; until then, treat them as stale too.

## The workflow

The user develops on a local machine (Mac/Linux/Windows) and runs all compute on the **VALAR** HPC cluster. Specifically:

1. **Local machine**: edit source (`src/v1/`, `jobs/*.sh`, `comparators/`), read results (`results/<case>/`), inspect papers, commit to git.
2. **VALAR login node** (`ai*.kuvalar.ku.edu.tr`): submit Slurm jobs (`sbatch jobs/*.sh`), monitor (`squeue`, `sacct`), read result JSONs, do git ops. **No Python compute on the login node, ever.**
3. **VALAR compute node** (allocated by `sbatch`): runs the actual Python — training, distillation, FHE primitives, etc.

When Claude runs **on the VALAR side** (which is where this repo lives, at `/scratch/hkanpak21/HE_IFD`), Claude should treat itself as on the login node and submit all compute via `sbatch`.

## GOLDEN RULE

**Never run `python` on the login node** if the script imports torch, tenseal, or anything that does training, FHE, or data generation. The only allowed `python` invocations on the login node are:

- syntax checks (`python -c "import ast; ast.parse(open(f).read())"`)
- text-only utilities (`tools/pdf_extract.py` for inspecting papers — pure pypdf, no compute)
- `argparse --help` to verify a CLI

Everything else goes through `sbatch jobs/<wrapper>.sh` or `srun --partition=t4_ai --account=comx29 ...` (only for very short < 5-min sanity checks; prefer `sbatch`).

## Submitting a job — quickstart

```sh
# from /scratch/hkanpak21/HE_IFD on the login node
sbatch jobs/v1_sweep.sh                                # defaults
V1_NS=1,2,4 V1_SEEDS=42,7 sbatch jobs/v1_sweep.sh      # override via env vars (see jobs/v1_sweep.sh header)
```

The sweep submits as a single job, runs all cells in series, and writes outputs to `results/v1_he-ifd_mlp_mnist_n-sweep/` with per-cell JSONs + a populated `README.md` + `results.csv`. Logs go to `results/v1_he-ifd_mlp_mnist_n-sweep/runs/sweep_<jobid>.{out,err}`.

## Monitoring a running job

```sh
squeue -u hkanpak21 -o "%.10i %.18j %.8T %.10M %R"                              # what's running / pending
sacct -X -u hkanpak21 --starttime=$(date -d '12 hours ago' +%FT%T) -o JobID,JobName,State,Elapsed,ExitCode
tail -f results/v1_he-ifd_mlp_mnist_n-sweep/runs/sweep_<jobid>.out               # live log
```

When orchestrating live, use the Monitor tool with a filter that skips tqdm noise (see prior session for the pattern).

## Conda environment

The single env we use is **`he_ofl`** (already exists at `/home/hkanpak21/.conda/envs/he_ofl`). Has installed: `torch 2.3.0+cu121`, `torchvision`, `tenseal 0.3.16`, `numpy`, `pypdf`, `termcolor`, `xgboost`, `pydicom`, `opacus` (from earlier comparator setup).

If a new dep is needed: `pip install --quiet <pkg>` from the login node is fine. Avoid `conda install` because the base env is read-only on this cluster.

## Slurm template (use this for new sbatch wrappers)

```bash
#!/bin/bash
#SBATCH --partition=t4_ai
#SBATCH --account=comx29
#SBATCH --qos=comx29
#SBATCH --gres=gpu:tesla_t4:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=24G              # bump to 64G+ for TenSEAL / multiparty CKKS work
#SBATCH --time=04:00:00
#SBATCH --job-name=<name>
#SBATCH --output=/scratch/hkanpak21/HE_IFD/results/<case>/runs/<name>_%j.out
#SBATCH --error=/scratch/hkanpak21/HE_IFD/results/<case>/runs/<name>_%j.err

set -euo pipefail
cd /scratch/hkanpak21/HE_IFD
source /opt/ohpc/pub/compiler/conda3/latest/etc/profile.d/conda.sh
conda activate he_ofl
exec srun python -u -m src.v1.<entrypoint> "$@"
```

## Datasets

Pre-fetched at:

```
data/MNIST/raw/                # MNIST, ready to load with torchvision (download=False)
data/FashionMNIST/raw/
data/cifar-10-batches-py/
data/cifar-10-python.tar.gz
```

Loaders in `src/v1/data.py` already use `download=False` and point at the repo's `data/` root. Don't re-download.

## Repo layout (post-2026-05-21)

```
src/v1/                              # current source. Single-version simulation.
  data.py                              MNIST loader + Dirichlet partition + probe extraction
  model.py                             MLP 784→128→32→10 with named per-layer state I/O
  teacher.py                           per-client teacher training (seed-keyed cache)
  distill.py                           local KL distillation, end-of-K cumulative deltas
  aggregate.py                         server-side linear aggregator (FHE-compatible by construction)
  evaluation.py                        accuracy helpers
  cell.py                              single (N, seed) → CellResult JSON
  sweep.py                             CLI: sweep over Ns + seeds
  report.py                            auto-writes per-case README + results.csv + partition_diagnostic.jsonl

jobs/                                # sbatch wrappers — the ONLY entrypoints that run python
  v1_sweep.sh                          the N-sweep wrapper

comparators/                         # vendored upstream code, audit-trail-only commit (rest gitignored)
  REPORTED_RESULTS.md                  per-paper extracted tables, paper-verbatim
  fedmd/, feddf/, dense/, coboosting/, feddiff/, fedkt/, poseidon/
                                       each: COMMIT.txt + minimal source (heavy data dropped)

results/<case>/                      # per experimental case (one folder per case, per the user's results_formatting.md spec)
  README.md                            3-sentence description + auto-populated results table
  results.csv                          long-form rows (auto)
  partition_diagnostic.jsonl           per-client per-class counts (auto)
  cell_<N>_s<seed>_<jobid>.json        per-cell results
  runs/sweep_<jobid>.{out,err}         Slurm logs

data/                                # gitignored — datasets stay on VALAR scratch
cache/                               # gitignored — teacher checkpoints, regenerable from seed
tools/                               # gitignored — local-only utilities (pdf_extract.py etc.)
FL_TDSC/                             # paper sources + CHANGES.md (Overleaf replay log)
```

## When the user asks you to "run X" or "sweep Y"

1. Locate or write the `jobs/<X>.sh` wrapper using the template above.
2. `sbatch jobs/<X>.sh` from the login node. Capture the `<jobid>`.
3. If asked to monitor live, use the Monitor tool with `tail -F .out` and a grep filter that keeps `[sweep] ok|FAIL`, `Traceback`, `OOM`, `CUDA`, `RuntimeError` — drop `it/s` tqdm noise.
4. When the job finishes, read `results/<case>/cell_*.json` and any auto-written `results/<case>/README.md`.
5. Never `tail -F` a slurm log on the login node directly (it's fine in a Monitor task because that's a managed background).

## When the user asks you to "add a new experiment"

1. Decide the case slug: `<version>_<method>_<model>_<dataset>_<axis>` (e.g. `v2_he-ifd_cnn_cifar10_dp-sweep`).
2. Create `results/<case>/` with a placeholder `README.md` (one-paragraph description); the auto-writer will populate the table.
3. Make sure the entrypoint module is importable as `src.<version>.<module>`.
4. Write the sbatch wrapper at `jobs/<case>.sh` using the template above.
5. Submit.

## When the user asks you to "compare against X"

1. Check `comparators/REPORTED_RESULTS.md` first — many published numbers are already extracted.
2. The vendored upstream code is at `comparators/<vendor>/`. Many vendors have stale APIs (Co-Boosting needs old torchvision, FedKT needs old TF-Privacy port, FedDiff upstream is empty). Confirm runnability before promising a re-run.

## Things to NOT do

- **Never `python ...` on the login node** if it would do training, FHE, or model loading. Submit via `sbatch`.
- **Never re-download datasets.** They're cached at `data/MNIST/`, `data/FashionMNIST/`, `data/cifar-10-batches-py/`. Use `download=False` in torchvision loaders.
- **Never commit big binaries.** Datasets, teacher checkpoints, slurm logs are gitignored. If a new heavy artefact appears, add it to `.gitignore` before committing.
- **Never invent numbers from prior papers.** Use `tools/pdf_extract.py` (or just open the PDF with pypdf) and quote verbatim. The previous draft of `REPORTED_RESULTS.md` was full of LLM-recollection errors; the user's critique caught it.
- **Never edit `FL_TDSC/*.tex` without explicit user direction.** The paper text reflects prior methodology decisions; it will be rewritten in a separate intentional pass.

## Common operations cheatsheet

| Task | Command |
|---|---|
| Submit v1 sweep | `sbatch jobs/v1_sweep.sh` |
| Submit with overrides | `V1_NS=1,2,4 V1_SEEDS=42,7 sbatch jobs/v1_sweep.sh` |
| Watch queue | `watch -n 30 squeue -u hkanpak21` (or one-shot: `squeue -u hkanpak21`) |
| Recent history | `sacct -X -u hkanpak21 --starttime=$(date -d '6 hours ago' +%FT%T) -o JobID,JobName,State,Elapsed,ExitCode` |
| Aggregate sweep results | `python -c "from src.v1 import report; ..."` — auto-runs at sweep end |
| Tail a running job | `tail -F results/<case>/runs/<name>_<jobid>.out` |
| Cancel a job | `scancel <jobid>` |
| PDF inspection | `python tools/pdf_extract.py <pdf> "<keywords>" --context 2` |

## Local-side workflow

```sh
# on local machine
git clone https://github.com/hkanpak21/HE-IFD.git
cd HE-IFD
# edit src/v1/*.py, jobs/*.sh, comparators/REPORTED_RESULTS.md
git add -p && git commit -m "..."
git push origin master

# on VALAR (via ssh)
cd /scratch/hkanpak21/HE_IFD && git pull
sbatch jobs/v1_sweep.sh
# when job lands, `git add results/<case>/ && git commit && git push` so local sees it
```

## Git remote

Origin is **`https://github.com/hkanpak21/HE-IFD.git`**, set up 2026-05-21.

### Auth on VALAR (configured 2026-05-21)

Credentials are stored at `~/.git-credentials` (mode 600), populated via `git config --global credential.helper store` and a Personal Access Token the user left at `/scratch/hkanpak21/HE_IFD/git_token.txt` (gitignored). Future `git pull` / `git push` from VALAR work silently.

**Do NOT echo or commit the token.** `git_token.txt` is in `.gitignore`; `~/.git-credentials` lives outside the repo. If the token rotates, the user updates `~/.git-credentials` directly or re-runs the setup below.

### Auth setup options (for reference / future machines)

The push from VALAR will fail until one of these is done. Pick whichever the user prefers:

**Option A — SSH key (recommended for HPC).** Generate a key on VALAR, add the public half to GitHub, switch the remote to SSH:

```sh
ssh-keygen -t ed25519 -C "hkanpak21@valar" -f ~/.ssh/id_ed25519     # no passphrase = no prompt per push
cat ~/.ssh/id_ed25519.pub                                            # paste into https://github.com/settings/keys
ssh -T git@github.com                                                # verify
cd /scratch/hkanpak21/HE_IFD
git remote set-url origin git@github.com:hkanpak21/HE-IFD.git
git push -u origin master
```

**Option B — Personal Access Token (HTTPS).** Create a PAT with `repo` scope at https://github.com/settings/tokens, then:

```sh
git config --global credential.helper 'cache --timeout=86400'
git push -u origin master         # asks for username + paste PAT as password; cached 24h
```

**Option C — `gh` CLI**. Not installed on VALAR; `pip install --user gh` doesn't ship one (gh is a Go binary). Skip unless you install the binary manually.

The user almost certainly wants Option A. Once the SSH key is set up once, every future `git pull` / `git push` from VALAR is silent.

### From local machine (Mac / Linux / WSL)

Standard HTTPS-with-credential-helper or SSH key as you already use for other GitHub repos. No special setup beyond the standard `git clone https://...` or `git clone git@github.com:hkanpak21/HE-IFD.git`.

## Rsync alternative (if GitHub auth is painful)

Skip the remote and sync directly:

```sh
# from local; pulls VALAR -> local
rsync -avz --exclude '.git/' --exclude 'data/' --exclude 'cache/' \
  hkanpak21@valar:/scratch/hkanpak21/HE_IFD/ ~/projects/HE-IFD/

# from local; pushes local -> VALAR
rsync -avz --exclude '.git/' --exclude 'data/' --exclude 'cache/' \
  ~/projects/HE-IFD/ hkanpak21@valar:/scratch/hkanpak21/HE_IFD/
```

Cheaper iteration loop if you don't want a GitHub round-trip per change, but loses the PR/diff review surface and bypasses git history on local. Recommended only as a fast experimental loop, with periodic git pushes to GitHub for backup.
