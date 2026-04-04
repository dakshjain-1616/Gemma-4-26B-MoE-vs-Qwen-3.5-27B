#!/usr/bin/env python3
"""
Generate infographic-quality charts from benchmark results.
Outputs PNG charts to outputs/
"""

import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from pathlib import Path

ROOT    = Path(__file__).parent.parent
RESULTS = ROOT / "results" / "summary.json"
OUTDIR  = ROOT / "outputs"
OUTDIR.mkdir(exist_ok=True)

# ── Palette ────────────────────────────────────────────────────────────────
GEMMA_COLOR = "#4285F4"   # Google blue
QWEN_COLOR  = "#7B2FBE"   # Qwen purple
BG          = "#0F1117"
CARD        = "#1A1D27"
TEXT        = "#E8EAED"
GRID        = "#2A2D3A"
ACCENT      = "#00D4AA"

MODEL_LABELS = {
    "gemma4_26b_moe": "Gemma 4\n26B MoE",
    "qwen35_27b":     "Qwen 3.5\n27B Dense",
}
MODEL_COLORS = {
    "gemma4_26b_moe": GEMMA_COLOR,
    "qwen35_27b":     QWEN_COLOR,
}

def load_summary():
    with open(RESULTS) as f:
        return json.load(f)

def style_ax(ax, title=""):
    ax.set_facecolor(CARD)
    ax.tick_params(colors=TEXT, labelsize=10)
    ax.xaxis.label.set_color(TEXT)
    ax.yaxis.label.set_color(TEXT)
    for spine in ax.spines.values():
        spine.set_edgecolor(GRID)
    ax.grid(axis="y", color=GRID, linewidth=0.8, linestyle="--", alpha=0.7)
    if title:
        ax.set_title(title, color=TEXT, fontsize=13, fontweight="bold", pad=12)

# ── Chart 1: Overall Score + Cost side-by-side bars ───────────────────────
def chart_overview(summary):
    models = list(summary["by_model"].keys())
    scores = [summary["by_model"][m]["avg_score"]      for m in models]
    costs  = [summary["by_model"][m]["total_cost_usd"] for m in models]
    labels = [MODEL_LABELS[m] for m in models]
    colors = [MODEL_COLORS[m] for m in models]

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    fig.patch.set_facecolor(BG)

    # Score bar
    ax = axes[0]
    style_ax(ax, "Average Quality Score")
    bars = ax.bar(labels, scores, color=colors, width=0.4, zorder=3, edgecolor="none")
    ax.set_ylim(0, 1.0)
    ax.set_ylabel("Score (0–1)", color=TEXT)
    for bar, val in zip(bars, scores):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
                f"{val:.3f}", ha="center", va="bottom", color=TEXT, fontsize=12, fontweight="bold")

    # Cost bar
    ax = axes[1]
    style_ax(ax, "Total API Cost (USD)")
    bars = ax.bar(labels, costs, color=colors, width=0.4, zorder=3, edgecolor="none")
    ax.set_ylabel("Cost (USD)", color=TEXT)
    for bar, val in zip(bars, costs):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(costs)*0.01,
                f"${val:.5f}", ha="center", va="bottom", color=TEXT, fontsize=11, fontweight="bold")

    fig.suptitle("Gemma 4 26B MoE  vs  Qwen 3.5 27B — Overview", color=TEXT,
                 fontsize=15, fontweight="bold", y=1.02)
    plt.tight_layout()
    path = OUTDIR / "01_overview.png"
    plt.savefig(path, dpi=150, bbox_inches="tight", facecolor=BG)
    plt.close()
    print(f"  Saved {path.name}")

# ── Chart 2: Score per Dollar (efficiency) ────────────────────────────────
def chart_efficiency(summary):
    models  = list(summary["by_model"].keys())
    spd     = [summary["by_model"][m]["score_per_dollar"] for m in models]
    labels  = [MODEL_LABELS[m] for m in models]
    colors  = [MODEL_COLORS[m] for m in models]

    fig, ax = plt.subplots(figsize=(8, 5))
    fig.patch.set_facecolor(BG)
    style_ax(ax, "Score per Dollar  (higher = better value)")
    bars = ax.bar(labels, spd, color=colors, width=0.35, zorder=3, edgecolor="none")
    ax.set_ylabel("Score / USD", color=TEXT)
    for bar, val in zip(bars, spd):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(spd)*0.01,
                f"{val:.1f}×", ha="center", va="bottom", color=ACCENT,
                fontsize=14, fontweight="bold")
    plt.tight_layout()
    path = OUTDIR / "02_efficiency.png"
    plt.savefig(path, dpi=150, bbox_inches="tight", facecolor=BG)
    plt.close()
    print(f"  Saved {path.name}")

# ── Chart 3: Per-category grouped bar chart ───────────────────────────────
def chart_by_category(summary):
    categories = list(summary["by_category"].keys())
    models     = list(summary["by_model"].keys())
    x          = np.arange(len(categories))
    width      = 0.35

    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor(BG)
    style_ax(ax, "Quality Score by Task Category")

    for i, m in enumerate(models):
        vals = [summary["by_category"][cat].get(m, {}).get("avg_score", 0) for cat in categories]
        offset = (i - 0.5) * width
        bars = ax.bar(x + offset, vals, width, label=MODEL_LABELS[m],
                      color=MODEL_COLORS[m], zorder=3, edgecolor="none")
        for bar, val in zip(bars, vals):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                    f"{val:.2f}", ha="center", va="bottom", color=TEXT, fontsize=9)

    ax.set_xticks(x)
    ax.set_xticklabels([c.replace("_", "\n").title() for c in categories], color=TEXT)
    ax.set_ylim(0, 1.1)
    ax.set_ylabel("Avg Score", color=TEXT)
    legend = ax.legend(facecolor=CARD, edgecolor=GRID, labelcolor=TEXT, fontsize=10)
    plt.tight_layout()
    path = OUTDIR / "03_by_category.png"
    plt.savefig(path, dpi=150, bbox_inches="tight", facecolor=BG)
    plt.close()
    print(f"  Saved {path.name}")

# ── Chart 4: Latency comparison ───────────────────────────────────────────
def chart_latency(summary):
    models  = list(summary["by_model"].keys())
    lats    = [summary["by_model"][m]["avg_latency_s"] for m in models]
    labels  = [MODEL_LABELS[m] for m in models]
    colors  = [MODEL_COLORS[m] for m in models]

    fig, ax = plt.subplots(figsize=(8, 5))
    fig.patch.set_facecolor(BG)
    style_ax(ax, "Average Response Latency (seconds)")
    bars = ax.bar(labels, lats, color=colors, width=0.35, zorder=3, edgecolor="none")
    ax.set_ylabel("Latency (s)", color=TEXT)
    for bar, val in zip(bars, lats):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(lats)*0.01,
                f"{val:.2f}s", ha="center", va="bottom", color=TEXT,
                fontsize=12, fontweight="bold")
    plt.tight_layout()
    path = OUTDIR / "04_latency.png"
    plt.savefig(path, dpi=150, bbox_inches="tight", facecolor=BG)
    plt.close()
    print(f"  Saved {path.name}")

# ── Chart 5: Scatter — Quality vs Cost per prompt ─────────────────────────
def chart_scatter(summary):
    # Load raw results for per-prompt scatter
    raw_path = ROOT / "results" / "benchmark_results.json"
    if not raw_path.exists():
        print("  Skipping scatter (no raw results)")
        return
    with open(raw_path) as f:
        raw = json.load(f)

    fig, ax = plt.subplots(figsize=(10, 6))
    fig.patch.set_facecolor(BG)
    style_ax(ax, "Quality vs Cost — Every Prompt")

    for m in ["gemma4_26b_moe", "qwen35_27b"]:
        pts = [(r["cost_usd"], r["score"]) for r in raw if r["model_key"] == m and r.get("score", 0) > 0]
        if pts:
            xs, ys = zip(*pts)
            ax.scatter(xs, ys, color=MODEL_COLORS[m], label=MODEL_LABELS[m].replace("\n", " "),
                       alpha=0.75, s=70, edgecolors="none", zorder=4)

    ax.set_xlabel("Cost per Prompt (USD)", color=TEXT)
    ax.set_ylabel("Quality Score", color=TEXT)
    ax.set_ylim(0, 1.1)
    legend = ax.legend(facecolor=CARD, edgecolor=GRID, labelcolor=TEXT, fontsize=10)
    plt.tight_layout()
    path = OUTDIR / "05_scatter_quality_cost.png"
    plt.savefig(path, dpi=150, bbox_inches="tight", facecolor=BG)
    plt.close()
    print(f"  Saved {path.name}")

# ── Chart 6: Summary infographic card ─────────────────────────────────────
def chart_summary_card(summary):
    fig, ax = plt.subplots(figsize=(12, 4))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    ax.axis("off")

    models = list(summary["by_model"].keys())
    col_x  = [0.25, 0.75]

    for xi, m in zip(col_x, models):
        info  = summary.get("model_info", {}).get(m, {})
        stats = summary["by_model"][m]
        color = MODEL_COLORS[m]

        # Card background
        fancy = mpatches.FancyBboxPatch((xi - 0.22, 0.05), 0.44, 0.90,
            boxstyle="round,pad=0.02", linewidth=2,
            edgecolor=color, facecolor=CARD, transform=ax.transAxes, zorder=1)
        ax.add_patch(fancy)

        label = info.get("name", m)
        params = info.get("params", "")
        ax.text(xi, 0.88, label, ha="center", va="center", color=color,
                fontsize=16, fontweight="bold", transform=ax.transAxes)
        ax.text(xi, 0.78, params, ha="center", va="center", color=TEXT,
                fontsize=11, transform=ax.transAxes, alpha=0.8)

        metrics = [
            ("Avg Score",    f"{stats['avg_score']:.3f}"),
            ("Total Cost",   f"${stats['total_cost_usd']:.5f}"),
            ("Latency",      f"{stats['avg_latency_s']}s"),
            ("Score/Dollar", f"{stats['score_per_dollar']:.1f}×"),
        ]
        for j, (label_m, val) in enumerate(metrics):
            y = 0.62 - j * 0.14
            ax.text(xi - 0.10, y, label_m, ha="left", va="center", color=TEXT,
                    fontsize=10, transform=ax.transAxes, alpha=0.7)
            ax.text(xi + 0.18, y, val, ha="right", va="center", color=ACCENT,
                    fontsize=11, fontweight="bold", transform=ax.transAxes)

    ax.text(0.5, 0.98, "Gemma 4 26B MoE  vs  Qwen 3.5 27B — Summary Card",
            ha="center", va="top", color=TEXT, fontsize=14,
            fontweight="bold", transform=ax.transAxes)
    ax.text(0.5, 0.01, "Benchmark by NEO · heyneo.so", ha="center", va="bottom",
            color=ACCENT, fontsize=9, transform=ax.transAxes, alpha=0.8)

    plt.tight_layout()
    path = OUTDIR / "00_summary_card.png"
    plt.savefig(path, dpi=150, bbox_inches="tight", facecolor=BG)
    plt.close()
    print(f"  Saved {path.name}")

if __name__ == "__main__":
    print("Generating charts...")
    summary = load_summary()
    chart_summary_card(summary)
    chart_overview(summary)
    chart_efficiency(summary)
    chart_by_category(summary)
    chart_latency(summary)
    chart_scatter(summary)
    print(f"\nAll charts saved to {OUTDIR}/")
