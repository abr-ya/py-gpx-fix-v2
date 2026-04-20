from __future__ import annotations

import numpy as np


def moving_average_lat_lon(
    lat: np.ndarray,
    lon: np.ndarray,
    *,
    window: int = 5,
) -> tuple[np.ndarray, np.ndarray]:
    """Centered moving average; window must be odd and >= 1. Edges use shrinking window."""
    if window < 1:
        raise ValueError("window must be >= 1")
    if window % 2 == 0:
        raise ValueError("window must be odd")
    n = lat.size
    if n == 0:
        return lat.copy(), lon.copy()
    if window == 1:
        return lat.copy(), lon.copy()

    half = window // 2
    lat_out = np.empty_like(lat, dtype=np.float64)
    lon_out = np.empty_like(lon, dtype=np.float64)
    for i in range(n):
        lo = max(0, i - half)
        hi = min(n, i + half + 1)
        lat_out[i] = float(np.mean(lat[lo:hi]))
        lon_out[i] = float(np.mean(lon[lo:hi]))
    return lat_out, lon_out
