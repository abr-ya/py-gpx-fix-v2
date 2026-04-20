from __future__ import annotations

import argparse
import sys
from pathlib import Path

from gpx_clean.io import clean_gpx_file


def _parse_max_accel(s: str | None) -> float | None:
    if s is None:
        return 15.0
    v = float(s)
    if v <= 0:
        return None
    return v


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="gpx-clean",
        description="Remove implausible GPS points from GPX running tracks (speed/acceleration gates).",
    )
    p.add_argument("input", type=Path, help="Input GPX file path")
    p.add_argument("-o", "--output", type=Path, required=True, help="Output GPX file path (does not overwrite input by default)")
    p.add_argument(
        "--max-speed",
        type=float,
        default=12.0,
        metavar="MPS",
        help="Maximum plausible speed between consecutive kept points in m/s (default: 12)",
    )
    p.add_argument(
        "--max-acceleration",
        type=str,
        default="15",
        metavar="MPS2_OR_0",
        help="Maximum plausible acceleration in m/s^2, or 0 to disable (default: 15)",
    )
    p.add_argument(
        "--min-dt",
        type=float,
        default=1e-3,
        metavar="SEC",
        help="Minimum delta-time to treat as distinct samples (default: 1e-3)",
    )
    p.add_argument(
        "--max-iterations",
        type=int,
        default=50_000,
        help=(
            "Safety cap on refinement passes per segment (default: 50000). "
            "At most one speed/accel outlier removed per pass."
        ),
    )
    p.add_argument(
        "--enable-smooth",
        action="store_true",
        help="Apply simple moving-average smoothing to lat/lon after filtering (default: off)",
    )
    p.add_argument(
        "--smooth-window",
        type=int,
        default=5,
        help="Odd window size for moving average when --enable-smooth is set (default: 5)",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.input.resolve() == args.output.resolve():
        print("Refusing to read and write the same path; choose a different --output.", file=sys.stderr)
        return 2

    max_accel = _parse_max_accel(args.max_acceleration)
    win = args.smooth_window
    if args.enable_smooth and (win % 2 == 0 or win < 1):
        print("--smooth-window must be a positive odd integer when smoothing is enabled.", file=sys.stderr)
        return 2

    try:
        stats = clean_gpx_file(
            args.input,
            args.output,
            max_speed_mps=args.max_speed,
            max_acceleration_mps2=max_accel,
            min_dt_s=args.min_dt,
            max_iterations=args.max_iterations,
            smooth=args.enable_smooth,
            smooth_window=win,
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
        f"{stats.removed} removed)."
    )
    return 0
