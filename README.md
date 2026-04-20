# gpx-clean

Removes **implausible GPS trackpoints** from GPX files (running-oriented): **speed** and **optional acceleration** limits between consecutive kept points, plus **duplicate timestamps**. Preserves metadata and appends **provenance** to the GPX `<description>`.

Specification snapshot: [docs/PLAN.md](docs/PLAN.md).

## Algorithm

For each track segment (points need **timestamps**):

1. Geodesic distance and \(\Delta t\) between consecutive kept points.
2. Drop later point of pairs with \(\Delta t \le\) `--min-dt` (batch).
3. Drop at most one point per pass for speed \> `--max-speed` or |accel| \> `--max-acceleration` (or disable accel with `--max-acceleration 0`).
4. Repeat until stable or `--max-iterations`.

Optional **`--enable-smooth`**: moving average on lat/lon **after** filtering (numpy only). Default **off**.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

After pulling changes, run `pip install -e ".[dev]"` again so new console scripts (e.g. `gpx-clean-subset`) appear under `.venv/bin`. Use a shell with the venv activated (`source .venv/bin/activate`), or call the module directly (see below).

## CLI

**Arguments**

| Option | Role |
|--------|------|
| **`input`** | Path to the source GPX file. |
| **`-o` / `--output`** | Path for the written GPX (must differ from `input`). |
| **`--max-speed`** | Upper bound on speed (m/s) between **consecutive kept** points. Segments use geodesic distance and timestamps. Default `12`. |
| **`--max-acceleration`** | Upper bound on \|acceleration\| (m/s²) using the same consecutive-kept pairs. Use **`0`** to turn the acceleration check off (speed and duplicate-time rules still apply). Default `15`. |
| **`--min-dt`** | Minimum \(\Delta t\) (seconds) between samples treated as distinct. Pairs with \(\Delta t \le\) this value are handled as **duplicate timestamps** (the later point is dropped in a batch step). Default `1e-3`. |
| **`--max-iterations`** | Maximum filter passes per segment (each pass removes **at most one** point for speed/accel). Stops earlier when nothing changes. Default `50000`. |
| **`--enable-smooth`** | If set, applies a simple moving average to latitude/longitude **after** filtering. Default: off. |
| **`--smooth-window`** | Window size for that average; must be a **positive odd** integer when `--enable-smooth` is used (e.g. `5`, `7`). Default `5`; ignored for smoothing until you pass `--enable-smooth`. |

**Examples**

Typical run (speed + acceleration, no smoothing):

```bash
gpx-clean input.gpx -o cleaned.gpx --max-speed 12 --max-acceleration 15
```

All explicit knobs, including post-filter smoothing:

```bash
gpx-clean input.gpx -o cleaned.gpx --max-speed 12 --max-acceleration 15 --min-dt 0.001 --max-iterations 50000 --enable-smooth --smooth-window 5
```

Same as above but **only** the speed gate (no acceleration limit):

```bash
gpx-clean input.gpx -o cleaned.gpx --max-speed 12 --max-acceleration 0 --min-dt 0.001 --max-iterations 50000 --enable-smooth --smooth-window 7
```

Output GPX gets an English provenance line and `filtered` appended to `<keywords>`.

## Coordinate subset (`gpx-clean-subset`)

Use this when you have a **timed** GPX (e.g. `cleaned.gpx`) and a **reference** GPX with the **same** lat/lon points (possibly a subset) but **without** timestamps. The command keeps only source trackpoints whose coordinates appear in the reference segment-by-segment; **track and segment counts must match** between the two files. Matching is **strict** by default (`--coord-epsilon-deg 0`); set a small epsilon if XML round-trip shifts floats slightly.

Design: [docs/COORDINATE_SUBSET_PLAN.md](docs/COORDINATE_SUBSET_PLAN.md).

```bash
gpx-clean-subset cleaned.gpx -r reference_no_time.gpx -o cleaned2.gpx --coord-epsilon-deg 0
```

If the shell reports “command not found”, activate `.venv` and reinstall as above, or run:

```bash
python -m gpx_clean.cli_subset cleaned.gpx -r reference_no_time.gpx -o cleaned2.gpx --coord-epsilon-deg 0
```

The output appends an English provenance line and adds `subset` to `<keywords>`.

## Limitations

- **Times required** on every trackpoint used for filtering.
- **gpxpy** may not round-trip every vendor XML extension.

## Tests

```bash
pytest
```
