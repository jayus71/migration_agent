#!/usr/bin/env python3
"""Independent audit of the per-step divergence delivery.

Checks the delivered CSV against DATA_REQUEST_per_step_divergence.md section 8,
plus cross-consistency against the two pre-existing datasets it must agree with.
Independent of the vendor's own self-checks, which are recomputed here from the
CSV rather than read from the summary.

Run after installing requirements-analysis.txt:
    python scripts/verify_per_step_divergence.py
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

B = Path(__file__).resolve().parent.parent / "data/paper_section_65_66"
NEW = B / "results_section65_per_step_divergence/section65_per_step_divergence_steps50.csv"
OLD66 = B / "results_realdata_66/section66_realdata_training_consistency_steps_steps50.csv"
OLD65 = B / "results_section65_signal_sanity_current/section65_signal_effectiveness_table.csv"

THRESHOLDS = {"loss_abs": 0.02, "grad_norm_abs": 0.05, "param_update_rel_l2": 0.03}
# Candidate-side and derived columns only. The reference columns (torch_loss,
# torch_grad_norm) stay populated when the candidate crashes, because the
# PyTorch reference still ran.
CANDIDATE_COLS = [
    "torch4ms_loss", "loss_abs_diff", "loss_rel_diff",
    "torch4ms_grad_norm", "grad_norm_abs_diff", "grad_norm_rel_diff",
    "param_update_rel_l2", "param_update_cosine",
]
REFERENCE_COLS = ["torch_loss", "torch_grad_norm"]

results = []


def check(name, ok, detail=""):
    results.append((name, bool(ok), detail))
    print(f"[{'PASS' if ok else 'FAIL':4s}] {name}" + (f" -- {detail}" if detail else ""))


def main():
    df = pd.read_csv(NEW)
    # keep_default_na=False so "" (absent) is distinguishable from 0
    raw = pd.read_csv(NEW, keep_default_na=False, dtype=str)
    old66 = pd.read_csv(OLD66)
    old65 = pd.read_csv(OLD65)

    print("=== grid ===")
    check("row_count == 4800", len(df) == 4800, f"observed {len(df)}")
    g = df.groupby(["coupling", "fault", "model", "seed"]).size()
    check("96 combinations x 50 steps", len(g) == 96 and (g == 50).all(),
          f"{len(g)} combos, sizes {sorted(g.unique())}")
    check("steps are 1..50 in every group",
          df.groupby(["coupling", "fault", "model", "seed"])["step"]
            .apply(lambda s: sorted(s) == list(range(1, 51))).all())

    print("\n=== empty-vs-zero convention (spec section 3: absent must be blank, never 0) ===")
    exec_failed = raw[(raw.fault == "execution") & (raw.torch4ms_status != "ok")]
    check("execution failed rows: candidate metrics blank",
          (exec_failed[CANDIDATE_COLS] == "").all().all(),
          f"{len(exec_failed)} failed rows")
    check("execution failed rows: reference metrics still present",
          (exec_failed[REFERENCE_COLS] != "").all().all(),
          "the PyTorch reference still ran when the candidate crashed")
    train = raw[raw.fault == "training"]
    check("training rows: gradient metrics blank",
          (train[["torch4ms_grad_norm", "grad_norm_abs_diff", "grad_norm_rel_diff"]] == "").all().all())
    tokens = {c: int(raw[c].str.lower().isin(["nan", "inf", "-inf", "none", "null"]).sum())
              for c in CANDIDATE_COLS}
    check("no nan/inf/none tokens", not any(tokens.values()),
          str({k: v for k, v in tokens.items() if v}) or "clean")

    print("\n=== spec check 2: fault=none reproduces machine precision ===")
    none = df[df.fault == "none"]
    check("none: max loss_abs_diff < 1e-5", none.loss_abs_diff.max() < 1e-5,
          f"{none.loss_abs_diff.max():.4e}")
    check("none: max param_update_rel_l2 < 1e-4", none.param_update_rel_l2.max() < 1e-4,
          f"{none.param_update_rel_l2.max():.4e}")

    print("\n=== reference side must not be contaminated by the injected fault ===")
    for coup in ["teacher-forced", "free-running"]:
        base = df[(df.fault == "none") & (df.coupling == coup)][["model", "seed", "step", "torch_loss"]]
        for f in ["execution", "numeric", "training"]:
            o = df[(df.fault == f) & (df.coupling == coup)][["model", "seed", "step", "torch_loss"]]
            m = base.merge(o, on=["model", "seed", "step"], suffixes=("_a", "_b"))
            d = np.abs(m.torch_loss_a - m.torch_loss_b).max()
            check(f"{coup}: torch_loss identical none vs {f}", d == 0, f"max|delta|={d:.3e}")

    print("\n=== spec check 3: training + teacher-forced (the layering claim) ===")
    t = df[(df.fault == "training") & (df.coupling == "teacher-forced")]
    check("forward matches to <1e-5 for all 50 steps", t.loss_abs_diff.max() < 1e-5,
          f"max {t.loss_abs_diff.max():.4e}")
    check("param_update_rel_l2 == 1.0 throughout", np.allclose(t.param_update_rel_l2, 1.0))
    check("param_update_cosine == 0.0 throughout", np.allclose(t.param_update_cosine, 0.0))

    print("\n=== spec check 4: training + free-running rises after step 1 ===")
    for mdl in sorted(df.model.unique()):
        s = df[(df.fault == "training") & (df.coupling == "free-running") & (df.model == mdl)]
        mean = s.groupby("step").loss_abs_diff.mean()
        rho = pd.Series(mean.values).corr(pd.Series(mean.index), method="spearman")
        frac_inc = float(np.mean(np.diff(mean.values) > 0))
        crossed = mean[mean > THRESHOLDS["loss_abs"]].index.min()
        check(f"{mdl}: step-1 forward is clean", mean.loc[1] < 1e-5, f"{mean.loc[1]:.3e}")
        print(f"       {mdl:16s} spearman={rho:.3f} frac_increasing={frac_inc:.2f} "
              f"step50={mean.iloc[-1]:.5f} mean_crosses_thr="
              f"{'never' if pd.isna(crossed) else int(crossed)}")
        # per-seed crossing, which is what a figure would have to show honestly
        for seed, sg in s.groupby("seed"):
            sg = sg.sort_values("step")
            above = int((sg.loss_abs_diff > THRESHOLDS["loss_abs"]).sum())
            print(f"         seed {seed}: max={sg.loss_abs_diff.max():.5f} steps_above_thr={above}/50")

    print("\n=== spec check 5: numeric exceeds the loss threshold ===")
    num = df[df.fault == "numeric"]
    check("numeric: every row above loss threshold",
          (num.loss_abs_diff > THRESHOLDS["loss_abs"]).all(),
          f"min {num.loss_abs_diff.min():.4f}")
    for mdl in sorted(num.model.unique()):
        s = num[num.model == mdl]
        gmax = s.grad_norm_abs_diff.max()
        print(f"       {mdl:16s} loss median={s.loss_abs_diff.median():.4f} | "
              f"grad max={gmax:.4f} crosses_{THRESHOLDS['grad_norm_abs']}="
              f"{bool(gmax > THRESHOLDS['grad_norm_abs'])}")

    print("\n=== spec check 6: execution breaks at step 20 ===")
    e = raw[raw.fault == "execution"].copy()
    e["step"] = e.step.astype(int)
    failed = e[e.torch4ms_status != "ok"]
    check("first failure at step 20", failed.step.min() == 20, f"min {failed.step.min()}")
    check("steps 1-19 all ok", e[e.step < 20].torch4ms_status.eq("ok").all())
    check("failed count == 744 (31 steps x 3 seeds x 4 models x 2 couplings)",
          len(failed) == 744, f"observed {len(failed)}")

    print("\n=== cross-check: does fault=none match the existing 6.6 run? ===")
    n_tf = df[(df.fault == "none") & (df.coupling == "teacher-forced")]
    m = n_tf.merge(old66, on=["model", "seed", "step"], suffixes=("_new", "_old"))
    for mdl in sorted(m.model.unique()):
        s = m[m.model == mdl]
        d = np.abs(s.torch_loss_new - s.torch_loss_old).max()
        print(f"       {mdl:16s} max|delta torch_loss vs 6.6| = {d:.3e}"
              + ("   <-- different reference trajectory" if d > 1e-5 else ""))
    check("divergence metrics still machine precision despite trajectory change",
          n_tf.loss_abs_diff.max() < 1e-5 and n_tf.param_update_rel_l2.max() < 1e-4,
          "the diff columns are what the paper cites, and they hold")

    print("\n=== cross-check: fault magnitudes vs the existing 36-row 6.5 data ===")
    for f in ["numeric", "training"]:
        o = old65[old65.fault == f].loss_abs_diff.dropna()
        n = df[df.fault == f].loss_abs_diff.dropna()
        print(f"       {f:9s} old median={o.median():.4e} new median={n.median():.4e}")

    print("\n=== detection matrix vs paper Table V ===")
    print("       Table V: Num = N+G+U (TinyLM N+U) | Train = G+U")
    for mdl in ["cnn", "nlp", "transformer", "tiny_causal_lm"]:
        for f in ["numeric", "training"]:
            s = df[(df.fault == f) & (df.model == mdl) & (df.coupling == "teacher-forced")]
            sig = []
            if (s.loss_abs_diff > THRESHOLDS["loss_abs"]).any():
                sig.append("N")
            if (s.grad_norm_abs_diff > THRESHOLDS["grad_norm_abs"]).any():
                sig.append("G")
            elif s.grad_norm_abs_diff.isna().all():
                sig.append("G(missing-evidence)")
            if (s.param_update_rel_l2 > THRESHOLDS["param_update_rel_l2"]).any():
                sig.append("U")
            print(f"       {mdl:16s} {f:9s} -> {'+'.join(sig)}")

    failed_checks = [n for n, ok, _ in results if not ok]
    print(f"\n{'=' * 60}\n{len(results) - len(failed_checks)}/{len(results)} checks passed")
    if failed_checks:
        print("FAILED:")
        for n in failed_checks:
            print(f"  - {n}")
    return 1 if failed_checks else 0


if __name__ == "__main__":
    sys.exit(main())
