"""Image-level evaluation: feeds REAL image bytes through the full pipeline.

Usage:
    python -m ai.evaluate_images                  # simulated dataset
    python -m ai.evaluate_images --dir ai/dataset/real   # YOUR real photos + manifest.json
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

# Offline bench by default (deterministic, no quota). Live version: evaluate_live.py
import os
os.environ.setdefault("CAMPUSFIX_OFFLINE", "1")

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ai.inference import analyze_incident  # noqa: E402

HERE = Path(__file__).resolve().parent


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=str(HERE / "dataset"))
    DATA = Path(ap.parse_args().dir)
    manifest = json.loads((DATA / "manifest.json").read_text())
    n = len(manifest)
    cc = sc = low = 0
    lat: list[float] = []
    print(f"IMAGE EVALUATION  n={n} ({DATA}, real JPEG bytes, offline)")
    print("-" * 78)
    for m in manifest:
        img = (DATA / m["file"]).read_bytes()
        t0 = time.perf_counter()
        out = analyze_incident(description=m["description"], location=m["location"],
                               image_bytes=img, filename=m["file"], check_duplicates=False)
        lat.append((time.perf_counter() - t0) * 1000)
        ok_c = out["category"] == m["expected_category"]
        ok_s = out["severity"] == m["expected_severity"]
        cc += ok_c
        sc += ok_s
        low += out["needs_human_review"]
        flag = "ok" if ok_c and ok_s else "MISS"
        print(f"[{flag}] {m['file']:20s} {m['expected_category']:14s}/{m['expected_severity']:8s} "
              f"-> {out['category']:14s}/{out['severity']:8s} conf={out['confidence']:.0%} "
              f"{'REVIEW' if out['needs_human_review'] else 'auto'} {lat[-1]:.1f}ms")
    print("-" * 78)
    print(f"Category accuracy : {cc / n:.1%}   Severity accuracy : {sc / n:.1%}")
    print(f"Human-review rate : {low / n:.0%}   Avg latency : {sum(lat) / n:.1f} ms")
    ok = cc / n >= 0.85 and sc / n >= 0.80
    print("IMAGE GATES (cat>=85%, sev>=80%):", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
