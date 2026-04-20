from __future__ import annotations

import copy
from typing import Iterable

import gpxpy.gpx


def assert_matching_track_layout(
    a: gpxpy.gpx.GPX,
    b: gpxpy.gpx.GPX,
    *,
    a_label: str = "source",
    b_label: str = "reference",
) -> None:
    if len(a.tracks) != len(b.tracks):
        raise ValueError(
            f"{a_label} has {len(a.tracks)} track(s) but {b_label} has {len(b.tracks)}; "
            "structures must match."
        )
    for ti, (ta, tb) in enumerate(zip(a.tracks, b.tracks)):
        if len(ta.segments) != len(tb.segments):
            raise ValueError(
                f"Track {ti}: {a_label} has {len(ta.segments)} segment(s) but "
                f"{b_label} has {len(tb.segments)}; structures must match."
            )


def _ref_lookup(ref_points: Iterable[gpxpy.gpx.GPXTrackPoint], coord_epsilon_deg: float):
    pts = list(ref_points)
    if coord_epsilon_deg == 0.0:
        return ("set", {(float(p.latitude), float(p.longitude)) for p in pts})
    coords = [(float(p.latitude), float(p.longitude)) for p in pts]
    return ("list", coords)


def _coord_in_ref(lat: float, lon: float, lookup: tuple, coord_epsilon_deg: float) -> bool:
    kind, data = lookup
    if kind == "set":
        return (lat, lon) in data
    for rlat, rlon in data:
        if abs(lat - rlat) <= coord_epsilon_deg and abs(lon - rlon) <= coord_epsilon_deg:
            return True
    return False


def filter_segment_points_by_reference(
    source_points: list[gpxpy.gpx.GPXTrackPoint],
    reference_points: list[gpxpy.gpx.GPXTrackPoint],
    *,
    coord_epsilon_deg: float,
) -> list[gpxpy.gpx.GPXTrackPoint]:
    if coord_epsilon_deg < 0:
        raise ValueError("coord_epsilon_deg must be non-negative.")
    lookup = _ref_lookup(reference_points, coord_epsilon_deg)
    out: list[gpxpy.gpx.GPXTrackPoint] = []
    for p in source_points:
        lat = float(p.latitude)
        lon = float(p.longitude)
        if _coord_in_ref(lat, lon, lookup, coord_epsilon_deg):
            out.append(copy.copy(p))
    return out
