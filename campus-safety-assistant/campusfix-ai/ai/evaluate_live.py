"""Live evaluation: REAL Gemini vision + reasoning on every dataset photo.

Each call sends actual image bytes to the API (costs quota + seconds).
Usage:
    python -m ai.evaluate_live --limit 6        # quick check
    python -m ai.evaluate_live                  # full 22-image bench
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ai.inference import analyze_incident  # noqa: E402

HERE = Path(__file__).resolve().parent


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=str(HERE / "dataset"))
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()
    DATA = Path(args.dir)
    manifest = json.loads((DATA / "manifest.json").read_text())
    if args.limit:
        manifest = manifest[: args.limit]

    n = len(manifest)
    cc = sc = 0
    print(f"LIVE GEMINI EVALUATION  n={n} (real API calls)")
    print("-" * 90)
    for m in manifest:
        img = (DATA / m["file"]).read_bytes()
        t0 = time.perf_counter()
        try:
            out = analyze_incident(description=m["description"], location=m["location"],
                                   image_bytes=img, filename=m["file"], check_duplicates=False)
        except Exception as e:  # quota / network -> report, don't crash the bench
            print(f"[ERR ] {m['file']:20s} {type(e).__name__}: {str(e)[:120]}")
            continue
        dt = time.perf_counter() - t0
        ok_c = out["category"] == m["expected_category"]
        ok_s = out["severity"] == m["expected_severity"]
        cc += ok_c
        sc += ok_s
        flag = "ok" if ok_c and ok_s else "MISS"
        print(f"[{flag}] {m['file']:20s} exp {m['expected_category']:14s}/{m['expected_severity']:8s} "
              f"got {out['category']:14s}/{out['severity']:8s} conf={out['confidence']:.0%} {dt:.1f}s")
        print(f"       caption: {(out.get('caption') or '')[:110]}")
    print("-" * 90)
    print(f"LIVE category accuracy : {cc / n:.1%}   LIVE severity accuracy : {sc / n:.1%}")
    return 0


if __name__ == "__main__":
    main()
