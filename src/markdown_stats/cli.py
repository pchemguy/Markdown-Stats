"""Command-line interface for markdown-stats."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .analysis import analyze_file
from .report import render_report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="markdown-stats",
        description="Report gross byte counts for Markdown heading-defined sections.",
    )
    parser.add_argument("target", type=Path, help="Markdown file to analyze")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        analysis = analyze_file(args.target)
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        print(f"markdown-stats: error: {exc}", file=sys.stderr)
        return 1

    sys.stdout.write(render_report(analysis))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
