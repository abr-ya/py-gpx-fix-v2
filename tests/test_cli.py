from __future__ import annotations

from pathlib import Path

from gpx_clean.cli import main


def test_cli_refuses_same_input_output(tmp_path):
    p = tmp_path / "x.gpx"
    p.write_text("<gpx></gpx>", encoding="utf-8")
    code = main([str(p), "-o", str(p)])
    assert code == 2


def test_cli_runs_on_sample(tmp_path):
    root = Path(__file__).resolve().parent
    inp = root / "data" / "sample_track.gpx"
    out = tmp_path / "o.gpx"
    code = main([str(inp), "-o", str(out), "--max-speed", "50", "--max-acceleration", "0"])
    assert code == 0
    assert out.is_file()
    text = out.read_text(encoding="utf-8")
    assert "Filtered with gpx-clean" in text
