from __future__ import annotations

from pathlib import Path

import gpxpy

from gpx_clean.io import clean_gpx_file, load_gpx


DATA = Path(__file__).resolve().parent / "data" / "sample_track.gpx"


def test_clean_preserves_metadata_and_adds_provenance(tmp_path):
    out = tmp_path / "out.gpx"
    clean_gpx_file(
        DATA,
        out,
        max_speed_mps=50.0,
        max_acceleration_mps2=None,
        min_dt_s=1e-3,
        max_iterations=10,
        smooth=False,
        smooth_window=5,
    )
    gpx = load_gpx(out)
    assert gpx.name == "Sample Run"
    assert gpx.author_name == "Test Author"
    assert "Original description" in (gpx.description or "")
    assert "Filtered with gpx-clean" in (gpx.description or "")
    assert "removed" in (gpx.description or "").lower()
    assert "max_speed_mps=" in (gpx.description or "")
    kw = (gpx.keywords or "").lower()
    assert "filtered" in kw
    assert "morning" in kw


def test_clean_removes_implausible_point(tmp_path):
    xml = """<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" xmlns="http://www.topografix.com/GPX/1/1">
  <metadata><name>T</name></metadata>
  <trk><name>X</name><trkseg>
    <trkpt lat="52.0" lon="13.0"><time>2020-01-01T10:00:00Z</time></trkpt>
    <trkpt lat="52.0001" lon="13.0001"><time>2020-01-01T10:00:10Z</time></trkpt>
    <trkpt lat="53.5" lon="20.0"><time>2020-01-01T10:00:11Z</time></trkpt>
    <trkpt lat="52.0002" lon="13.0002"><time>2020-01-01T10:00:20Z</time></trkpt>
  </trkseg></trk>
</gpx>"""
    inp = tmp_path / "in.gpx"
    out = tmp_path / "out.gpx"
    inp.write_text(xml, encoding="utf-8")
    clean_gpx_file(
        inp,
        out,
        max_speed_mps=12.0,
        max_acceleration_mps2=None,
        max_iterations=30,
        min_dt_s=1e-3,
        smooth=False,
        smooth_window=5,
    )
    gpx = gpxpy.parse(out.read_text(encoding="utf-8"))
    seg = gpx.tracks[0].segments[0]
    assert len(seg.points) == 3
    lats = [p.latitude for p in seg.points]
    assert min(lats) > 51.99 and max(lats) < 52.01


def test_missing_time_errors(tmp_path):
    xml = """<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" xmlns="http://www.topografix.com/GPX/1/1">
  <trk><trkseg>
    <trkpt lat="0" lon="0"><time>2020-01-01T10:00:00Z</time></trkpt>
    <trkpt lat="0" lon="0"></trkpt>
  </trkseg></trk>
</gpx>"""
    inp = tmp_path / "in.gpx"
    out = tmp_path / "out.gpx"
    inp.write_text(xml, encoding="utf-8")
    import pytest

    with pytest.raises(ValueError, match="timestamps"):
        clean_gpx_file(
            inp,
            out,
            max_speed_mps=10.0,
            max_acceleration_mps2=None,
            min_dt_s=1e-3,
            max_iterations=5,
            smooth=False,
            smooth_window=5,
        )


def test_smooth_changes_coordinates_when_enabled(tmp_path):
    xml = """<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" xmlns="http://www.topografix.com/GPX/1/1">
  <trk><trkseg>
    <trkpt lat="52.0" lon="13.0"><time>2020-01-01T10:00:00Z</time></trkpt>
    <trkpt lat="52.00025" lon="13.0"><time>2020-01-01T10:00:01Z</time></trkpt>
    <trkpt lat="52.00035" lon="13.0001"><time>2020-01-01T10:00:02Z</time></trkpt>
    <trkpt lat="52.0007" lon="13.0"><time>2020-01-01T10:00:03Z</time></trkpt>
    <trkpt lat="52.00085" lon="13.00015"><time>2020-01-01T10:00:04Z</time></trkpt>
  </trkseg></trk>
</gpx>"""
    inp = tmp_path / "in.gpx"
    out_off = tmp_path / "off.gpx"
    out_on = tmp_path / "on.gpx"
    inp.write_text(xml, encoding="utf-8")
    clean_gpx_file(
        inp,
        out_off,
        max_speed_mps=100.0,
        max_acceleration_mps2=None,
        min_dt_s=1e-3,
        max_iterations=5,
        smooth=False,
        smooth_window=5,
    )
    clean_gpx_file(
        inp,
        out_on,
        max_speed_mps=100.0,
        max_acceleration_mps2=None,
        min_dt_s=1e-3,
        max_iterations=5,
        smooth=True,
        smooth_window=5,
    )
    a = gpxpy.parse(out_off.read_text(encoding="utf-8")).tracks[0].segments[0].points
    b = gpxpy.parse(out_on.read_text(encoding="utf-8")).tracks[0].segments[0].points
    assert abs(a[2].latitude - b[2].latitude) > 1e-9
