from __future__ import annotations

from datetime import datetime, timedelta, timezone

import numpy as np
import pytest

from gpx_clean.filter import filter_trackpoint_mask


def _times(n: int, step_s: float = 1.0) -> np.ndarray:
    base = datetime(2020, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
    return np.array([base + timedelta(seconds=i * step_s) for i in range(n)], dtype=object)


def test_filter_removes_speed_outlier_and_tail():
    n = 15
    lat = np.array([52.0] * n, dtype=np.float64)
    lon = np.array([0.0 + i * 7e-5 for i in range(n)], dtype=np.float64)
    lon[10] = 1.0
    lon[11] = 0.5
    lon[12] = 0.3
    lon[13] = lon[9] + 7e-5 * 4

    t = _times(n)
    keep, _ = filter_trackpoint_mask(
        lat,
        lon,
        t,
        max_speed_mps=12.0,
        max_acceleration_mps2=None,
        max_iterations=50,
    )
    kept_lon = lon[keep]
    assert keep.sum() < n
    assert float(np.max(np.abs(kept_lon))) < 0.02


def test_duplicate_time_drops_later_point():
    lat = np.array([0.0, 0.0, 0.0001], dtype=np.float64)
    lon = np.array([0.0, 0.0, 0.0], dtype=np.float64)
    base = datetime(2020, 1, 1, tzinfo=timezone.utc)
    t = np.array([base, base, base + timedelta(seconds=1)], dtype=object)
    keep, _ = filter_trackpoint_mask(lat, lon, t, max_speed_mps=100.0, max_acceleration_mps2=None)
    assert keep.tolist() == [True, False, True]


def test_requires_timestamps():
    lat = np.array([0.0, 0.0], dtype=np.float64)
    lon = np.array([0.0, 0.0], dtype=np.float64)
    t = np.array([datetime(2020, 1, 1, tzinfo=timezone.utc), None], dtype=object)
    with pytest.raises(ValueError, match="timestamps"):
        filter_trackpoint_mask(lat, lon, t, max_speed_mps=10.0)


def test_single_point():
    lat = np.array([1.0])
    lon = np.array([2.0])
    t = _times(1)
    keep, _ = filter_trackpoint_mask(lat, lon, t, max_speed_mps=1.0)
    assert keep.tolist() == [True]
