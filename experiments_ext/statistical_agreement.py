"""Paired finite-panel agreement with simultaneous bootstrap intervals."""
from collections import defaultdict
import numpy as np


def classify_interval(interval, margin):
    lo, hi = interval
    if not (np.isfinite([lo, hi, margin]).all() and lo <= hi and margin > 0):
        raise ValueError("Invalid interval or margin")
    if lo >= -margin and hi <= margin:
        return "equivalent"
    if lo > margin or hi < -margin:
        return "incompatible"
    return "inconclusive"


def align_rows(rows, expected_seeds):
    seeds = [r['seed'] for r in rows]
    if len(seeds) != len(set(seeds)) or set(seeds) != set(expected_seeds):
        raise ValueError("Duplicate or missing seed")
    return sorted(rows, key=lambda r: r['seed'])


def bootstrap_means(matrix, draws, batch_size=1000):
    """Rows=metrics, columns=paired seeds; reuse each draw across all rows."""
    a = np.asarray(matrix, dtype=float)
    idx = np.asarray(draws)
    if a.ndim != 2 or idx.ndim != 2 or idx.shape[1] != a.shape[1]:
        raise ValueError("Invalid paired bootstrap shape")
    out = np.empty((len(idx), len(a)))
    for start in range(0, len(idx), batch_size):
        block = idx[start:start+batch_size]
        weights = np.zeros((len(block), a.shape[1]))
        np.add.at(weights, (np.arange(len(block))[:, None], block), 1)
        out[start:start+len(block)] = weights @ a.T / a.shape[1]
    return out


def simultaneous_agreement(metrics, resamples=20000, seed=20261015):
    """metrics contain id, cohort, fresh/reference arrays and positive margin.

    Fixed reference mean scales are supplied by the caller; max standardized
    bootstrap deviations control a single approximate family of intervals.
    """
    if not metrics or resamples < 100:
        raise ValueError("Metrics and adequate resamples required")
    if len({m['id'] for m in metrics}) != len(metrics):
        raise ValueError("Duplicate metric id")
    cohorts = defaultdict(list)
    for i, m in enumerate(metrics):
        a, b = np.asarray(m['fresh'], float), np.asarray(m['reference'], float)
        if a.ndim != 1 or a.shape != b.shape or len(a) < 2 or not np.isfinite([a,b]).all():
            raise ValueError("Unpaired or nonfinite data")
        if m['scale'] <= 0 or m['margin'] <= 0:
            raise ValueError("Positive scale and margin required")
        cohorts[m['cohort']].append((i, (a-b)/m['scale']))
    rng = np.random.default_rng(seed)
    boots = np.empty((resamples, len(metrics)))
    observed, se = np.empty(len(metrics)), np.empty(len(metrics))
    for cohort in sorted(cohorts):
        records = cohorts[cohort]
        n = len(records[0][1])
        if any(len(d) != n for _, d in records):
            raise ValueError("Different seed counts within cohort")
        indices = rng.integers(0, n, (resamples, n))
        matrix = np.stack([d for _,d in records])
        values = bootstrap_means(matrix, indices)
        for j, (i,d) in enumerate(records):
            observed[i] = d.mean()
            # A repeated non-binary decimal can acquire a tiny artificial std
            # through mean-rounding; do not inflate the max statistic with it.
            se[i] = 0.0 if np.ptp(d)==0 else d.std(ddof=1)/np.sqrt(n)
            boots[:,i] = values[:,j]
    active = se > 0
    max_scores = (np.max(np.abs((boots[:,active]-observed[active])/se[active]), axis=1)
                  if active.any() else np.zeros(resamples))
    critical = float(np.percentile(max_scores, 95))
    results = []
    for i,m in enumerate(metrics):
        family = [float(observed[i]-critical*se[i]), float(observed[i]+critical*se[i])]
        d = np.asarray(m['fresh'])-np.asarray(m['reference'])
        results.append(dict(id=m['id'],cohort=m['cohort'],n=len(d),scale=m['scale'],
            margin=m['margin'],delta_mean=float(d.mean()),normalized_delta_mean=float(observed[i]),
            normalized_ci95=[float(x) for x in np.percentile(boots[:,i],[2.5,97.5])],
            simultaneous_interval=family,classification=classify_interval(family,m['margin']),
            positive_seeds=int((d>1e-9).sum()),negative_seeds=int((d < -1e-9).sum()),
            same_seeds=int((np.abs(d)<=1e-9).sum()),max_absolute_difference=float(np.max(np.abs(d)))))
    return dict(resamples=resamples,seed=seed,family_size=len(metrics),critical_value=critical,
        method="paired bootstrap max absolute standardized centered-mean deviation; fixed sample SE",
        caveat="Approximate finite-panel inference; zero observed variance is not proof for unseen seeds.",
        results=results,all_equivalent=all(r['classification']=='equivalent' for r in results))
