# GPX outlier cleaning (runner) — design snapshot

This document records the specification agreed before implementation. The working tool is `gpx_clean`; see [README.md](../README.md).

## Context

GPS tracks may contain coordinate jumps and a short tail of bad points before returning to the true route. The goal is to drop points inconsistent with plausible **running speed and acceleration**, with user-tunable limits.

## Detection approach

1. **Segment speed** between consecutive kept points: \(v = d/\Delta t\) using geodesic \(d\). If \(v > v_{\max}\), drop the end point of that segment (one point per iteration so a later “return” point is re-evaluated against the last good fix).
2. **Acceleration** between consecutive segment speeds (optional): flag the middle point if \(|a|\) exceeds a cap; again one removal per pass.
3. **Duplicate timestamps**: if \(\Delta t \le\) `min_dt`, drop the later point (batch all such endpoints in one pass).
4. Iterate until no violations or `max_iterations`.

**Smoothing** is optional, numpy-only moving average on lat/lon **after** filtering, default **off** (`--enable-smooth`).

## Libraries

- `gpxpy`, `geographiclib`, `numpy`, `pytest` (no `scipy`).

## I/O contract

- **Input**: GPX file path. **Output**: separate GPX path (`-o`); same path as input is rejected.
- **Metadata**: preserve structure and fields where possible; do not alter waypoints/routes; replace track segment point lists with filtered points.
- **Provenance**: append an English line to the root GPX `<description>` (`Filtered with gpx-clean …; removed N/M trackpoints; …`). Append `filtered` to `<keywords>` without clobbering existing tags.

## Edge cases

- **Missing times** on any trackpoint: raise a clear error (speed filtering requires time).
- **Empty segments**: left empty.

## Project layout

- `src/gpx_clean/`: `metrics.py`, `filter.py`, `smooth.py`, `io.py`, `cli.py`, `__main__.py`
- `tests/`: synthetic and file-based tests, `tests/data/*.gpx`
