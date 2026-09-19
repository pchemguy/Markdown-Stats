from __future__ import annotations

from markdown_stats.analysis import analyze_bytes
from markdown_stats.report import render_report


def test_no_headings_report() -> None:
    assert render_report(analyze_bytes(b"plain text\n")) == "No headings found.\n"


def test_report_groups_by_level_and_parent_in_document_order() -> None:
    data = (
        b"# Introduction\nintro\n"
        b"## Purpose\np\n"
        b"## Scope\ns\n"
        b"# Architecture\na\n"
        b"## Components\nc\n"
        b"## Data model\nd\n"
        b"### Records\nr\n"
        b"### Indexes\ni\n"
    )
    report = render_report(analyze_bytes(data))

    assert report.index("Heading level 1") < report.index(
        "Heading level 2 — parent 1: Introduction"
    )
    assert report.index("Heading level 2 — parent 1: Introduction") < report.index(
        "Heading level 2 — parent 2: Architecture"
    )
    assert report.index("Heading level 2 — parent 2: Architecture") < report.index(
        "Heading level 3 — parent 2.2: Data model"
    )
    assert "Path" in report
    header_line = next(line for line in report.splitlines() if line.startswith("Path"))
    assert header_line.index("Bytes") < header_line.index("Heading")
    assert "2.2.1" in report and "Records" in report


def test_bytes_are_thousands_separated_and_right_aligned() -> None:
    data = b"# A\n" + (b"x" * 12_000) + b"\n# B\nq\n"
    report = render_report(analyze_bytes(data))
    assert "12,005" in report


def test_long_heading_is_not_truncated() -> None:
    heading = "A very long heading " * 20
    data = f"# {heading}\nbody\n".encode()
    report = render_report(analyze_bytes(data))
    assert heading.rstrip() in report
