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

## Limitations

- **Times required** on every trackpoint used for filtering.
- **gpxpy** may not round-trip every vendor XML extension.

## Tests

```bash
pytest
```
