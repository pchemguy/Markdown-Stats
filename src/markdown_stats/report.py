"""Plain-text report rendering."""

from __future__ import annotations

from collections import defaultdict

from .analysis import Analysis, Section


def _format_table(rows: list[Section]) -> list[str]:
    paths = [row.dotted_path for row in rows]
    sizes = [f"{row.byte_count:,}" for row in rows]
    path_width = max(len("Path"), *(len(value) for value in paths))
    size_width = max(len("Bytes"), *(len(value) for value in sizes))

    lines = [
        f"{'Path':<{path_width}}   {'Bytes':>{size_width}}   Heading"
    ]
    for row, path, size in zip(rows, paths, sizes, strict=True):
        lines.append(
            f"{path:<{path_width}}   {size:>{size_width}}   {row.heading}"
        )
    return lines


def render_report(analysis: Analysis) -> str:
    """Render sections by structural level and parent, preserving source order."""

    if not analysis.sections:
        return "No headings found.\n"

    by_level: dict[int, list[Section]] = defaultdict(list)
    for section in analysis.sections:
        by_level[section.structural_level].append(section)

    by_path = {section.path: section for section in analysis.sections}
    blocks: list[str] = []

    for level in sorted(by_level):
        sections = by_level[level]
        if level == 1:
            lines = ["Heading level 1", "", *_format_table(sections)]
            blocks.append("\n".join(lines))
            continue

        groups: dict[tuple[int, ...], list[Section]] = {}
        for section in sections:
            parent_path = section.path[:-1]
            groups.setdefault(parent_path, []).append(section)

        for parent_path, rows in groups.items():
            parent = by_path[parent_path]
            header = (
                f"Heading level {level} — parent {parent.dotted_path}: "
                f"{parent.heading}"
            )
            blocks.append("\n".join([header, "", *_format_table(rows)]))

    return "\n\n\n".join(blocks) + "\n"
