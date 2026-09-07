#!/usr/bin/env python3
"""Token cost composition: the gap is in prompt tokens, not completion.

Data from experiments/baselines/full_hier_fixed50/summary.csv, aggregated to
match Table I. Hard-coded here so the figure cannot drift from the manuscript.

Source: EXPERIMENT_REQUEST_20260820.md Figure 4 data; cross-checked against
Table I token totals (5.205M / 7.635M / 1.583M / 0.191M / 0.180M / 0.155M).
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

# (name, prompt_K, completion_K, family)
# Prompt + completion = total tokens in Table I.
METHODS = [
    ("R-EXEC\n(exec. only)",  108.3,   46.5, "reduced"),
    ("R-FLAT\n(unordered)",   111.4,   69.0, "reduced"),
    ("LADDER\n(ours)",        147.3,   43.3, "ours"),
    ("Direct LLM",           1406.3,  176.6, "baseline"),
    ("MatchFixAgent",        4739.4,  465.8, "baseline"),
    ("SWE-agent",            7512.5,  122.5, "baseline"),
]

INK = "#1a1a1a"
MUTED = "#5c5c5c"
EDGE = "#9a9a9a"

PROMPT_COLOR = "#2171b5"
COMPLETION_COLOR = "#6baed6"

fig, ax = plt.subplots(figsize=(3.4, 2.8))

y = np.arange(len(METHODS))
names = [m[0] for m in METHODS]
prompts = [m[1] for m in METHODS]
completions = [m[2] for m in METHODS]
totals = [p + c for p, c in zip(prompts, completions)]

bars_p = ax.barh(y, prompts, height=0.55, color=PROMPT_COLOR,
                 edgecolor="white", linewidth=0.5, label="Prompt", zorder=3)
bars_c = ax.barh(y, completions, height=0.55, left=prompts,
                 color=COMPLETION_COLOR, edgecolor="white", linewidth=0.5,
                 label="Completion", zorder=3)

# Labels: prompt percentage on each bar
for i, (p, c, t) in enumerate(zip(prompts, completions, totals)):
    pct = p / t * 100
    # Place percentage inside the prompt bar for wide bars, outside for narrow
    if p > 300:
        ax.text(p * 0.5, i, f"{pct:.0f}%", ha="center", va="center",
                fontsize=6.5, color="white", fontweight="bold", zorder=4)
    else:
        ax.text(p * 0.5, i, f"{pct:.0f}%", ha="center", va="center",
                fontsize=5.8, color="white", zorder=4)
    # Total at end of bar
    ax.text(t * 1.04, i, f"{t / 1000:.1f}M", ha="left", va="center",
            fontsize=6.2, color=INK, zorder=4)

ax.set_xscale("log")
ax.set_xlim(50, 18000)
ax.set_xticks([100, 1000, 10000])
ax.set_xticklabels(["100K", "1M", "10M"])
ax.set_xlabel("Tokens (log scale)", fontsize=7.5, color=INK)
ax.set_yticks(y)
ax.set_yticklabels(names, fontsize=6.8, color=INK)
ax.tick_params(labelsize=7, color=EDGE)
ax.invert_yaxis()

ax.grid(True, axis="x", which="major", linestyle="-", linewidth=0.5,
        color="#e2e2e2", zorder=0)
ax.set_axisbelow(True)
for side in ("top", "right"):
    ax.spines[side].set_visible(False)
for side in ("left", "bottom"):
    ax.spines[side].set_color(EDGE)
    ax.spines[side].set_linewidth(0.7)

# Multiplier annotations for the three baselines vs LADDER
ladder_prompt = 147.3
ladder_comp = 43.3
for i, (name, p, c, fam) in enumerate(METHODS):
    if fam == "baseline":
        pm = p / ladder_prompt
        cm = c / ladder_comp
        ax.text(totals[i] * 1.04, i + 0.28,
                f"prompt {pm:.0f}x  compl. {cm:.1f}x",
                ha="left", va="top", fontsize=5.2, color=MUTED, zorder=4)

leg = ax.legend(fontsize=6.5, loc="upper center", bbox_to_anchor=(0.55, 1.12),
                frameon=True, framealpha=0.92, edgecolor="#dcdcdc", ncol=2,
                handlelength=1.2, handletextpad=0.4, borderpad=0.4)
leg.get_frame().set_linewidth(0.6)

fig.tight_layout(pad=0.3, rect=[0, 0, 1, 0.92])
fig.savefig("figures/token_composition.pdf", bbox_inches="tight")
fig.savefig("figures/token_composition.png", dpi=200, bbox_inches="tight")
print("wrote figures/token_composition.pdf + .png")
