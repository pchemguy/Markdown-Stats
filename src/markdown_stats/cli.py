"""Command-line interface for the ``markdown-stats`` utility.

The CLI supports direct console output and sibling Markdown report generation.
All user-facing failures are normalized to concise diagnostics on stderr.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .analysis import analyze_file
from .report import render_markdown_report, render_report

_CONSOLE_FORMATS = {"stdout", "console", "con"}
_MARKDOWN_FORMATS = {"markdown", "md"}


def build_parser() -> argparse.ArgumentParser:
    """Build and return the command-line argument parser."""

    parser = argparse.ArgumentParser(
        prog="markdown-stats",
        description="Report gross byte counts for Markdown heading-defined sections.",
    )
    parser.add_argument("target", type=Path, help="Markdown file to analyze")
    parser.add_argument(
        "--format",
        choices=["stdout", "console", "con", "markdown", "md"],
        default="stdout",
        help=(
            "output format: stdout/console/con (default) writes the console report "
            "to stdout; markdown/md writes TARGET as a sibling *.stats.md file"
        ),
    )
    return parser


def markdown_output_path(target: Path) -> Path:
    """Derive the sibling Markdown report path for *target*.

    The final suffix, when present, is replaced with ``.stats.md``; otherwise
    ``.stats.md`` is appended to the filename.
    """

    if target.suffix:
        return target.with_suffix(".stats.md")
    return target.with_name(f"{target.name}.stats.md")


def main(argv: list[str] | None = None) -> int:
    """Run the command-line application and return its process exit status.

    Args:
        argv: Optional argument vector excluding the executable name. ``None``
            delegates argument collection to :mod:`argparse`.

    Returns:
        ``0`` on success or ``1`` for file, decoding, or analysis failures.
        Invalid command-line usage is handled by :mod:`argparse` itself.
    """

    args = build_parser().parse_args(argv)

    try:
        analysis = analyze_file(args.target)

        if args.format in _CONSOLE_FORMATS:
            sys.stdout.write(render_report(analysis))
        elif args.format in _MARKDOWN_FORMATS:
            output_path = markdown_output_path(args.target)
            output_path.write_text(
                render_markdown_report(analysis),
                encoding="utf-8",
                newline="\n",
            )
        else:  # pragma: no cover - argparse choices make this unreachable
            raise ValueError(f"unsupported output format: {args.format}")
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        print(f"markdown-stats: error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
