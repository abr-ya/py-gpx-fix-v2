from __future__ import annotations

import argparse
import sys
from pathlib import Path

from gpx_clean.io import subset_gpx_file


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="gpx-clean-subset",
        description=(
            "Keep only trackpoints from a timed GPX whose coordinates appear in a reference GPX "
            "(same track/segment layout; reference may omit timestamps)."
        ),
    )
    p.add_argument("source", type=Path, help="Source GPX with timestamps (e.g. cleaned track)")
    p.add_argument(
        "-r",
        "--reference",
        type=Path,
        required=True,
        help="Reference GPX with the same coordinates (subset allowed); time optional on points",
    )
    p.add_argument("-o", "--output", type=Path, required=True, help="Output GPX path")
    p.add_argument(
        "--coord-epsilon-deg",
        type=float,
        default=0.0,
        metavar="DEG",
        help="Treat lat/lon as matching reference when |Δlat| and |Δlon| are within this (default: 0, strict equality)",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    src = args.source.resolve()
    ref = args.reference.resolve()
    out = args.output.resolve()
    if out == src:
        print("Refusing to write over the source file; choose a different --output.", file=sys.stderr)
        return 2
    if out == ref:
        print("Refusing to write over the reference file; choose a different --output.", file=sys.stderr)
        return 2
    if args.coord_epsilon_deg < 0:
        print("--coord-epsilon-deg must be non-negative.", file=sys.stderr)
        return 2

    try:
        stats = subset_gpx_file(
            args.source,
            args.reference,
            args.output,
            coord_epsilon_deg=args.coord_epsilon_deg,
        )
    except ValueError as e:
        print(str(e), file=sys.stderr)
        return 1
    except OSError as e:
        print(f"I/O error: {e}", file=sys.stderr)
        return 1

    print(
        f"Wrote {args.output} "
        f"({stats.trackpoints_after}/{stats.trackpoints_before} trackpoints kept, "
        f"{stats.removed} dropped)."
    )
    return 0
