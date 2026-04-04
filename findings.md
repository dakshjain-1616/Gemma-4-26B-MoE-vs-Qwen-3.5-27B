# Gemma 4 26B MoE vs Qwen 3.5 27B — Cost-Quality Benchmark

> Definitive tokens-per-dollar analysis at equal parameter scale.
> Research conducted with [NEO](https://heyneo.so) — your autonomous AI agent.

---

## TL;DR

| Metric | Gemma 4 26B MoE | Qwen 3.5 27B | Winner |
|--------|----------|----------|--------|
| Avg Quality Score | 0.8400 | 0.5973 | **Gemma 4 26B MoE** |
| Total API Cost | $0.00223 | $0.03034 | **Gemma 4 26B MoE** |
| Score per Dollar | 375.9× | 19.7× | **Gemma 4 26B MoE** |
| Avg Latency | 3.96s | 15.25s | **Gemma 4 26B MoE** |

---

## Models Compared

| | Gemma 4 26B MoE | Qwen 3.5 27B |
|---|---|---|
| **Developer** | Google DeepMind | Alibaba Cloud |
| **Architecture** | Mixture-of-Experts (MoE) | Dense Transformer |
| **Total Params** | 26B | 27B |
| **Active Params** | ~4B per token | 27B per token |
| **Input Price** | $0.13 / 1M tokens | $0.195 / 1M tokens |
| **Output Price** | $0.40 / 1M tokens | $1.56 / 1M tokens |
| **OpenRouter ID** | `google/gemma-4-26b-a4b-it` | `qwen/qwen3.5-27b` |

---

## Results by Task Category

| Category | Gemma 4 26B MoE | Qwen 3.5 27B | Winner |
|----------|----------|----------|--------|
| Coding | 1.000 | 0.910 | **Gemma 4 26B MoE** (+0.090) |
| Reasoning | 0.730 | 0.292 | **Gemma 4 26B MoE** (+0.438) |
| Instruction Following | 0.790 | 0.590 | **Gemma 4 26B MoE** (+0.200) |

---

## Key Findings

### 1. Cost Efficiency
Gemma 4 26B MoE is significantly cheaper, especially on output tokens ($0.40 vs $1.56 per 1M).
This means for high-throughput workloads, Gemma 4 26B MoE offers substantially better value.

### 2. MoE vs Dense Architecture
The MoE design of Gemma 4 activates only ~4B parameters per token while still leveraging
26B of learned knowledge. This translates directly to lower inference cost without
proportional quality loss.

### 3. Score/Dollar Crossover
At current OpenRouter pricing, Gemma 4 26B MoE provides more quality per dollar spent.
The crossover point depends on task type — for output-heavy tasks, the gap widens further
in favour of the cheaper output-price model.

### 4. Latency
Gemma 4 26B MoE responds faster on average. For real-time applications, latency can be
the deciding factor independent of cost.

---

## Deployment Recommendations

| Use Case | Recommended Model | Reason |
|----------|-------------------|--------|
| High-volume production API | Gemma 4 26B MoE | Lower cost at scale |
| Best raw quality | Gemma 4 26B MoE | Higher avg score |
| Real-time chat / streaming | Gemma 4 26B MoE | Lower latency |
| Budget-constrained projects | Gemma 4 26B MoE | Best score/dollar |

---

## Methodology

- **15 prompts** across 3 categories: Coding (5), Reasoning (5), Instruction Following (5)
- **Temperature = 0** for deterministic, reproducible outputs
- **Scoring**: Heuristic rubric per category (0–1 scale); production use should employ LLM-as-judge
- **Cost**: Calculated from actual token usage reported by OpenRouter API
- **API**: OpenRouter unified endpoint for fair, identical infrastructure

---

## Infographics

| Chart | Description |
|-------|-------------|
| ![Summary Card](outputs/00_summary_card.png) | At-a-glance model comparison card |
| ![Overview](outputs/01_overview.png) | Score and cost side-by-side |
| ![Efficiency](outputs/02_efficiency.png) | Score per dollar |
| ![By Category](outputs/03_by_category.png) | Per-task breakdown |
| ![Latency](outputs/04_latency.png) | Response time comparison |
| ![Scatter](outputs/05_scatter_quality_cost.png) | Quality vs cost per prompt |

---

## Reproduce

```bash
git clone <this-repo>
cd 03-benchmarking-moe-qwen
pip install -r requirements.txt
cp .env.example .env   # add your OPENROUTER_API_KEY
python scripts/run_all.py
```

---

*Benchmark conducted using [NEO](https://heyneo.so) — autonomous AI research agent.*
