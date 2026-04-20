from __future__ import annotations

from pathlib import Path

import gpxpy
import pytest

from gpx_clean.io import load_gpx, subset_gpx_file


def test_subset_keeps_matching_coordinates_in_order(tmp_path: Path) -> None:
    source_xml = """<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" xmlns="http://www.topografix.com/GPX/1/1">
  <trk><trkseg>
    <trkpt lat="52.0" lon="13.0"><time>2020-01-01T10:00:00Z</time></trkpt>
    <trkpt lat="52.1" lon="13.1"><time>2020-01-01T10:00:01Z</time></trkpt>
    <trkpt lat="52.2" lon="13.2"><time>2020-01-01T10:00:02Z</time></trkpt>
    <trkpt lat="52.3" lon="13.3"><time>2020-01-01T10:00:03Z</time></trkpt>
  </trkseg></trk>
</gpx>"""
    ref_xml = """<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" xmlns="http://www.topografix.com/GPX/1/1">
  <trk><trkseg>
    <trkpt lat="52.1" lon="13.1"></trkpt>
    <trkpt lat="52.3" lon="13.3"></trkpt>
  </trkseg></trk>
</gpx>"""
    src = tmp_path / "s.gpx"
    ref = tmp_path / "r.gpx"
    out = tmp_path / "o.gpx"
    src.write_text(source_xml, encoding="utf-8")
    ref.write_text(ref_xml, encoding="utf-8")
    stats = subset_gpx_file(src, ref, out, coord_epsilon_deg=0.0)
    assert stats.trackpoints_before == 4
    assert stats.trackpoints_after == 2
    assert stats.removed == 2
    gpx = gpxpy.parse(out.read_text(encoding="utf-8"))
    seg = gpx.tracks[0].segments[0]
    assert len(seg.points) == 2
    assert seg.points[0].latitude == 52.1 and seg.points[0].time is not None
    assert seg.points[1].latitude == 52.3


def test_subset_segment_count_mismatch_raises(tmp_path: Path) -> None:
    source_xml = """<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" xmlns="http://www.topografix.com/GPX/1/1">
  <trk><trkseg>
    <trkpt lat="0" lon="0"><time>2020-01-01T10:00:00Z</time></trkpt>
  </trkseg></trk>
</gpx>"""
    ref_xml = """<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" xmlns="http://www.topografix.com/GPX/1/1">
  <trk><trkseg><trkpt lat="0" lon="0"></trkpt></trkseg>
  <trkseg><trkpt lat="1" lon="1"></trkpt></trkseg></trk>
</gpx>"""
    src = tmp_path / "s.gpx"
    ref = tmp_path / "r.gpx"
    out = tmp_path / "o.gpx"
    src.write_text(source_xml, encoding="utf-8")
    ref.write_text(ref_xml, encoding="utf-8")
    with pytest.raises(ValueError, match="segment"):
        subset_gpx_file(src, ref, out)


def test_subset_epsilon_matches_near_coordinates(tmp_path: Path) -> None:
    source_xml = """<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" xmlns="http://www.topografix.com/GPX/1/1">
  <trk><trkseg>
    <trkpt lat="52.0" lon="13.0"><time>2020-01-01T10:00:00Z</time></trkpt>
  </trkseg></trk>
</gpx>"""
    ref_xml = """<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" xmlns="http://www.topografix.com/GPX/1/1">
  <trk><trkseg>
    <trkpt lat="52.00000005" lon="13.00000005"></trkpt>
  </trkseg></trk>
</gpx>"""
    src = tmp_path / "s.gpx"
    ref = tmp_path / "r.gpx"
    out = tmp_path / "o.gpx"
    src.write_text(source_xml, encoding="utf-8")
    ref.write_text(ref_xml, encoding="utf-8")
    subset_gpx_file(src, ref, out, coord_epsilon_deg=1e-6)
    gpx = load_gpx(out)
    assert len(gpx.tracks[0].segments[0].points) == 1


def test_subset_strict_no_match_when_coords_differ_slightly(tmp_path: Path) -> None:
    source_xml = """<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" xmlns="http://www.topografix.com/GPX/1/1">
  <trk><trkseg>
    <trkpt lat="52.0" lon="13.0"><time>2020-01-01T10:00:00Z</time></trkpt>
  </trkseg></trk>
</gpx>"""
    ref_xml = """<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" xmlns="http://www.topografix.com/GPX/1/1">
  <trk><trkseg>
    <trkpt lat="52.00000005" lon="13.00000005"></trkpt>
  </trkseg></trk>
</gpx>"""
    src = tmp_path / "s.gpx"
    ref = tmp_path / "r.gpx"
    out = tmp_path / "o.gpx"
    src.write_text(source_xml, encoding="utf-8")
    ref.write_text(ref_xml, encoding="utf-8")
    stats = subset_gpx_file(src, ref, out, coord_epsilon_deg=0.0)
    assert stats.trackpoints_after == 0


def test_subset_missing_source_time_raises(tmp_path: Path) -> None:
    source_xml = """<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" xmlns="http://www.topografix.com/GPX/1/1">
  <trk><trkseg>
    <trkpt lat="52.0" lon="13.0"></trkpt>
  </trkseg></trk>
</gpx>"""
    ref_xml = """<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" xmlns="http://www.topografix.com/GPX/1/1">
  <trk><trkseg>
    <trkpt lat="52.0" lon="13.0"></trkpt>
  </trkseg></trk>
</gpx>"""
    src = tmp_path / "s.gpx"
    ref = tmp_path / "r.gpx"
    out = tmp_path / "o.gpx"
    src.write_text(source_xml, encoding="utf-8")
    ref.write_text(ref_xml, encoding="utf-8")
    with pytest.raises(ValueError, match="timestamps"):
        subset_gpx_file(src, ref, out)
