from __future__ import annotations

import copy
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import gpxpy
import gpxpy.gpx
import numpy as np

from gpx_clean import __version__
from gpx_clean.filter import filter_trackpoint_mask
from gpx_clean.smooth import moving_average_lat_lon
from gpx_clean.subset import assert_matching_track_layout, filter_segment_points_by_reference


@dataclass
class CleanStats:
    trackpoints_before: int
    trackpoints_after: int
    segments_processed: int

    @property
    def removed(self) -> int:
        return self.trackpoints_before - self.trackpoints_after


@dataclass
class SubsetStats:
    trackpoints_before: int
    trackpoints_after: int
    segments_processed: int

    @property
    def removed(self) -> int:
        return self.trackpoints_before - self.trackpoints_after


def load_gpx(path: Path) -> gpxpy.gpx.GPX:
    text = path.read_text(encoding="utf-8", errors="replace")
    return gpxpy.parse(text)


def save_gpx(gpx: gpxpy.gpx.GPX, path: Path) -> None:
    path.write_text(gpx.to_xml(), encoding="utf-8")


def _append_description(existing: str | None, addition: str) -> str:
    if not existing:
        return addition
    return f"{existing.rstrip()}\n\n{addition}"


def _append_keywords(existing: str | None, tag: str = "filtered") -> str | None:
    parts = [p.strip() for p in (existing or "").split(",") if p.strip()]
    if tag not in parts:
        parts.append(tag)
    return ", ".join(parts) if parts else tag


def apply_provenance(
    gpx: gpxpy.gpx.GPX,
    *,
    stats: CleanStats,
    max_speed_mps: float,
    max_acceleration_mps2: float | None,
    smooth_enabled: bool,
    smooth_window: int,
) -> None:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    acc_part = (
        f"max_acceleration_mps2={max_acceleration_mps2}"
        if max_acceleration_mps2 is not None and np.isfinite(max_acceleration_mps2)
        else "max_acceleration_mps2=disabled"
    )
    smooth_part = f"smooth=off" if not smooth_enabled else f"smooth=on window={smooth_window}"
    line = (
        f"Filtered with gpx-clean {__version__} at {ts}; "
        f"removed {stats.removed}/{stats.trackpoints_before} trackpoints; "
        f"max_speed_mps={max_speed_mps:g} {acc_part}; {smooth_part}"
    )
    gpx.description = _append_description(gpx.description, line)
    gpx.keywords = _append_keywords(gpx.keywords)


def apply_subset_provenance(
    gpx: gpxpy.gpx.GPX,
    *,
    stats: SubsetStats,
    coord_epsilon_deg: float,
) -> None:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    eps_part = f"coord_epsilon_deg={coord_epsilon_deg:g}" if coord_epsilon_deg else "coord_epsilon_deg=0 (strict)"
    line = (
        f"Coordinate subset with gpx-clean {__version__} at {ts}; "
        f"kept {stats.trackpoints_after}/{stats.trackpoints_before} trackpoints "
        f"({stats.removed} dropped); {eps_part}"
    )
    gpx.description = _append_description(gpx.description, line)
    gpx.keywords = _append_keywords(gpx.keywords, tag="subset")


def _segment_to_arrays(segment: gpxpy.gpx.GPXTrackSegment) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    pts = segment.points
    lat = np.array([float(p.latitude) for p in pts], dtype=np.float64)
    lon = np.array([float(p.longitude) for p in pts], dtype=np.float64)
    times = np.empty(len(pts), dtype=object)
    for i, p in enumerate(pts):
        times[i] = p.time
    return lat, lon, times


def _validate_times(times: np.ndarray) -> None:
    if times.size == 0:
        return
    for t in times:
        if t is None:
            raise ValueError(
                "All trackpoints must have timestamps. Re-export the GPX with time on each point."
            )


def clean_gpx(
    gpx: gpxpy.gpx.GPX,
    *,
    max_speed_mps: float,
    max_acceleration_mps2: float | None,
    min_dt_s: float,
    max_iterations: int,
    smooth: bool,
    smooth_window: int,
) -> CleanStats:
    raw_total = sum(len(s.points) for t in gpx.tracks for s in t.segments)
    total_after = 0
    segments_n = 0

    for track in gpx.tracks:
        for segment in track.segments:
            segments_n += 1
            pts = segment.points
            if not pts:
                continue

            lat, lon, times = _segment_to_arrays(segment)
            _validate_times(times)

            keep, _ = filter_trackpoint_mask(
                lat,
                lon,
                times,
                max_speed_mps=max_speed_mps,
                max_acceleration_mps2=max_acceleration_mps2,
                min_dt_s=min_dt_s,
                max_iterations=max_iterations,
            )

            kept_idx = np.where(keep)[0]
            lat_k = lat[keep]
            lon_k = lon[keep]

            if smooth and lat_k.size > 0:
                lat_k, lon_k = moving_average_lat_lon(lat_k, lon_k, window=smooth_window)

            new_points: list[gpxpy.gpx.GPXTrackPoint] = []
            for j, orig_i in enumerate(kept_idx):
                p = pts[int(orig_i)]
                q = copy.copy(p)
                q.latitude = float(lat_k[j])
                q.longitude = float(lon_k[j])
                new_points.append(q)

            segment.points = new_points
            total_after += len(new_points)

    stats = CleanStats(
        trackpoints_before=raw_total,
        trackpoints_after=total_after,
        segments_processed=segments_n,
    )
    apply_provenance(
        gpx,
        stats=stats,
        max_speed_mps=max_speed_mps,
        max_acceleration_mps2=max_acceleration_mps2,
        smooth_enabled=smooth,
        smooth_window=smooth_window,
    )
    return stats


def clean_gpx_file(
    input_path: Path,
    output_path: Path,
    *,
    max_speed_mps: float,
    max_acceleration_mps2: float | None,
    min_dt_s: float,
    max_iterations: int,
    smooth: bool,
    smooth_window: int,
) -> CleanStats:
    gpx = load_gpx(input_path)
    stats = clean_gpx(
        gpx,
        max_speed_mps=max_speed_mps,
        max_acceleration_mps2=max_acceleration_mps2,
        min_dt_s=min_dt_s,
        max_iterations=max_iterations,
        smooth=smooth,
        smooth_window=smooth_window,
    )
    save_gpx(gpx, output_path)
    return stats


def subset_gpx(
    gpx_source: gpxpy.gpx.GPX,
    gpx_reference: gpxpy.gpx.GPX,
    *,
    coord_epsilon_deg: float = 0.0,
) -> SubsetStats:
    assert_matching_track_layout(gpx_source, gpx_reference)
    raw_total = sum(len(s.points) for t in gpx_source.tracks for s in t.segments)
    total_after = 0
    segments_n = 0

    for track_s, track_r in zip(gpx_source.tracks, gpx_reference.tracks):
        for seg_s, seg_r in zip(track_s.segments, track_r.segments):
            segments_n += 1
            pts = seg_s.points
            if not pts:
                seg_s.points = []
                continue

            _, _, times = _segment_to_arrays(seg_s)
            _validate_times(times)

            seg_s.points = filter_segment_points_by_reference(
                pts,
                seg_r.points,
                coord_epsilon_deg=coord_epsilon_deg,
            )
            total_after += len(seg_s.points)

    stats = SubsetStats(
        trackpoints_before=raw_total,
        trackpoints_after=total_after,
        segments_processed=segments_n,
    )
    apply_subset_provenance(gpx_source, stats=stats, coord_epsilon_deg=coord_epsilon_deg)
    return stats


def subset_gpx_file(
    source_path: Path,
    reference_path: Path,
    output_path: Path,
    *,
    coord_epsilon_deg: float = 0.0,
) -> SubsetStats:
    gpx_source = load_gpx(source_path)
    gpx_reference = load_gpx(reference_path)
    stats = subset_gpx(
        gpx_source,
        gpx_reference,
        coord_epsilon_deg=coord_epsilon_deg,
    )
    save_gpx(gpx_source, output_path)
    return stats
