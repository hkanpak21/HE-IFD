# real_query/ — the exports the real-query run consumes

**The record for that run is one directory up: `../real_query.csv` and
`../real_query_README.md`.** Nothing here is a result.

`jobs/fhe_export_head.sh` writes `<task>_s<seed>_<arrangement>.json` here on
VALAR: the served head (W, b) rebuilt from a recorded artifact, real test
features under the same frozen backbone, and the plaintext logits and argmax the
encrypted answer is compared against. `jobs/fhe_serve_real.sh` writes
`<name>_answers.json` beside it. Neither is committed; each export is about
0.34 MB of float64 features and regenerates from the artifact in under a minute.

`mechanism_check_synthetic.csv` is the serving path run on a random head at the
real shape (C=4, d=768, three queries, N=3) on a laptop, before the artifacts
were reachable. It is a code check. **Do not cite it and do not put it in the
paper.**
