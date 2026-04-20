from __future__ import annotations

import numpy as np
from geographiclib.geodesic import Geodesic

_G = Geodesic.WGS84


def geodesic_distances_m(lat: np.ndarray, lon: np.ndarray) -> np.ndarray:
    """Pairwise geodesic distances between consecutive points (meters). len == n - 1."""
    n = lat.shape[0]
    if n < 2:
        return np.array([], dtype=np.float64)
    out = np.empty(n - 1, dtype=np.float64)
    for i in range(n - 1):
        inv = _G.Inverse(float(lat[i]), float(lon[i]), float(lat[i + 1]), float(lon[i + 1]))
        out[i] = inv["s12"]
    return out


def times_to_seconds(times: np.ndarray) -> np.ndarray:
    """Convert datetime64[s|ms|us] or object datetimes to float seconds (epoch)."""
    if times.dtype == object:
        import datetime as _dt

        base = np.array(
            [t.timestamp() if t is not None else np.nan for t in times],
            dtype=np.float64,
        )
        return base
    # numpy datetime64
    return times.astype("datetime64[ns]").astype(np.int64) / 1e9


def segment_speeds_mps(dists_m: np.ndarray, dt_s: np.ndarray, min_dt_s: float) -> np.ndarray:
    """Speed for each segment; np.inf where dt <= min_dt_s."""
    v = np.empty_like(dists_m, dtype=np.float64)
    mask = dt_s > min_dt_s
    v[:] = np.inf
    v[mask] = dists_m[mask] / dt_s[mask]
    return v


def segment_accelerations_mps2(v: np.ndarray, dt_s: np.ndarray, min_dt_s: float) -> np.ndarray:
    """Acceleration at interior points (len n-2 for n-1 segments)."""
    if v.size < 2:
        return np.array([], dtype=np.float64)
    dv = np.diff(v)
    dt_mid = (dt_s[:-1] + dt_s[1:]) / 2.0
    a = np.empty_like(dv, dtype=np.float64)
    mask = dt_mid > min_dt_s
    a[:] = np.inf
    a[mask] = dv[mask] / dt_mid[mask]
    return a
