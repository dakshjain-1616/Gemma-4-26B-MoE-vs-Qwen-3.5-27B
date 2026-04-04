#!/usr/bin/env python3
"""
MoE Cost-Quality Benchmark: Gemma 4 26B MoE vs Qwen 3.5 27B
Runs identical prompts via OpenRouter API, tracks quality scores + cost.
"""

import os
import json
import time
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
BASE_URL = "https://openrouter.ai/api/v1/chat/completions"

MODELS = {
    "gemma4_26b_moe": "google/gemma-4-26b-a4b-it",   # 26B total, 4B active (MoE)
    "qwen35_27b":     "qwen/qwen3.5-27b",              # 27B dense
}

MODEL_INFO = {
    "gemma4_26b_moe": {"name": "Gemma 4 26B MoE", "params": "26B (4B active)", "arch": "MoE"},
    "qwen35_27b":     {"name": "Qwen 3.5 27B",    "params": "27B dense",       "arch": "Dense"},
}

# Pricing per 1M tokens (USD) — from OpenRouter
PRICING = {
    "gemma4_26b_moe": {"input": 0.13,  "output": 0.40},
    "qwen35_27b":     {"input": 0.195, "output": 1.56},
}

TASK_PROMPTS = {
    "coding": [
        "Write a Python function to find all prime numbers up to N using the Sieve of Eratosthenes. Include type hints and docstring.",
        "Implement a thread-safe LRU cache in Python with get/put operations in O(1) time.",
        "Write a Python decorator that retries a function up to 3 times on exception with exponential backoff and jitter.",
        "Implement merge sort in Python and analyze its time and space complexity in comments.",
        "Write a Python context manager that times code blocks and logs execution duration.",
    ],
    "reasoning": [
        "A bat and ball cost $1.10. The bat costs $1 more than the ball. How much does the ball cost? Show every step.",
        "If all Bloops are Razzles, and all Razzles are Lazzles, are all Bloops definitely Lazzles? Use formal logic.",
        "A snail climbs 3 feet up a 10-foot wall each day but slides back 2 feet each night. How many days to reach the top?",
        "You have 12 balls, one is heavier. Using a balance scale exactly 3 times, how do you find the heavy ball?",
        "Alice is twice as old as Bob was when Alice was as old as Bob is now. Bob is 24. How old is Alice?",
    ],
    "instruction_following": [
        "List exactly 5 European capitals in alphabetical order. One per line, no extra text, no numbering.",
        "Translate 'The early bird catches the worm' into French, Spanish, German, and Japanese. Format: Language: Translation",
        "Write a haiku about artificial intelligence. Strict 5-7-5 syllable count. Title it 'Silicon Mind'.",
        "Give me 3 synonyms each for: happy, sad, fast. Respond only with valid JSON: {\"word\": [\"syn1\",\"syn2\",\"syn3\"]}",
        "Summarize the theory of evolution in exactly 3 sentences. No more, no less.",
    ],
}

def call_openrouter(model_id: str, prompt: str) -> dict:
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://heyneo.so",
        "X-Title": "NEO MoE Benchmark",
    }
    payload = {
        "model": model_id,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 600,
        "temperature": 0.0,
    }
    t0 = time.time()
    resp = requests.post(BASE_URL, headers=headers, json=payload, timeout=60)
    latency = time.time() - t0
    resp.raise_for_status()
    data = resp.json()
    usage = data.get("usage", {})
    return {
        "response": data["choices"][0]["message"]["content"],
        "input_tokens":  usage.get("prompt_tokens", 0),
        "output_tokens": usage.get("completion_tokens", 0),
        "latency_s":     round(latency, 3),
    }

def score_response(prompt: str, response: str, category: str) -> float:
    if not response:
        return 0.0
    score = 0.40
    text = response.strip()
    if len(text) > 80:
        score += 0.15
    if category == "coding":
        if "def " in text or "class " in text:
            score += 0.20
        if '"""' in text or "'''" in text or "#" in text:
            score += 0.10
        if "return" in text:
            score += 0.10
        if ":" in text and "\n" in text:
            score += 0.05
    elif category == "reasoning":
        keywords = ["therefore", "because", "since", "thus", "step", "so ", "hence",
                    "conclude", "equals", "=", "result", "answer"]
        hits = sum(1 for w in keywords if w in text.lower())
        score += min(hits * 0.06, 0.35)
    elif category == "instruction_following":
        if len(text) < 700:
            score += 0.15
        if "\n" in text:
            score += 0.10
        if any(c in text for c in [":", "-", "•", "{"]):
            score += 0.10
    return min(round(score, 3), 1.0)

def compute_cost(model_key: str, input_tokens: int, output_tokens: int) -> float:
    p = PRICING[model_key]
    return round((input_tokens * p["input"] + output_tokens * p["output"]) / 1_000_000, 8)

def generate_summary(results: list) -> dict:
    summary = {"by_model": {}, "by_category": {}, "model_info": MODEL_INFO}
    for category in TASK_PROMPTS.keys():
        summary["by_category"][category] = {}

    for r in results:
        m   = r["model_key"]
        cat = r["category"]
        if m not in summary["by_model"]:
            summary["by_model"][m] = {"scores": [], "costs": [], "latencies": [], "tokens_out": []}
        summary["by_model"][m]["scores"].append(r["score"])
        summary["by_model"][m]["costs"].append(r["cost_usd"])
        summary["by_model"][m]["latencies"].append(r["latency_s"])
        summary["by_model"][m]["tokens_out"].append(r.get("output_tokens", 0))

        if m not in summary["by_category"][cat]:
            summary["by_category"][cat][m] = {"scores": [], "costs": []}
        summary["by_category"][cat][m]["scores"].append(r["score"])
        summary["by_category"][cat][m]["costs"].append(r["cost_usd"])

    for m, d in summary["by_model"].items():
        n = len(d["scores"])
        d["avg_score"]      = round(sum(d["scores"]) / n, 4)
        d["total_cost_usd"] = round(sum(d["costs"]), 8)
        d["avg_latency_s"]  = round(sum(d["latencies"]) / n, 3)
        d["avg_tokens_out"] = round(sum(d["tokens_out"]) / n, 1)
        d["score_per_dollar"] = round(d["avg_score"] / d["total_cost_usd"], 4) if d["total_cost_usd"] > 0 else 0
        d["total_prompts"]  = n

    for cat, models in summary["by_category"].items():
        for m, d in models.items():
            n = len(d["scores"])
            d["avg_score"]      = round(sum(d["scores"]) / n, 4)
            d["total_cost_usd"] = round(sum(d["costs"]), 8)

    return summary

def run_benchmarks() -> list:
    results = []
    total = sum(len(p) for p in TASK_PROMPTS.values()) * len(MODELS)
    done  = 0
    for model_key, model_id in MODELS.items():
        info = MODEL_INFO[model_key]
        print(f"\n{'='*60}")
        print(f"  {info['name']}  |  {info['params']}  |  {info['arch']}")
        print(f"  slug: {model_id}")
        print(f"{'='*60}")
        for category, prompts in TASK_PROMPTS.items():
            print(f"\n  [{category.upper()}]")
            for i, prompt in enumerate(prompts):
                done += 1
                print(f"    ({done}/{total}) {prompt[:60]}...", end=" ", flush=True)
                try:
                    out   = call_openrouter(model_id, prompt)
                    score = score_response(prompt, out["response"], category)
                    cost  = compute_cost(model_key, out["input_tokens"], out["output_tokens"])
                    results.append({
                        "model_key":     model_key,
                        "model_id":      model_id,
                        "category":      category,
                        "prompt_idx":    i,
                        "prompt":        prompt[:100],
                        "score":         score,
                        "cost_usd":      cost,
                        "latency_s":     out["latency_s"],
                        "input_tokens":  out["input_tokens"],
                        "output_tokens": out["output_tokens"],
                        "response":      out["response"][:300],
                    })
                    print(f"score={score:.3f}  cost=${cost:.7f}  {out['latency_s']}s")
                except Exception as e:
                    print(f"ERROR: {e}")
                    results.append({
                        "model_key": model_key, "model_id": model_id,
                        "category": category,   "prompt_idx": i,
                        "prompt":   prompt[:100],
                        "score": 0.0, "cost_usd": 0.0, "latency_s": 0.0,
                        "input_tokens": 0, "output_tokens": 0, "error": str(e),
                    })
                time.sleep(0.3)
    return results

if __name__ == "__main__":
    out_dir = Path(__file__).parent.parent / "results"
    out_dir.mkdir(exist_ok=True)

    print("NEO Benchmark: Gemma 4 26B MoE vs Qwen 3.5 27B")
    print(f"Prompts: {sum(len(p) for p in TASK_PROMPTS.values())} x {len(MODELS)} models = "
          f"{sum(len(p) for p in TASK_PROMPTS.values()) * len(MODELS)} total calls\n")

    results = run_benchmarks()
    summary = generate_summary(results)

    (out_dir / "benchmark_results.json").write_text(json.dumps(results, indent=2))
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2))

    print("\n" + "="*60)
    print("  RESULTS SUMMARY")
    print("="*60)
    for model_key, stats in summary["by_model"].items():
        info = MODEL_INFO[model_key]
        print(f"\n  {info['name']} ({info['params']})")
        print(f"    Avg Score:     {stats['avg_score']}")
        print(f"    Total Cost:    ${stats['total_cost_usd']:.7f}")
        print(f"    Avg Latency:   {stats['avg_latency_s']}s")
        print(f"    Score/Dollar:  {stats['score_per_dollar']}")

    print(f"\nSaved to {out_dir}/")
    print("Run scripts/visualize.py to generate charts.")
