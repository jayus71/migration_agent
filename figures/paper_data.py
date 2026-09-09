"""Read plotted results without changing their original scoring definitions."""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
THRESHOLDS = {"loss_abs_diff": 0.02, "grad_norm_abs_diff": 0.05,
              "param_update_rel_l2": 0.03}
FIXED50 = ROOT / "data/paper_figures/fixed50_original_summary.csv"
SIGNAL_ABLATION = ROOT / "data/paper_figures/signal_ablation_by_fault.csv"
ORIGINAL_STEPS = (ROOT / "data/paper_section_65_66"
                  / "results_section65_per_step_divergence"
                  / "section65_per_step_divergence_steps50.csv")
GRADIENT_STEPS = (ROOT / "data/experiments/03_experiment_C_gradient_and_parameter_faults"
                  / "results_per_step/section65_per_step_divergence_steps50.csv")
LOCALIZATION = (ROOT / "data/experiments/11_experiment_K_layer_localization/results"
                / "section65_fault_pool_localization_confusion_matrix.csv")
METHODS = ["r_exec", "r_flat", "r_direct", "r_swe", "r_matchfix", "r_hier"]
METHOD_LABELS = ["Execution only", "All signals", "Direct LLM",
                 "SWE-agent", "MatchFixAgent", "LADDER"]
STAGES = ["execution", "numerical", "gradient_update"]


def fixed50():
    frame = pd.read_csv(FIXED50).set_index("baseline_id")
    if not frame.index.is_unique or set(frame.index) != set(METHODS):
        raise ValueError("Expected exactly six original Fixed50 methods")
    frame = frame.loc[METHODS].copy()
    if not frame.instances.eq(50).all():
        raise ValueError("Mixed instance pools in the original Fixed50 snapshot")
    if not frame.total_tokens.eq(frame.prompt_tokens + frame.completion_tokens).all():
        raise ValueError("Token totals do not match prompt plus completion")
    passed = frame[[f"{stage}_success" for stage in STAGES]].sum(axis=1)
    if not passed.eq(frame.strict_success).all():
        raise ValueError("Fault-stage counts do not sum to original accepted repairs")
    frame["tokens_per_accepted_repair"] = frame.total_tokens / frame.strict_success
    return frame


def signal_ablation():
    frame = pd.read_csv(SIGNAL_ABLATION).set_index("fault_type").loc[STAGES]
    conditions = ["exec_only_success", "exec_num_success", "exec_num_grad_success"]
    counts = frame[conditions].to_numpy().T
    totals = frame.tasks.to_numpy()
    if not (totals == 4).all():
        raise ValueError("Expected four signal-ablation tasks per stage")
    if (counts < 0).any() or (counts > totals).any():
        raise ValueError("Invalid signal-ablation counts")
    return counts, totals


def budget_acceptance():
    frame = fixed50()
    budgets = (1, 2, 4)
    rates = frame[[f"repair_at_{budget}" for budget in budgets]].copy()
    rates.columns = list(budgets)
    values = rates.to_numpy()
    counts = rates.mul(frame.instances, axis=0).to_numpy()
    if (not np.isfinite(values).all() or (values < 0).any() or (values > 1).any()
            or (np.diff(values, axis=1) < 0).any()
            or not np.allclose(counts, np.rint(counts))):
        raise ValueError("Invalid cumulative acceptance checkpoints")
    if not np.allclose(counts[:, -1], frame.strict_success):
        raise ValueError("Four-attempt checkpoint disagrees with accepted repairs")
    return rates


def fault_signatures():
    original = pd.read_csv(ORIGINAL_STEPS)
    extra = pd.read_csv(GRADIENT_STEPS)
    original = original[original.coupling.eq("teacher-forced")]
    extra = extra[extra.coupling.eq("teacher-forced")]
    groups = [original[original.fault.eq("none")],
              original[original.fault.eq("execution") & original.torch4ms_status.eq("failed")],
              original[original.fault.eq("numeric")],
              extra[extra.fault.eq("grad_wrong")],
              extra[extra.fault.eq("param_wrong")]]
    values = []
    for group in groups:
        if group.empty:
            raise ValueError("Missing fault-signature source rows")
        row = [float(group.torch4ms_status.eq("failed").any())]
        for metric, threshold in THRESHOLDS.items():
            measured = group[metric].dropna()
            # A crashed run has no metric; absence must not look like a passed check.
            row.append(float(measured.gt(threshold).any()) if len(measured) else np.nan)
        values.append(row)
    return np.asarray(values)


def localization():
    frame = pd.read_csv(LOCALIZATION)
    matrix = frame.pivot(index="expected_layer", columns="predicted_layer",
                         values="instances")
    outside = matrix.drop(columns=STAGES, errors="ignore")
    if outside.to_numpy().sum() != 0 or not matrix.index.isin(STAGES).all():
        raise ValueError("Localization contains unplotted classes")
    values = matrix.loc[STAGES, STAGES].to_numpy()
    if not np.isfinite(values).all() or (values < 0).any() or values.sum() != 50:
        raise ValueError("Invalid localization matrix")
    return values
