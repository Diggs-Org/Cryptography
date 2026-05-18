"""Cross-runtime parity test: Python rng.py vs src/rng.js via Node.

Runs the JS implementation through Node.js and compares the first N floats
produced by each runtime for several seed strings.  Any divergence is a bug.

Usage:
    python3 scripts/test-rng-parity.py
"""
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from rng import make_rng, djb2

SEEDS = ["abc123", "puzzle42", "2026-05-18", "xk9q", "a", "zzzzzzzzzzzzzzzz"]
N = 20  # floats to compare per seed

JS_HARNESS = """
import {{ makeRng }} from './src/rng.js';
const seeds = {seeds};
const n = {n};
const out = {{}};
for (const seed of seeds) {{
  const rng = makeRng(seed);
  out[seed] = Array.from({{length: n}}, () => rng());
}}
process.stdout.write(JSON.stringify(out));
"""


def run_js(seeds, n):
    script = JS_HARNESS.format(seeds=json.dumps(seeds), n=n)
    root = Path(__file__).parent.parent
    tmp = root / "_rng_parity_test.mjs"
    tmp.write_text(script)
    try:
        result = subprocess.run(
            ["node", tmp.name],
            capture_output=True, text=True,
            cwd=root,
        )
    finally:
        tmp.unlink(missing_ok=True)
    if result.returncode != 0:
        print("Node error:", result.stderr, file=sys.stderr)
        sys.exit(1)
    return json.loads(result.stdout)


def run_python(seeds, n):
    out = {}
    for seed in seeds:
        rng = make_rng(seed)
        out[seed] = [rng() for _ in range(n)]
    return out


def main():
    print(f"Testing {len(SEEDS)} seeds × {N} samples each …")
    js_out = run_js(SEEDS, N)
    py_out = run_python(SEEDS, N)

    failures = 0
    for seed in SEEDS:
        js_vals = js_out[seed]
        py_vals = py_out[seed]
        for i, (j, p) in enumerate(zip(js_vals, py_vals)):
            if j != p:
                print(f"FAIL  seed={seed!r}  call={i}  js={j}  py={p}")
                failures += 1
        if failures == 0:
            print(f"  OK  seed={seed!r}")

    if failures:
        print(f"\n{failures} mismatch(es) — runtimes are NOT in parity.")
        sys.exit(1)
    else:
        print("\nAll values match — Python and JS are in parity.")


if __name__ == "__main__":
    main()
