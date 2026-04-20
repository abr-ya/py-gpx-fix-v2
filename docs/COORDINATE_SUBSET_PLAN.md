# Second CLI: subset by exact coordinate match to a reference track

## Context

[`gpx-clean`](../src/gpx_clean/cli.py) reads one GPX file, filters by speed, acceleration, and duplicate timestamps, and writes the result ([`clean_gpx` / `clean_gpx_file`](../src/gpx_clean/io.py)). The new command **does not replace** that workflow: it is a **separate** console script (e.g. `gpx-clean-subset`) so existing `gpx-clean input -o out` usage stays unchanged.

## Agreed behaviour

The **reference** GPX contains the **same** points as the cleaned track (the same set of coordinates), but **without** timestamps. The output must keep **only** those **source** points whose coordinates **exactly match** a coordinate present in the reference (no nearest-neighbour search, no distance threshold in metres—**lat/lon equality** only).

**Algorithm (single mode):**

- For each paired segment `source.track[i].segments[j]` and `reference.track[i].segments[j]`:
  - Build a **set** of `(latitude, longitude)` pairs from every point in that reference segment (duplicate coordinates in reference collapse to one set entry; sufficient for the “same points” case).
  - Walk **source** points **in original order**; for each point, if its `(lat, lon)` is **in** that set, append it to the output (a copy of the source `GPXTrackPoint` with all fields, including `time`).
- Result: point order follows **source**; output count is at most source count; if reference coordinates are a strict subset of cleaned, the extra points are dropped while timestamps remain on the kept points.

**Tracks and segments:** require the same `tracks` / `segments` structure (same list lengths). On mismatch, raise a clear `ValueError`. A “first track only” shortcut is optional and can be deferred.

**Timestamps:** reference points may omit time (`None` is allowed). For source segments being processed, **every** point must have a timestamp—same policy as [`_validate_times`](../src/gpx_clean/io.py) for the filter path (needed for a consistent “cleaned” contract).

**Floats and “exact match”:** after gpxpy parsing, compare `lat`/`lon` as `float`. **Strict equality** is the default. If XML round-trip causes tiny drift, support an optional CLI **`--coord-epsilon-deg`** (default `0`; e.g. `1e-9` treats a match when `abs(a-b) <= eps` on both axes). README should state that matching is strict by default.

**Empty segments:** if a reference segment has no points, the coordinate set is empty—the corresponding output segment is empty (prefer keeping the empty segment to preserve structure; keep consistent with the rest of the implementation).

## Implementation notes

- [`src/gpx_clean/subset.py`](../src/gpx_clean/subset.py): pure “coordinate set + ordered filter” logic; **no** geodesic library for matching.
- [`src/gpx_clean/io.py`](../src/gpx_clean/io.py): e.g. `subset_gpx_by_reference(gpx_source, gpx_ref, coord_epsilon_deg: float = 0.0) -> SubsetStats`, copy metadata from source, English provenance line: operation name, `coord_epsilon_deg`, trackpoint counts before/after.
- [`src/gpx_clean/cli_subset.py`](../src/gpx_clean/cli_subset.py): `source` (timed cleaned), `-r` / `--reference` (no time), `-o` / `--output`, optional `--coord-epsilon-deg`; refuse identical source and output paths like the main CLI.
- [`pyproject.toml`](../pyproject.toml): add a new `[project.scripts]` entry for the new command.

## Tests

- Two GPX files: source has four timed points; reference has the same lat/lon for two of them—output has two points with the same times and order as those two in source.
- A coordinate that only appears in source is dropped.
- Mismatched segment counts produce an error.

## Documentation

- [`README.md`](../README.md): purpose, reference = same coordinates without time, one-line example.

## Explicitly out of scope

- Modes `align` / `within`, monotonic nearest-neighbour, and **`--max-distance-m`** are **not** used; matching is **coordinate equality** only (plus optional ε in degrees).

## Implementation checklist

1. **subset-core:** Per segment, build reference coordinate set; scan source in order; keep matches; optional `--coord-epsilon-deg`.
2. **io-provenance:** `subset_gpx_file` + provenance in `io.py` (coordinate-subset operation, before/after counts).
3. **cli-entry:** `cli_subset.py` + `project.scripts` in `pyproject.toml`.
4. **tests-readme:** pytest for match/non-match and subset reference; README one-line example.
