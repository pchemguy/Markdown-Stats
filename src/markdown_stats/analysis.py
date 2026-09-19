"""Analyze Markdown heading structure and exact gross section byte sizes.

Markdown syntax is parsed with ``markdown-it-py`` while byte boundaries are
calculated independently from the original source bytes. This separation keeps
heading recognition CommonMark-aware without losing file-level byte fidelity.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from markdown_it import MarkdownIt
from markdown_it.token import Token


@dataclass(slots=True)
class Section:
    """Represent one parser-recognized heading-defined section.

    Attributes:
        markdown_level: Markdown heading level (1 through 6).
        structural_level: Depth in the derived section hierarchy.
        path: One-based sibling indexes forming the section's dotted path.
        heading: Plain display text extracted from the parsed heading.
        start_line: Zero-based source line on which the heading begins.
        start_byte: Inclusive byte offset of the heading's source line.
        end_byte: Exclusive byte offset of the gross section boundary.
    """

    markdown_level: int
    structural_level: int
    path: tuple[int, ...]
    heading: str
    start_line: int
    start_byte: int
    end_byte: int = 0

    @property
    def byte_count(self) -> int:
        """Return the gross section size in original source bytes."""

        return self.end_byte - self.start_byte

    @property
    def dotted_path(self) -> str:
        """Return the hierarchy path as a dot-separated one-based index."""

        return ".".join(str(part) for part in self.path)


@dataclass(slots=True)
class Analysis:
    """Contain the complete section analysis for one Markdown byte stream.

    Attributes:
        sections: Heading-defined sections in source order.
        total_bytes: Length of the unmodified input byte stream.
    """

    sections: list[Section]
    total_bytes: int


def _line_start_offsets(data: bytes) -> list[int]:
    """Return byte offsets for logical line starts in *data*.

    Markdown-it normalizes CRLF and lone CR to LF before block parsing while
    preserving line count, so this scanner recognizes all three line endings.
    """

    starts = [0]
    i = 0
    n = len(data)
    while i < n:
        byte = data[i]
        if byte == 0x0D:  # CR
            i += 1
            if i < n and data[i] == 0x0A:  # CRLF
                i += 1
            starts.append(i)
        elif byte == 0x0A:  # LF
            i += 1
            starts.append(i)
        else:
            i += 1
    return starts


def _plain_heading_text(inline: Token) -> str:
    """Return plain display text from a heading's inline token children.

    Formatting tokens are omitted, inline code contributes its literal content,
    and soft or hard line breaks are normalized to spaces for tabular display.
    """

    children = inline.children or []
    pieces: list[str] = []
    for child in children:
        if child.type in {"text", "code_inline"}:
            pieces.append(child.content)
        elif child.type in {"softbreak", "hardbreak"}:
            pieces.append(" ")
        elif child.type == "image":
            pieces.append(child.content)
        elif child.type == "html_inline":
            # Raw inline HTML is markup, not heading text. Any text represented
            # as separate inline text tokens is retained naturally.
            continue
    return "".join(pieces)


def _iter_headings(tokens: list[Token]) -> Iterable[tuple[int, int, str]]:
    """Yield ``(markdown_level, start_line, display_text)`` in source order."""

    for index, token in enumerate(tokens):
        if token.type != "heading_open":
            continue
        if token.map is None:
            raise ValueError("heading token has no source map")
        try:
            level = int(token.tag.removeprefix("h"))
        except ValueError as exc:  # defensive: markdown-it heading tags are h1..h6
            raise ValueError(f"unexpected heading tag: {token.tag!r}") from exc

        inline = tokens[index + 1] if index + 1 < len(tokens) else None
        if inline is None or inline.type != "inline":
            raise ValueError("heading token is not followed by inline content")
        yield level, token.map[0], _plain_heading_text(inline)


def analyze_bytes(data: bytes) -> Analysis:
    """Analyze UTF-8 Markdown from its original byte representation.

    Args:
        data: Original Markdown file bytes. UTF-8 with or without a BOM is
            accepted.

    Returns:
        An :class:`Analysis` containing all heading-defined sections in source
        order and the original stream length.

    Raises:
        UnicodeDecodeError: If *data* is not valid UTF-8.
        ValueError: If parser source metadata is internally inconsistent with
            the original byte stream.
    """

    text = data.decode("utf-8-sig")
    tokens = MarkdownIt("commonmark").parse(text)
    line_starts = _line_start_offsets(data)

    sections: list[Section] = []
    stack: list[Section] = []
    child_counts: dict[tuple[int, ...], int] = {}

    for markdown_level, start_line, heading in _iter_headings(tokens):
        while stack and stack[-1].markdown_level >= markdown_level:
            stack.pop()

        parent_path = stack[-1].path if stack else ()
        sibling_index = child_counts.get(parent_path, 0) + 1
        child_counts[parent_path] = sibling_index
        path = (*parent_path, sibling_index)

        if start_line >= len(line_starts):
            raise ValueError(
                f"parser source line {start_line} is outside original byte stream"
            )

        section = Section(
            markdown_level=markdown_level,
            structural_level=len(path),
            path=path,
            heading=heading,
            start_line=start_line,
            start_byte=line_starts[start_line],
        )
        sections.append(section)
        stack.append(section)

    total_bytes = len(data)
    for index, section in enumerate(sections):
        end_byte = total_bytes
        for following in sections[index + 1 :]:
            if following.structural_level <= section.structural_level:
                end_byte = following.start_byte
                break
        section.end_byte = end_byte

    return Analysis(sections=sections, total_bytes=total_bytes)


def analyze_file(path: str | Path) -> Analysis:
    """Read and analyze a Markdown file without modifying its bytes.

    Args:
        path: Path to the Markdown source file.

    Returns:
        The analysis produced from the file's exact byte content.

    Raises:
        OSError: If the file cannot be read.
        UnicodeDecodeError: If the file is not valid UTF-8.
        ValueError: If parser source metadata is inconsistent with the input.
    """

    return analyze_bytes(Path(path).read_bytes())
