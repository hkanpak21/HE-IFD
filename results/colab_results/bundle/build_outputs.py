"""
Build all paper-ready CSV files and a single Excel workbook from the
parsed long-form results.

Outputs (under /home/claude/he_ifd_parsed/):
  raw_all_results.csv                 - 861 rows, long form
  section_A_per_run.csv               - all section-A rows
  section_A_aggregated.csv            - mean ± std across seeds
  section_A_protocol_contribution.csv - protocol delta over warmup_only
  section_B_per_run.csv
  section_B_aggregated.csv
  section_C_per_run.csv
  section_C_aggregated.csv
  section_D_per_run.csv
  section_D_aggregated.csv
  section_D_best_per_alpha.csv        - best (eps, K) per setup-alpha
  paper_headline_table.csv            - one row per (section, setup, alpha, method) with mean ± std
  he_ifd_results.xlsx                 - single Excel workbook with all sheets
"""

import numpy as np
import pandas as pd

BASE = "/home/claude/he_ifd_parsed"

# Load the long-form CSV
df = pd.read_csv(f"{BASE}/raw_all_results.csv")
print(f"Loaded {len(df)} rows")

# ============================================================================
# Per-run CSVs (one per section)
# ============================================================================
for sec in ["A", "B", "C", "D"]:
    sub = df[df["section"] == sec].copy()
    sub.to_csv(f"{BASE}/section_{sec}_per_run.csv", index=False)
    print(f"  section_{sec}_per_run.csv : {len(sub)} rows")


# ============================================================================
# Section A: aggregated + protocol contribution table
# ============================================================================
df_A = df[df["section"] == "A"].copy()
agg_A = (df_A.groupby(["setup", "alpha", "probe_size", "method"])["acc"]
              .agg(mean="mean", std="std", count="count")
              .reset_index()
              .sort_values(["alpha", "probe_size", "method"]))
agg_A.to_csv(f"{BASE}/section_A_aggregated.csv", index=False)
print(f"  section_A_aggregated.csv : {len(agg_A)} rows")

# Protocol contribution table
method_order_A = ["no_phase0", "warmup_only_labelled", "labelled_probe_warmup",
                   "raw_union_K20", "dp_avg_eps2_K20", "dp_avg_eps8_K20"]
PROTOCOL_METHODS = ["raw_union_K20", "labelled_probe_warmup",
                    "dp_avg_eps2_K20", "dp_avg_eps8_K20"]

rows = []
for alpha in sorted(df_A["alpha"].unique()):
    for P in sorted(df_A["probe_size"].unique()):
        sub = agg_A[(agg_A["alpha"] == alpha) & (agg_A["probe_size"] == P)]
        row = {"alpha": alpha, "probe_size": P}
        for m in method_order_A:
            r = sub[sub["method"] == m]
            if len(r):
                row[f"{m}_mean"] = round(r["mean"].iloc[0], 4)
                row[f"{m}_std"]  = round(r["std"].iloc[0], 4)
        # best-protocol - warmup_only_labelled
        wo = sub[sub["method"] == "warmup_only_labelled"]["mean"]
        prot = sub[sub["method"].isin(PROTOCOL_METHODS)]["mean"]
        if len(wo) and len(prot):
            row["best_protocol_minus_warmup_only"] = round(prot.max() - wo.iloc[0], 4)
        rows.append(row)
contrib_A = pd.DataFrame(rows)
contrib_A.to_csv(f"{BASE}/section_A_protocol_contribution.csv", index=False)
print(f"  section_A_protocol_contribution.csv : {len(contrib_A)} rows")


# ============================================================================
# Section B: aggregated
# ============================================================================
df_B = df[df["section"] == "B"].copy()
agg_B = (df_B.groupby(["backbone", "alpha", "method"])["acc"]
              .agg(mean="mean", std="std", count="count")
              .reset_index()
              .sort_values(["backbone", "alpha", "method"]))
agg_B.to_csv(f"{BASE}/section_B_aggregated.csv", index=False)
print(f"  section_B_aggregated.csv : {len(agg_B)} rows")


# ============================================================================
# Section C: aggregated
# ============================================================================
df_C = df[df["section"] == "C"].copy()
agg_C = (df_C.groupby(["backbone", "alpha", "method"])["acc"]
              .agg(mean="mean", std="std", count="count")
              .reset_index()
              .sort_values(["backbone", "alpha", "method"]))
agg_C.to_csv(f"{BASE}/section_C_aggregated.csv", index=False)
print(f"  section_C_aggregated.csv : {len(agg_C)} rows")


# ============================================================================
# Section D: aggregated, plus best (ε, K) per (setup, α)
# ============================================================================
df_D = df[df["section"] == "D"].copy()
agg_D = (df_D.groupby(["setup", "alpha", "eps", "K_per_class"])["acc"]
              .agg(mean="mean", std="std", count="count")
              .reset_index()
              .sort_values(["setup", "alpha", "eps", "K_per_class"]))
agg_D.to_csv(f"{BASE}/section_D_aggregated.csv", index=False)
print(f"  section_D_aggregated.csv : {len(agg_D)} rows")

# Best (eps, K) per (setup, α). Also: ε=inf reference at same K
best_rows = []
for setup in sorted(df_D["setup"].unique()):
    for alpha in sorted(df_D["alpha"].unique()):
        sub = agg_D[(agg_D["setup"] == setup) & (agg_D["alpha"] == alpha)]
        # Best DP (not inf)
        finite = sub[sub["eps"] != np.inf]
        if len(finite):
            best_finite = finite.sort_values("mean", ascending=False).iloc[0]
            inf_at_K = sub[(sub["eps"] == np.inf)
                             & (sub["K_per_class"] == best_finite["K_per_class"])]
            inf_acc = inf_at_K["mean"].iloc[0] if len(inf_at_K) else None
            # Strict DP @ ε=2
            strict = sub[(sub["eps"] == 2.0)]
            best_strict = strict.sort_values("mean", ascending=False).iloc[0] if len(strict) else None
            row = {
                "setup": setup,
                "alpha": alpha,
                "best_DP_eps": best_finite["eps"],
                "best_DP_K": best_finite["K_per_class"],
                "best_DP_acc_mean": round(best_finite["mean"], 4),
                "best_DP_acc_std": round(best_finite["std"], 4),
                "no_noise_at_same_K_acc": round(inf_acc, 4) if inf_acc is not None else None,
                "DP_cost": round(inf_acc - best_finite["mean"], 4) if inf_acc is not None else None,
                "strict_eps2_K20_mean": round(strict[strict["K_per_class"] == 20]["mean"].iloc[0], 4)
                                            if len(strict[strict["K_per_class"] == 20]) else None,
                "strict_eps2_K20_std": round(strict[strict["K_per_class"] == 20]["std"].iloc[0], 4)
                                            if len(strict[strict["K_per_class"] == 20]) else None,
            }
            best_rows.append(row)
best_D = pd.DataFrame(best_rows)
best_D.to_csv(f"{BASE}/section_D_best_per_alpha.csv", index=False)
print(f"  section_D_best_per_alpha.csv : {len(best_D)} rows")


# ============================================================================
# Paper headline table: one row per (section, setup, alpha, [probe], method)
# Includes mean and std, suitable for direct inclusion in the paper appendix.
# ============================================================================
headline_rows = []

# Section A
for _, r in agg_A.iterrows():
    headline_rows.append({
        "section": "A",
        "setup": r["setup"],
        "backbone": "MLP",
        "alpha": r["alpha"],
        "probe_size": r["probe_size"],
        "method": r["method"],
        "acc_mean": round(r["mean"], 4),
        "acc_std": round(r["std"], 4) if pd.notna(r["std"]) else None,
        "n_seeds": int(r["count"]),
    })

# Section B
for _, r in agg_B.iterrows():
    headline_rows.append({
        "section": "B",
        "setup": f"cifar10_{r['backbone']}",
        "backbone": r["backbone"],
        "alpha": r["alpha"],
        "probe_size": None,
        "method": r["method"],
        "acc_mean": round(r["mean"], 4),
        "acc_std": round(r["std"], 4) if pd.notna(r["std"]) else None,
        "n_seeds": int(r["count"]),
    })

# Section C
for _, r in agg_C.iterrows():
    headline_rows.append({
        "section": "C",
        "setup": f"ag_news_{r['backbone']}",
        "backbone": r["backbone"],
        "alpha": r["alpha"],
        "probe_size": None,
        "method": r["method"],
        "acc_mean": round(r["mean"], 4),
        "acc_std": round(r["std"], 4) if pd.notna(r["std"]) else None,
        "n_seeds": int(r["count"]),
    })

# Section D
for _, r in agg_D.iterrows():
    eps_str = "inf" if r["eps"] == np.inf else str(r["eps"])
    headline_rows.append({
        "section": "D",
        "setup": r["setup"],
        "backbone": r["setup"].replace("cifar10_", "").replace("ag_news_", ""),
        "alpha": r["alpha"],
        "probe_size": None,
        "method": f"dp_avg_eps{eps_str}_K{int(r['K_per_class'])}",
        "acc_mean": round(r["mean"], 4),
        "acc_std": round(r["std"], 4) if pd.notna(r["std"]) else None,
        "n_seeds": int(r["count"]),
    })

paper_headline = pd.DataFrame(headline_rows)
paper_headline.to_csv(f"{BASE}/paper_headline_table.csv", index=False)
print(f"  paper_headline_table.csv : {len(paper_headline)} rows")


# ============================================================================
# Wide-format pivot tables for easy paper inclusion
# ============================================================================
# Section A wide pivot: rows = (alpha, P), cols = method (mean acc only)
wide_A_mean = (df_A.groupby(["alpha", "probe_size", "method"])["acc"].mean()
                  .unstack("method").round(4)
                  .reindex(columns=method_order_A))
wide_A_mean.to_csv(f"{BASE}/section_A_wide_mean.csv")
print(f"  section_A_wide_mean.csv : pivot table")

wide_A_std = (df_A.groupby(["alpha", "probe_size", "method"])["acc"].std()
                 .unstack("method").round(4)
                 .reindex(columns=method_order_A))
wide_A_std.to_csv(f"{BASE}/section_A_wide_std.csv")

# Section B wide pivot per backbone
method_order_BC = ["no_phase0", "labelled_probe_warmup", "raw_union_K20",
                    "dp_avg_eps2_K20", "dp_avg_eps8_K20"]
for sec, df_sec in [("B", df_B), ("C", df_C)]:
    for bb in df_sec["backbone"].unique():
        sub = df_sec[df_sec["backbone"] == bb]
        wide_mean = (sub.groupby(["alpha", "method"])["acc"].mean()
                          .unstack("method").round(4)
                          .reindex(columns=method_order_BC))
        wide_std = (sub.groupby(["alpha", "method"])["acc"].std()
                         .unstack("method").round(4)
                         .reindex(columns=method_order_BC))
        wide_mean.to_csv(f"{BASE}/section_{sec}_{bb}_wide_mean.csv")
        wide_std.to_csv(f"{BASE}/section_{sec}_{bb}_wide_std.csv")


# Section D wide pivots: rows = eps, cols = K_per_class, one per (setup, α)
EPS_ORDER = [0.5, 2.0, 8.0, 32.0, np.inf]
K_ORDER = [1, 5, 20]
for setup in df_D["setup"].unique():
    for alpha in sorted(df_D["alpha"].unique()):
        sub = df_D[(df_D["setup"] == setup) & (df_D["alpha"] == alpha)]
        wm = (sub.groupby(["eps", "K_per_class"])["acc"].mean()
                 .unstack("K_per_class").round(4))
        # Reindex to consistent order, eps=inf last
        wm = wm.reindex([e for e in EPS_ORDER if e in wm.index])
        wm = wm.reindex(columns=[k for k in K_ORDER if k in wm.columns])
        alpha_clean = str(alpha).replace(".", "p")
        wm.to_csv(f"{BASE}/section_D_{setup}_alpha{alpha_clean}_wide_mean.csv")


# ============================================================================
# Excel workbook with all sheets
# ============================================================================
print("\nBuilding Excel workbook...")
with pd.ExcelWriter(f"{BASE}/he_ifd_results.xlsx", engine="openpyxl") as xw:
    # Top-level raw data
    df.to_excel(xw, sheet_name="00_raw_all_results", index=False)
    paper_headline.to_excel(xw, sheet_name="01_paper_headline_table", index=False)

    # Section A
    df_A.to_excel(xw, sheet_name="A_per_run", index=False)
    agg_A.to_excel(xw, sheet_name="A_aggregated", index=False)
    contrib_A.to_excel(xw, sheet_name="A_protocol_contribution", index=False)
    wide_A_mean.to_excel(xw, sheet_name="A_wide_mean")
    wide_A_std.to_excel(xw, sheet_name="A_wide_std")

    # Section B
    df_B.to_excel(xw, sheet_name="B_per_run", index=False)
    agg_B.to_excel(xw, sheet_name="B_aggregated", index=False)
    for bb in df_B["backbone"].unique():
        sub = df_B[df_B["backbone"] == bb]
        wm = (sub.groupby(["alpha", "method"])["acc"].mean()
                 .unstack("method").round(4)
                 .reindex(columns=method_order_BC))
        ws = (sub.groupby(["alpha", "method"])["acc"].std()
                 .unstack("method").round(4)
                 .reindex(columns=method_order_BC))
        wm.to_excel(xw, sheet_name=f"B_{bb}_mean")
        ws.to_excel(xw, sheet_name=f"B_{bb}_std")

    # Section C
    df_C.to_excel(xw, sheet_name="C_per_run", index=False)
    agg_C.to_excel(xw, sheet_name="C_aggregated", index=False)
    for bb in df_C["backbone"].unique():
        sub = df_C[df_C["backbone"] == bb]
        wm = (sub.groupby(["alpha", "method"])["acc"].mean()
                 .unstack("method").round(4)
                 .reindex(columns=method_order_BC))
        ws = (sub.groupby(["alpha", "method"])["acc"].std()
                 .unstack("method").round(4)
                 .reindex(columns=method_order_BC))
        wm.to_excel(xw, sheet_name=f"C_{bb}_mean")
        ws.to_excel(xw, sheet_name=f"C_{bb}_std")

    # Section D
    df_D.to_excel(xw, sheet_name="D_per_run", index=False)
    agg_D.to_excel(xw, sheet_name="D_aggregated", index=False)
    best_D.to_excel(xw, sheet_name="D_best_per_alpha", index=False)
    for setup in df_D["setup"].unique():
        for alpha in sorted(df_D["alpha"].unique()):
            sub = df_D[(df_D["setup"] == setup) & (df_D["alpha"] == alpha)]
            wm = (sub.groupby(["eps", "K_per_class"])["acc"].mean()
                     .unstack("K_per_class").round(4))
            wm = wm.reindex([e for e in EPS_ORDER if e in wm.index])
            wm = wm.reindex(columns=[k for k in K_ORDER if k in wm.columns])
            alpha_clean = str(alpha).replace(".", "p")
            # Excel sheet name limit is 31 chars
            short_setup = setup.replace("cifar10_", "c10_").replace("ag_news_", "agn_")
            sheet_name = f"D_{short_setup}_a{alpha_clean}"[:31]
            wm.to_excel(xw, sheet_name=sheet_name)

print(f"\nAll outputs written to {BASE}/")
import os
for f in sorted(os.listdir(BASE)):
    size = os.path.getsize(f"{BASE}/{f}") / 1024
    print(f"  {f}  ({size:.1f} KB)")
