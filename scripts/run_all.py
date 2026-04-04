#!/usr/bin/env python3
"""
Run the full benchmark pipeline end-to-end:
  1. Run benchmarks (API calls)
  2. Generate visualizations
  3. Write findings.md
"""

import subprocess
import sys
from pathlib import Path

ROOT    = Path(__file__).parent.parent
SCRIPTS = Path(__file__).parent

def run(script: str, desc: str):
    print(f"\n{'='*60}")
    print(f"  {desc}")
    print(f"{'='*60}")
    result = subprocess.run([sys.executable, str(SCRIPTS / script)], check=True)
    return result.returncode == 0

if __name__ == "__main__":
    run("benchmark_runner.py", "Step 1/3 — Running benchmarks")
    run("visualize.py",        "Step 2/3 — Generating charts")
    run("write_findings.py",   "Step 3/3 — Writing findings report")
    print("\n Pipeline complete. See results/ and outputs/")
