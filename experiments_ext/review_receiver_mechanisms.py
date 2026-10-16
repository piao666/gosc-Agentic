"""Read-only reanalysis of saved author diagnostics; never runs a mission.

Writes to a new directory only. Ordinal versus average-tie rank comparisons are
descriptive sensitivity checks, without confidence intervals or significance tests.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

import numpy as np

from experiments.analyze_fidelity import rk, spearman


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def average_ranks(x):
    _, inverse, counts = np.unique(np.asarray(x), return_inverse=True, return_counts=True)
    starts = np.cumsum(counts) - counts
    return (starts + (counts - 1) / 2)[inverse]


def correlation(x, y):
    x, y = np.asarray(x), np.asarray(y)
    if len(x) < 2 or np.all(x == x[0]) or np.all(y == y[0]):
        return None
    return float(np.corrcoef(x, y)[0, 1])


def review(root):
    source = root / "results/rev_value_fidelity.json"
    if source.exists():
        rows = json.loads(source.read_text(encoding="utf-8"))
    else:
        source = source.with_suffix(".json.gz")
        with gzip.open(source, "rt", encoding="utf-8") as f:
            rows = json.load(f)
    result = {
        "analysis_kind": "saved_author_data_only_no_new_simulation",
        "input_path": str(source), "input_sha256": sha(source),
        "records": len(rows), "missions": len({r["seed"] for r in rows}),
        "missing_target_change_count": sum(r.get("n_teammate_changes") is None for r in rows),
        "metric_warning": "gt_gain != 0 measures changed coverage utility, not count of changed targets",
        "rank_sensitivity": "point estimates only, no CI, no significance claim",
        "kinds": {},
    }
    for kind in ("E", "I", "EI"):
        group = [r for r in rows if r["kind"] == kind]
        gain = np.asarray([r["gt_gain"] for r in group])
        dtime = np.asarray([r["dT"] for r in group])
        stats = {
            "n": len(group), "nonzero_coverage_gain": int(np.count_nonzero(gain)),
            "nonzero_coverage_gain_fraction": float(np.mean(gain != 0)),
            "positive_dT": int(np.sum(dtime > 0)), "negative_dT": int(np.sum(dtime < 0)),
            "zero_dT": int(np.sum(dtime == 0)), "ranks": {},
        }
        for estimator in ("tom", "tv", "bits", "aoi"):
            x = [r["est"][estimator] for r in group]
            author = spearman(x, dtime)
            stats["ranks"][estimator] = {
                "unique_feature_values": len(set(x)), "unique_dT_values": len(set(dtime)),
                "author_ordinal_rho": float(author) if np.isfinite(author) else None,
                "average_tie_rho": correlation(average_ranks(x), average_ranks(dtime)),
            }
        result["kinds"][kind] = stats
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    result = review(root)
    protected = json.loads((root / ".local/reproduction/2026-10-15-baseline-v1/"
                           "protected_checkout_inputs.json").read_text(encoding="utf-8"))
    result["protected_inputs"] = {
        "checked": len(protected),
        "differences": [p for p, expected in protected.items() if sha(root / p) != expected],
    }
    args.output_dir.mkdir(parents=True, exist_ok=False)
    with (args.output_dir / "saved_diagnostic_audit.json").open("x", encoding="utf-8") as f:
        json.dump(result, f, indent=2, allow_nan=False)
    print(json.dumps(result, indent=2, allow_nan=False))
    if result["protected_inputs"]["differences"]:
        raise SystemExit("Protected baseline inputs changed")


if __name__ == "__main__":
    main()
