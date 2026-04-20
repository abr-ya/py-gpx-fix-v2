from __future__ import annotations

import numpy as np

from gpx_clean.metrics import (
    geodesic_distances_m,
    segment_accelerations_mps2,
    segment_speeds_mps,
    times_to_seconds,
)

DEFAULT_MIN_DT_S = 1e-3


def filter_trackpoint_mask(
    lat: np.ndarray,
    lon: np.ndarray,
    times: np.ndarray,
    *,
    max_speed_mps: float,
    max_acceleration_mps2: float | None = 15.0,
    min_dt_s: float = DEFAULT_MIN_DT_S,
    max_iterations: int = 50_000,
) -> tuple[np.ndarray, int]:
    """
    Return (keep_mask, removed_count) for n trackpoints.

    Duplicate timestamps are removed in bulk each pass. Speed and acceleration violations
    remove at most one point per pass (leftmost offending segment / middle).
    """
    n = lat.shape[0]
    if n == 0:
        return np.array([], dtype=bool), 0
    if n == 1:
        return np.ones(1, dtype=bool), 0

    keep = np.ones(n, dtype=bool)
    t = times_to_seconds(times)

    if np.any(~np.isfinite(t)):
        raise ValueError("All trackpoints must have valid timestamps for speed-based filtering.")

    removed_total = 0
    for _ in range(max_iterations):
        idx = np.where(keep)[0]
        if idx.size < 2:
            break

        lat_k = lat[idx]
        lon_k = lon[idx]
        t_k = t[idx]

        dists = geodesic_distances_m(lat_k, lon_k)
        dt = np.diff(t_k)

        dup_bad = {k + 1 for k in range(dt.size) if dt[k] <= min_dt_s}
        if dup_bad:
            orig = idx[sorted(dup_bad)]
            keep[orig] = False
            removed_total += int(orig.size)
            continue

        speeds = segment_speeds_mps(dists, dt, min_dt_s)
        removed_one = False
        for k in range(speeds.size):
            if np.isfinite(speeds[k]) and speeds[k] > max_speed_mps:
                keep[idx[k + 1]] = False
                removed_total += 1
                removed_one = True
                break

        if removed_one:
            continue

        if max_acceleration_mps2 is not None and np.isfinite(max_acceleration_mps2):
            acc = segment_accelerations_mps2(speeds, dt, min_dt_s)
            for k in range(acc.size):
                if np.isfinite(acc[k]) and abs(acc[k]) > max_acceleration_mps2:
                    keep[idx[k + 1]] = False
                    removed_total += 1
                    removed_one = True
                    break

        if removed_one:
            continue

        break

    return keep, removed_total
