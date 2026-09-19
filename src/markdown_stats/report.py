"""Render analyzed sections as console text or Markdown reports.

Both renderers share identical grouping semantics: structural levels are emitted
in ascending order and nested levels are partitioned by their immediate parent.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable

from .analysis import Analysis, Section


def _group_sections(
    analysis: Analysis,
) -> list[tuple[int, Section | None, list[Section]]]:
    """Group sections by structural level and parent in report order."""

    by_level: dict[int, list[Section]] = defaultdict(list)
    for section in analysis.sections:
        by_level[section.structural_level].append(section)

    by_path = {section.path: section for section in analysis.sections}
    groups: list[tuple[int, Section | None, list[Section]]] = []

    for level in sorted(by_level):
        sections = by_level[level]
        if level == 1:
            groups.append((level, None, sections))
            continue

        parent_groups: dict[tuple[int, ...], list[Section]] = {}
        for section in sections:
            parent_path = section.path[:-1]
            parent_groups.setdefault(parent_path, []).append(section)

        for parent_path, rows in parent_groups.items():
            groups.append((level, by_path[parent_path], rows))

    return groups


def _group_title(level: int, parent: Section | None) -> str:
    """Return the human-readable title for one report group."""

    if parent is None:
        return "Heading level 1"
    return (
        f"Heading level {level} — parent {parent.dotted_path}: "
        f"{parent.heading}"
    )


def _format_console_table(rows: list[Section]) -> list[str]:
    """Format one section group as aligned plain-text table rows."""

    paths = [row.dotted_path for row in rows]
    sizes = [f"{row.byte_count:,}" for row in rows]
    path_width = max(len("Path"), *(len(value) for value in paths))
    size_width = max(len("Bytes"), *(len(value) for value in sizes))

    lines = [f"{'Path':<{path_width}}   {'Bytes':>{size_width}}   Heading"]
    for row, path, size in zip(rows, paths, sizes, strict=True):
        lines.append(f"{path:<{path_width}}   {size:>{size_width}}   {row.heading}")
    return lines


def _escape_markdown_cell(value: str) -> str:
    """Escape text that would otherwise alter a Markdown table cell."""

    return value.replace("\\", "\\\\").replace("|", "\\|")


def _format_markdown_table(rows: list[Section]) -> list[str]:
    """Format one section group as a Markdown pipe table."""

    lines = [
        "| Path | Bytes | Heading |",
        "| :--- | ---: | :--- |",
    ]
    for row in rows:
        heading = _escape_markdown_cell(row.heading)
        lines.append(f"| {row.dotted_path} | {row.byte_count:,} | {heading} |")
    return lines


def _render_groups(
    analysis: Analysis,
    title: Callable[[int, Section | None], str],
    table: Callable[[list[Section]], list[str]],
) -> list[str]:
    """Render all structural groups using supplied title and table formatters."""

    blocks: list[str] = []
    for level, parent, rows in _group_sections(analysis):
        blocks.append("\n".join([title(level, parent), "", *table(rows)]))
    return blocks


def render_report(analysis: Analysis) -> str:
    """Render an analysis as the aligned plain-text console report.

    Args:
        analysis: Completed Markdown section analysis.

    Returns:
        A newline-terminated report suitable for stdout.
    """

    if not analysis.sections:
        return "No headings found.\n"

    blocks = _render_groups(analysis, _group_title, _format_console_table)
    return "\n\n\n".join(blocks) + "\n"


def render_markdown_report(analysis: Analysis) -> str:
    """Render an analysis as Markdown heading groups and pipe tables.

    Args:
        analysis: Completed Markdown section analysis.

    Returns:
        A newline-terminated Markdown document suitable for ``*.stats.md``.
    """

    if not analysis.sections:
        return "No headings found.\n"

    def markdown_title(level: int, parent: Section | None) -> str:
        return f"{'#' * level} {_group_title(level, parent)}"

    blocks = _render_groups(analysis, markdown_title, _format_markdown_table)
    return "\n\n".join(blocks) + "\n"
