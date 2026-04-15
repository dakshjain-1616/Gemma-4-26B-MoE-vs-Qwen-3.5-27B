"""
Generate beautiful dark-theme SVG charts for the Gemma4 vs Qwen3.5 benchmark.
Outputs to outputs/*.svg
"""
import json, math, os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(BASE, "results", "summary.json")
RAW     = os.path.join(BASE, "results", "benchmark_results.json")
OUT     = os.path.join(BASE, "outputs")

# ── Design tokens ─────────────────────────────────────────────────────────────
BG       = "#0D1117"
SURFACE  = "#161B22"
SURFACE2 = "#1C2128"
BORDER   = "#30363D"
GRID     = "#21262D"
TEXT1    = "#E6EDF3"
TEXT2    = "#8B949E"
TEXT3    = "#484F58"
GEMMA    = "#58A6FF"
GEMMA2   = "#1158A6"
QWEN     = "#FF7B54"
QWEN2    = "#A63011"
GREEN    = "#3FB950"
YELLOW   = "#D29922"
FONT     = "system-ui,-apple-system,'Segoe UI',sans-serif"

def fmt_cost(v):
    if v >= 0.01: return f"${v:.4f}"
    if v >= 0.001: return f"${v:.5f}"
    return f"${v:.6f}"

def svg_header(w, h, extra_defs=""):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">
<defs>
  <linearGradient id="gG" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0%" stop-color="{GEMMA}"/>
    <stop offset="100%" stop-color="{GEMMA2}"/>
  </linearGradient>
  <linearGradient id="gQ" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0%" stop-color="{QWEN}"/>
    <stop offset="100%" stop-color="{QWEN2}"/>
  </linearGradient>
  <linearGradient id="bgG" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0%" stop-color="#0D1117"/>
    <stop offset="100%" stop-color="#161B22"/>
  </linearGradient>
  <filter id="shadow" x="-5%" y="-5%" width="110%" height="120%">
    <feDropShadow dx="0" dy="2" stdDeviation="4" flood-color="#000" flood-opacity="0.4"/>
  </filter>
  <filter id="glow">
    <feGaussianBlur stdDeviation="6" result="blur"/>
    <feComposite in="SourceGraphic" in2="blur" operator="over"/>
  </filter>
  {extra_defs}
</defs>
<rect width="{w}" height="{h}" fill="url(#bgG)" rx="12"/>
'''

def svg_footer():
    return '</svg>\n'

def text(x, y, s, anchor="middle", size=13, weight="normal", color=TEXT1, opacity=1.0):
    op = f' opacity="{opacity}"' if opacity != 1.0 else ""
    return f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-family="{FONT}" font-size="{size}" font-weight="{weight}" fill="{color}"{op}>{s}</text>\n'

def rect(x, y, w, h, fill, rx=0, stroke=None, sw=1):
    s = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ""
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" rx="{rx}"{s}/>\n'

def line(x1, y1, x2, y2, color, width=1, dash=""):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{width}"{d}/>\n'

def circle(cx, cy, r, fill, stroke=None, sw=1.5):
    s = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ""
    return f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}"{s}/>\n'

# ── 00: Summary Card ──────────────────────────────────────────────────────────
def make_summary_card(s):
    W, H = 800, 460
    g = s["by_model"]["gemma4_26b_moe"]
    q = s["by_model"]["qwen35_27b"]

    svg = svg_header(W, H)

    # Top accent gradient bar
    svg += f'<defs><linearGradient id="topbar" x1="0" y1="0" x2="1" y2="0"><stop offset="0%" stop-color="{GEMMA}"/><stop offset="50%" stop-color="#8B5CF6"/><stop offset="100%" stop-color="{QWEN}" stop-opacity="0.3"/></linearGradient></defs>\n'
    svg += rect(0, 0, W, 4, "url(#topbar)", rx=2)

    # Title
    svg += text(W//2, 38, "Gemma 4 26B MoE  vs  Qwen 3.5 27B", size=20, weight="700", color=TEXT1)
    svg += text(W//2, 60, "Cost-Quality Benchmark · 15 prompts · 3 categories · OpenRouter · April 2026", size=12, color=TEXT2)

    # Winner badge
    svg += rect(200, 74, 400, 32, "#0D2010", rx=16, stroke=GREEN, sw=1.5)
    svg += text(400, 95, "🏆  Gemma 4 wins on cost · Quality is nearly equal (0.84 vs 0.82)", size=13, weight="600", color=GREEN)

    # 4 stat cards: x positions
    cost_ratio  = round(q['total_cost_usd'] / g['total_cost_usd'], 1)
    lat_ratio   = round(q['avg_latency_s']  / g['avg_latency_s'],  1)
    spd_ratio   = round(g['score_per_dollar'] / q['score_per_dollar'], 0)
    cards = [
        ("QUALITY SCORE", f"{g['avg_score']:.2f}", f"vs {q['avg_score']:.2f} Qwen", f"{g['avg_score']/q['avg_score']:.2f}×", "better score"),
        ("TOTAL RUN COST", f"${g['total_cost_usd']:.4f}", f"vs ${q['total_cost_usd']:.4f} Qwen", f"{cost_ratio:.0f}×", "cheaper per run"),
        ("AVG LATENCY", f"{g['avg_latency_s']:.1f}s", f"vs {q['avg_latency_s']:.1f}s Qwen", f"{lat_ratio:.1f}×", "faster response"),
        ("SCORE PER DOLLAR", f"{g['score_per_dollar']:.0f}", f"vs {q['score_per_dollar']:.1f} Qwen", f"{spd_ratio:.0f}×", "better value"),
    ]

    cw, gap, margin = 172, 12, 22
    for i, (label, val, sub, mult, multlabel) in enumerate(cards):
        cx = margin + i * (cw + gap)
        # Card bg
        svg += rect(cx, 120, cw, 220, SURFACE, rx=10, stroke=BORDER, sw=1)
        # Label
        svg += text(cx + cw//2, 148, label, size=11, weight="600", color=TEXT2)
        # Main value
        svg += text(cx + cw//2, 195, val, size=32, weight="700", color=GEMMA)
        # Sub label
        svg += text(cx + cw//2, 218, sub, size=11, color=TEXT2)
        # Divider
        svg += line(cx+16, 228, cx+cw-16, 228, BORDER)
        # Multiplier
        svg += text(cx + cw//2, 264, mult, size=30, weight="700", color=GREEN)
        svg += text(cx + cw//2, 285, multlabel, size=11, color=TEXT2)
        # Mini score bars for first card only
        if i == 0:
            bx, by, bw, bh = cx+16, 300, cw-32, 8
            svg += rect(bx, by, bw, bh, GRID, rx=4)
            svg += rect(bx, by, int(bw * g['avg_score']), bh, "url(#gG)", rx=4)
            svg += rect(bx, by+14, bw, bh, GRID, rx=4)
            svg += rect(bx, by+14, int(bw * q['avg_score']), bh, "url(#gQ)", rx=4)
            svg += text(bx, by+38, "● Gemma", size=10, anchor="start", color=GEMMA)
            svg += text(cx+cw-16, by+38, "● Qwen", size=10, anchor="end", color=QWEN)

    # Footer note
    svg += line(30, 358, W-30, 358, BORDER, dash="4,4")
    svg += text(W//2, 378, "MoE architecture uses only ~4B active params/token vs 27B dense — same hardware tier, dramatically different economics", size=11, color=TEXT3)
    svg += text(W//2, 400, "Quality gap is narrow (0.84 vs 0.82) · Cost gap is large · Qwen thinking-mode inflates token spend", size=11, color=TEXT3)

    # Legend
    svg += rect(30, 420, 12, 12, GEMMA, rx=2)
    svg += text(48, 431, "google/gemma-4-26b-a4b-it", size=11, anchor="start", color=TEXT2)
    svg += rect(310, 420, 12, 12, QWEN, rx=2)
    svg += text(328, 431, "qwen/qwen3.5-27b", size=11, anchor="start", color=TEXT2)

    svg += svg_footer()
    return svg


# ── 01: Overview (3 grouped bar panels) ───────────────────────────────────────
def make_overview(s):
    W, H = 800, 500
    g = s["by_model"]["gemma4_26b_moe"]
    q = s["by_model"]["qwen35_27b"]

    svg = svg_header(W, H)
    svg += rect(0, 0, W, 4, "url(#topbar)", rx=2) if False else ""
    svg += f'<defs><linearGradient id="topbar2" x1="0" y1="0" x2="1" y2="0"><stop offset="0%" stop-color="{GEMMA}"/><stop offset="100%" stop-color="{QWEN}" stop-opacity="0.5"/></linearGradient></defs>\n'
    svg += rect(0, 0, W, 4, "url(#topbar2)", rx=2)
    svg += text(W//2, 36, "Model Comparison Overview", size=18, weight="700", color=TEXT1)
    svg += text(W//2, 56, "Quality · Cost · Latency — side by side", size=12, color=TEXT2)

    # 3 panels
    panels = [
        {
            "title": "Avg Quality Score",
            "unit": "(0–1 scale)",
            "gval": g["avg_score"],
            "qval": q["avg_score"],
            "max": 1.0,
            "fmt": lambda v: f"{v:.3f}",
        },
        {
            "title": "Total Run Cost",
            "unit": "(USD, 15 prompts)",
            "gval": g["total_cost_usd"],
            "qval": q["total_cost_usd"],
            "max": 0.045,
            "fmt": fmt_cost,
        },
        {
            "title": "Avg Response Latency",
            "unit": "(seconds)",
            "gval": g["avg_latency_s"],
            "qval": q["avg_latency_s"],
            "max": 25.0,
            "fmt": lambda v: f"{v:.2f}s",
        },
    ]

    pw = 220   # panel width
    pgap = 30
    pl = 60    # panel left margin inside chart area
    ch = 300   # chart height (y_bottom - y_top)
    y_top, y_bot = 90, 390
    bw = 60    # bar width

    total_panels = len(panels)
    total_w = total_panels * pw + (total_panels - 1) * pgap
    x_start = (W - total_w) // 2

    for pi, p in enumerate(panels):
        px = x_start + pi * (pw + pgap)  # panel left edge
        cx = px + pw // 2               # panel center

        # Panel title
        svg += text(cx, y_top - 12, p["title"], size=13, weight="600", color=TEXT1)
        svg += text(cx, y_top + 2, p["unit"], size=10, color=TEXT2)

        # Grid lines (3)
        for gi, frac in enumerate([0.25, 0.5, 0.75, 1.0]):
            gy = y_bot - int(ch * frac)
            val = p["max"] * frac
            svg += line(px, gy, px + pw, gy, GRID, dash="2,3")

        # Bottom axis
        svg += line(px, y_bot, px + pw, y_bot, BORDER)

        # Gemma bar
        gh = int((p["gval"] / p["max"]) * ch)
        gx = cx - bw - 8
        svg += rect(gx, y_bot - gh, bw, gh, "url(#gG)", rx=4)
        svg += text(gx + bw//2, y_bot - gh - 8, p["fmt"](p["gval"]), size=11, weight="600", color=GEMMA)

        # Qwen bar
        qh = int((p["qval"] / p["max"]) * ch)
        qx = cx + 8
        svg += rect(qx, y_bot - qh, bw, qh, "url(#gQ)", rx=4)
        svg += text(qx + bw//2, y_bot - qh - 8, p["fmt"](p["qval"]), size=11, weight="600", color=QWEN)

        # X labels
        svg += text(gx + bw//2, y_bot + 18, "Gemma 4", size=10, color=GEMMA)
        svg += text(qx + bw//2, y_bot + 18, "Qwen 3.5", size=10, color=QWEN)

        # Delta badge
        if pi == 0:
            delta = f"{p['gval']/p['qval']:.2f}×"
            color = GREEN
        elif pi == 1:
            delta = f"{p['qval']/p['gval']:.1f}× cheaper →"
            color = GREEN
        else:
            delta = f"{p['qval']/p['gval']:.1f}× slower →"
            color = GREEN
        svg += text(cx, y_bot + 38, f"Gemma: {delta.split('×')[0]}× advantage", size=10, weight="600", color=color)

    # Legend at bottom
    svg += rect(270, H-44, 12, 12, GEMMA, rx=2)
    svg += text(288, H-32, "Gemma 4 26B MoE", size=11, anchor="start", color=TEXT2)
    svg += rect(420, H-44, 12, 12, QWEN, rx=2)
    svg += text(438, H-32, "Qwen 3.5 27B", size=11, anchor="start", color=TEXT2)

    svg += svg_footer()
    return svg


# ── 02: Score per Dollar (efficiency chart) ──────────────────────────────────
def make_efficiency(s):
    W, H = 800, 400
    g = s["by_model"]["gemma4_26b_moe"]
    q = s["by_model"]["qwen35_27b"]
    gspd = g["score_per_dollar"]   # 375.88
    qspd = q["score_per_dollar"]   # 19.68
    ratio = gspd / qspd

    svg = svg_header(W, H)
    svg += f'<defs><linearGradient id="topbar3" x1="0" y1="0" x2="1" y2="0"><stop offset="0%" stop-color="{GEMMA}"/><stop offset="100%" stop-color="{GEMMA}" stop-opacity="0.3"/></linearGradient></defs>\n'
    svg += rect(0, 0, W, 4, "url(#topbar3)", rx=2)
    svg += text(W//2, 36, "Score per Dollar", size=18, weight="700", color=TEXT1)
    svg += text(W//2, 56, "Higher = better value. Quality score achieved per USD spent.", size=12, color=TEXT2)

    y_top, y_bot = 80, 330
    ch = y_bot - y_top  # 250
    max_val = 420.0

    bw = 100
    # Gemma bar
    gx = 180
    gh = int((gspd / max_val) * ch)
    svg += rect(gx, y_bot - gh, bw, gh, "url(#gG)", rx=6)
    svg += text(gx + bw//2, y_bot - gh - 28, f"{gspd:.1f}", size=26, weight="700", color=GEMMA)
    svg += text(gx + bw//2, y_bot - gh - 10, "score / dollar", size=10, color=TEXT2)
    svg += text(gx + bw//2, y_bot + 18, "Gemma 4 26B MoE", size=12, color=GEMMA)

    # Qwen bar
    qx = 500
    qh = int((qspd / max_val) * ch)
    svg += rect(qx, y_bot - qh, bw, qh, "url(#gQ)", rx=6)
    svg += text(qx + bw//2, y_bot - qh - 28, f"{qspd:.1f}", size=26, weight="700", color=QWEN)
    svg += text(qx + bw//2, y_bot - qh - 10, "score / dollar", size=10, color=TEXT2)
    svg += text(qx + bw//2, y_bot + 18, "Qwen 3.5 27B", size=12, color=QWEN)

    # Baseline axis
    svg += line(120, y_bot, W-120, y_bot, BORDER)

    # Grid lines
    for frac in [0.25, 0.5, 0.75, 1.0]:
        gy = y_bot - int(ch * frac)
        gval = max_val * frac
        svg += line(120, gy, W-120, gy, GRID, dash="3,4")
        svg += text(112, gy+4, f"{gval:.0f}", size=9, anchor="end", color=TEXT3)

    # Ratio callout in middle
    mx = (gx + bw + qx) // 2
    svg += text(mx, y_bot - ch//2 - 20, f"{ratio:.0f}×", size=40, weight="700", color=GREEN)
    svg += text(mx, y_bot - ch//2 + 20, "more value", size=13, color=GREEN)
    svg += text(mx, y_bot - ch//2 + 38, "per dollar", size=13, color=GREEN)

    cost_mult = round(q["total_cost_usd"] / g["total_cost_usd"], 1)
    svg += line(30, y_bot + 50, W-30, y_bot + 50, BORDER, dash="2,4")
    svg += text(W//2, y_bot + 68, f"Gemma's MoE design activates only ~4B params/token → {cost_mult:.0f}× lower total cost → {ratio:.0f}× better value", size=11, color=TEXT3)

    svg += svg_footer()
    return svg


# ── 03: By Category ───────────────────────────────────────────────────────────
def make_by_category(s):
    W, H = 800, 480
    cats = s["by_category"]
    cat_keys = ["coding", "reasoning", "instruction_following"]
    cat_labels = ["Coding", "Reasoning", "Instruction\nFollowing"]

    svg = svg_header(W, H)
    svg += f'<defs><linearGradient id="topbar4" x1="0" y1="0" x2="1" y2="0"><stop offset="0%" stop-color="{GEMMA}"/><stop offset="50%" stop-color="#8B5CF6"/><stop offset="100%" stop-color="{QWEN}"/></linearGradient></defs>\n'
    svg += rect(0, 0, W, 4, "url(#topbar4)", rx=2)
    svg += text(W//2, 36, "Performance by Category", size=18, weight="700", color=TEXT1)
    svg += text(W//2, 56, "Avg quality score per task type", size=12, color=TEXT2)

    # Two rows: Score row and Cost row
    # Score bars: y_top=80, y_bot=280
    # Cost bars: y_top=300, y_bot=420

    y_top1, y_bot1 = 80, 290
    ch1 = y_bot1 - y_top1   # 210
    bw = 70
    pgap = 80

    n = len(cat_keys)
    total_bw = n * (2*bw + pgap) - pgap
    x_start = (W - total_bw) // 2

    # Score section label
    svg += text(28, 190, "Score", size=11, anchor="start", color=TEXT2, weight="600")
    svg += line(20, y_top1, 20, y_bot1, TEXT3)
    for gi in range(5):
        frac = gi / 4
        gy = y_bot1 - int(ch1 * frac)
        svg += line(30, gy, W-20, gy, GRID, dash="2,3")
        svg += text(12, gy+4, f"{frac:.2f}", size=8, anchor="end", color=TEXT3)

    svg += line(20, y_bot1, W-20, y_bot1, BORDER)

    for ci, (ck, cl) in enumerate(zip(cat_keys, cat_labels)):
        cx_center = x_start + ci * (2*bw + pgap) + bw
        gv = cats[ck]["gemma4_26b_moe"]["avg_score"]
        qv = cats[ck]["qwen35_27b"]["avg_score"]

        # Gemma bar
        gh = int((gv / 1.0) * ch1)
        gx = cx_center - bw - 4
        svg += rect(gx, y_bot1 - gh, bw, gh, "url(#gG)", rx=4)
        svg += text(gx + bw//2, y_bot1 - gh - 6, f"{gv:.2f}", size=10, weight="600", color=GEMMA)

        # Qwen bar
        qh = int((qv / 1.0) * ch1)
        qx = cx_center + 4
        svg += rect(qx, y_bot1 - qh, bw, qh, "url(#gQ)", rx=4)
        svg += text(qx + bw//2, y_bot1 - qh - 6, f"{qv:.2f}", size=10, weight="600", color=QWEN)

        # Category label (handle multiline)
        label_y = y_bot1 + 18
        for line_text in cl.split("\n"):
            svg += text(cx_center + bw//2 - bw//2 + bw//2 - 4, label_y, line_text, size=12, weight="600", color=TEXT1)
            label_y += 16

    # Cost comparison section
    y_top2, y_bot2 = 340, 430
    ch2 = y_bot2 - y_top2  # 90

    svg += text(W//2, y_top2 - 12, "Cost per Category (USD, 5 prompts each)", size=12, weight="600", color=TEXT2)
    svg += line(20, y_bot2, W-20, y_bot2, BORDER)

    max_cost = 0.022  # approximate max Qwen instruction cost
    svg += line(20, y_top2, 20, y_bot2, TEXT3)
    for gi in range(3):
        frac = gi / 2
        gy = y_bot2 - int(ch2 * frac)
        svg += line(20, gy, W-20, gy, GRID, dash="2,3")
        svg += text(12, gy+4, f"${max_cost*frac:.4f}", size=7, anchor="end", color=TEXT3)

    for ci, ck in enumerate(cat_keys):
        cx_center = x_start + ci * (2*bw + pgap) + bw
        gv = cats[ck]["gemma4_26b_moe"]["total_cost_usd"]
        qv = cats[ck]["qwen35_27b"]["total_cost_usd"]

        gh = max(2, int((gv / max_cost) * ch2))
        gx = cx_center - bw - 4
        svg += rect(gx, y_bot2 - gh, bw, gh, "url(#gG)", rx=3)
        lbl = fmt_cost(gv)
        svg += text(gx + bw//2, y_bot2 - gh - 4, lbl, size=8, color=GEMMA)

        qh = max(2, int((qv / max_cost) * ch2))
        qx = cx_center + 4
        svg += rect(qx, y_bot2 - qh, bw, qh, "url(#gQ)", rx=3)
        lbl2 = fmt_cost(qv)
        svg += text(qx + bw//2, y_bot2 - qh - 4, lbl2, size=8, color=QWEN)

    # Legend
    svg += rect(278, H-32, 10, 10, GEMMA, rx=2)
    svg += text(294, H-22, "Gemma 4 26B MoE", size=11, anchor="start", color=TEXT2)
    svg += rect(420, H-32, 10, 10, QWEN, rx=2)
    svg += text(436, H-22, "Qwen 3.5 27B", size=11, anchor="start", color=TEXT2)

    svg += svg_footer()
    return svg


# ── 04: Latency ───────────────────────────────────────────────────────────────
def make_latency(raw):
    W, H = 800, 440
    # Get per-prompt latencies
    gdata = [(r["prompt_idx"], r["category"], r["latency_s"]) for r in raw if r["model_key"] == "gemma4_26b_moe"]
    qdata = [(r["prompt_idx"], r["category"], r["latency_s"]) for r in raw if r["model_key"] == "qwen35_27b"]

    cat_colors = {"coding": "#4FC3F7", "reasoning": "#C792EA", "instruction_following": "#A5D6A7"}
    cat_labels = {"coding": "Coding", "reasoning": "Reasoning", "instruction_following": "Instruction"}

    svg = svg_header(W, H)
    svg += f'<defs><linearGradient id="topbar5" x1="0" y1="0" x2="1" y2="0"><stop offset="0%" stop-color="{GEMMA}"/><stop offset="100%" stop-color="#8B5CF6"/></linearGradient></defs>\n'
    svg += rect(0, 0, W, 4, "url(#topbar5)", rx=2)
    svg += text(W//2, 34, "Response Latency per Prompt", size=18, weight="700", color=TEXT1)
    svg += text(W//2, 54, "Lower = faster. Each bar = one prompt call. Grouped by model.", size=12, color=TEXT2)

    # Two horizontal sections: Gemma top, Qwen bottom
    # Gemma: y_top=70, y_bot=200; Qwen: y_top=230, y_bot=360
    n = 15
    bar_w = 34
    gap = 6
    x_start = 70
    total_bars_w = n * (bar_w + gap) - gap
    # Center in chart area (70..730)
    x0 = x_start

    sections = [
        ("Gemma 4 26B MoE", gdata, 70, 190, GEMMA, "url(#gG)"),
        ("Qwen 3.5 27B", qdata, 230, 360, QWEN, "url(#gQ)"),
    ]

    max_lat = 85.0  # Qwen 12-balls reasoning hit ~76s

    for (label, data, y_top, y_bot, color, fill) in sections:
        ch = y_bot - y_top

        # Section label
        svg += text(x0, y_top - 6, label, size=12, weight="600", anchor="start", color=color)
        svg += line(x0, y_bot, x0 + n*(bar_w+gap), y_bot, BORDER)

        # Grid lines
        for frac in [0.25, 0.5, 0.75, 1.0]:
            gy = y_bot - int(ch * frac)
            lat = max_lat * frac
            svg += line(x0, gy, x0 + n*(bar_w+gap), gy, GRID, dash="2,3")
            svg += text(x0 - 5, gy+4, f"{lat:.0f}s", size=8, anchor="end", color=TEXT3)

        cats = ["coding", "reasoning", "instruction_following"]
        for bi, (pidx, cat, lat) in enumerate(data):
            bx = x0 + bi * (bar_w + gap)
            bh = max(2, int((lat / max_lat) * ch))
            cat_color = cat_colors[cat]
            # Create gradient per category
            gid = f"grad_{label[:1]}_{cat[:3]}"
            svg += f'<defs><linearGradient id="{gid}" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="{cat_color}"/><stop offset="100%" stop-color="{cat_color}" stop-opacity="0.5"/></linearGradient></defs>\n'
            svg += rect(bx, y_bot - bh, bar_w, bh, f"url(#{gid})", rx=3)
            if lat > 0:
                svg += text(bx + bar_w//2, y_bot - bh - 4, f"{lat:.1f}", size=7, color=TEXT2)

        # Category dividers
        svg += line(x0 + 5*(bar_w+gap), y_top, x0 + 5*(bar_w+gap), y_bot, BORDER, dash="4,3")
        svg += line(x0 + 10*(bar_w+gap), y_top, x0 + 10*(bar_w+gap), y_bot, BORDER, dash="4,3")
        svg += text(x0 + 2.5*(bar_w+gap), y_top + 12, "Coding", size=9, color=TEXT3)
        svg += text(x0 + 7.5*(bar_w+gap), y_top + 12, "Reasoning", size=9, color=TEXT3)
        svg += text(x0 + 12.5*(bar_w+gap), y_top + 12, "Instruction", size=9, color=TEXT3)

    # Legend
    for ck, cv in cat_colors.items():
        pass  # skip per-category legend for simplicity
    svg += rect(230, H-30, 10, 10, GEMMA, rx=2)
    svg += text(246, H-20, "Gemma 4 26B MoE", size=11, anchor="start", color=TEXT2)
    svg += rect(390, H-30, 10, 10, QWEN, rx=2)
    svg += text(406, H-20, "Qwen 3.5 27B", size=11, anchor="start", color=TEXT2)

    svg += text(W//2, H-8, "Qwen 12-balls reasoning prompt took 76s · Qwen thinking mode generates many internal tokens before answering", size=10, color=TEXT3)

    svg += svg_footer()
    return svg


# ── 05: Scatter Quality vs Cost ───────────────────────────────────────────────
def make_scatter(raw):
    W, H = 800, 500
    gdata = [r for r in raw if r["model_key"] == "gemma4_26b_moe"]
    qdata = [r for r in raw if r["model_key"] == "qwen35_27b"]

    svg = svg_header(W, H)
    svg += f'<defs><linearGradient id="topbar6" x1="0" y1="0" x2="1" y2="0"><stop offset="0%" stop-color="{GEMMA}"/><stop offset="50%" stop-color="#8B5CF6"/><stop offset="100%" stop-color="{QWEN}"/></linearGradient></defs>\n'
    svg += rect(0, 0, W, 4, "url(#topbar6)", rx=2)
    svg += text(W//2, 34, "Quality vs Cost per Prompt", size=18, weight="700", color=TEXT1)
    svg += text(W//2, 54, "Each dot = one API call. Top-left corner = best (high quality, low cost).", size=12, color=TEXT2)

    # Chart area
    xl, xr, yt, yb = 80, 740, 70, 420
    cw = xr - xl
    ch = yb - yt

    max_cost = 0.012   # x axis max (just above max Qwen cost per call)
    max_score = 1.0    # y axis max

    # Grid
    for xi in range(6):
        gx = xl + int(cw * xi / 5)
        cost_val = max_cost * xi / 5
        svg += line(gx, yt, gx, yb, GRID, dash="2,3")
        svg += text(gx, yb+15, f"${cost_val:.4f}", size=9, color=TEXT3)

    for yi in range(6):
        gy = yt + int(ch * yi / 5)
        score_val = max_score * (1 - yi/5)
        svg += line(xl, gy, xr, gy, GRID, dash="2,3")
        svg += text(xl-5, gy+4, f"{score_val:.2f}", size=9, anchor="end", color=TEXT3)

    # Axes
    svg += line(xl, yb, xr, yb, BORDER)
    svg += line(xl, yt, xl, yb, BORDER)

    # Axis labels
    svg += text(W//2, yb+32, "Cost per Call (USD)", size=11, color=TEXT2)
    svg += f'<text x="20" y="{(yt+yb)//2}" text-anchor="middle" font-family="{FONT}" font-size="11" fill="{TEXT2}" transform="rotate(-90,20,{(yt+yb)//2})">Quality Score</text>\n'

    cat_shapes = {"coding": "●", "reasoning": "■", "instruction_following": "▲"}

    # "Best value" corner label
    svg += text(xl+8, yt+14, "← Best value zone", size=9, anchor="start", color=GREEN, opacity=0.6)

    # Qwen dots
    for r in qdata:
        cost = r["cost_usd"]
        score = r["score"]
        xi = xl + int((cost / max_cost) * cw)
        yi2 = yb - int((score / max_score) * ch)
        xi = max(xl+3, min(xr-3, xi))
        yi2 = max(yt+3, min(yb-3, yi2))
        svg += circle(xi, yi2, 7, QWEN, stroke=SURFACE, sw=1.5)

    # Gemma dots (on top)
    for r in gdata:
        cost = r["cost_usd"]
        score = r["score"]
        xi = xl + int((cost / max_cost) * cw)
        yi2 = yb - int((score / max_score) * ch)
        xi = max(xl+3, min(xr-3, xi))
        yi2 = max(yt+3, min(yb-3, yi2))
        svg += circle(xi, yi2, 7, GEMMA, stroke=SURFACE, sw=1.5)

    # Cluster annotation for Gemma
    # Most Gemma dots cluster around x≈0-0.00025 (xl to xl+15), score=0.6-1.0
    ann_x = xl + int((0.00025/max_cost)*cw) + 20
    ann_y = yb - int((0.9/max_score)*ch)
    svg += f'<line x1="{ann_x-15}" y1="{ann_y+5}" x2="{ann_x-60}" y2="{ann_y+30}" stroke="{GEMMA}" stroke-width="1" stroke-dasharray="2,2" opacity="0.6"/>\n'
    svg += rect(ann_x-75, ann_y+28, 140, 26, SURFACE2, rx=4, stroke=GEMMA, sw=1)
    svg += text(ann_x-5, ann_y+43, "Gemma cluster (cheap+fast)", size=9, color=GEMMA)

    # Qwen outlier annotation (12-balls reasoning: most expensive call)
    out_x = xl + int((0.01034/max_cost)*cw)
    out_y = yb - int((0.67/max_score)*ch)
    svg += rect(out_x-90, out_y-34, 180, 22, SURFACE2, rx=4, stroke=QWEN, sw=1)
    svg += text(out_x, out_y-20, "Qwen 12-balls: $0.01034, 76s", size=9, color=QWEN)

    # Legend
    svg += circle(290, H-24, 7, GEMMA, stroke=SURFACE, sw=1.5)
    svg += text(303, H-19, "Gemma 4 26B MoE (15 calls)", size=11, anchor="start", color=TEXT2)
    svg += circle(490, H-24, 7, QWEN, stroke=SURFACE, sw=1.5)
    svg += text(503, H-19, "Qwen 3.5 27B (15 calls, 0 failures)", size=11, anchor="start", color=TEXT2)

    svg += svg_footer()
    return svg


# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    with open(RESULTS) as f:
        summary = json.load(f)
    with open(RAW) as f:
        raw = json.load(f)

    os.makedirs(OUT, exist_ok=True)

    charts = [
        ("00_summary_card.svg",        make_summary_card(summary)),
        ("01_overview.svg",            make_overview(summary)),
        ("02_efficiency.svg",          make_efficiency(summary)),
        ("03_by_category.svg",         make_by_category(summary)),
        ("04_latency.svg",             make_latency(raw)),
        ("05_scatter_quality_cost.svg",make_scatter(raw)),
    ]

    for fname, svg_content in charts:
        path = os.path.join(OUT, fname)
        with open(path, "w") as f:
            f.write(svg_content)
        print(f"  ✓ {fname}")

    print(f"\nAll {len(charts)} SVGs written to outputs/")
