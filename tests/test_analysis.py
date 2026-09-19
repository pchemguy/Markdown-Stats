from __future__ import annotations

import pytest

from markdown_stats.analysis import analyze_bytes


def by_path(data: bytes):
    return {section.dotted_path: section for section in analyze_bytes(data).sections}


def test_atx_headings_paths_and_document_order() -> None:
    data = b"# A\na\n## A1\nb\n# B\nc\n"
    sections = analyze_bytes(data).sections
    assert [(s.dotted_path, s.heading) for s in sections] == [
        ("1", "A"),
        ("1.1", "A1"),
        ("2", "B"),
    ]


def test_setext_headings_are_detected() -> None:
    data = b"Alpha\n=====\n\nBeta\n----\ny\n"
    sections = analyze_bytes(data).sections
    assert [(s.markdown_level, s.dotted_path, s.heading) for s in sections] == [
        (1, "1", "Alpha"),
        (2, "1.1", "Beta"),
    ]


def test_headings_inside_fences_are_ignored() -> None:
    data = (
        b"# A\n"
        b"```markdown\n"
        b"# fake\n"
        b"fake setext\n"
        b"===========\n"
        b"```\n"
        b"## Real\n"
    )
    sections = analyze_bytes(data).sections
    assert [(s.dotted_path, s.heading) for s in sections] == [
        ("1", "A"),
        ("1.1", "Real"),
    ]


def test_skipped_markdown_levels_do_not_create_phantom_levels() -> None:
    data = b"## Parent\n#### Child\n### Sibling structural level 2\n"
    sections = analyze_bytes(data).sections
    assert [s.dotted_path for s in sections] == ["1", "1.1", "1.2"]
    assert [s.structural_level for s in sections] == [1, 2, 2]


def test_shallower_heading_later_becomes_top_level() -> None:
    data = b"### First\n## Second\n### Child\n"
    sections = analyze_bytes(data).sections
    assert [s.dotted_path for s in sections] == ["1", "2", "2.1"]


def test_sibling_numbering_is_scoped_to_parent() -> None:
    data = b"# A\n## a\n## b\n# B\n## c\n"
    assert [s.dotted_path for s in analyze_bytes(data).sections] == [
        "1", "1.1", "1.2", "2", "2.1"
    ]


def test_gross_byte_counts_include_descendants() -> None:
    data = b"# A\na\n## A1\nb\n## A2\nc\n# B\nd\n"
    sections = by_path(data)
    assert sections["1"].byte_count == data.index(b"# B")
    assert sections["1.1"].byte_count == data.index(b"## A2") - data.index(b"## A1")
    assert sections["1.2"].byte_count == data.index(b"# B") - data.index(b"## A2")
    assert sections["2"].end_byte == len(data)


def test_content_before_first_heading_is_excluded() -> None:
    data = b"preamble\ntext\n# A\nbody\n"
    section = analyze_bytes(data).sections[0]
    assert section.start_byte == data.index(b"# A")
    assert section.byte_count == len(data) - data.index(b"# A")


def test_utf8_counts_original_bytes() -> None:
    data = "# Привет\r\nтекст €\r\n## 子\r\n終\r\n".encode()
    sections = by_path(data)
    child_start = data.index("## 子".encode())
    assert sections["1"].byte_count == len(data)
    assert sections["1.1"].start_byte == child_start
    assert sections["1.1"].byte_count == len(data) - child_start


def test_bom_is_preserved_in_first_heading_section_size() -> None:
    data = b"\xef\xbb\xbf# A\nbody"
    section = analyze_bytes(data).sections[0]
    assert section.start_line == 0
    assert section.start_byte == 0
    assert section.byte_count == len(data)


def test_no_final_newline_ends_exactly_at_eof() -> None:
    data = b"# A\nbody"
    section = analyze_bytes(data).sections[0]
    assert section.end_byte == len(data)
    assert section.byte_count == len(data)


def test_crlf_line_mapping_is_exact() -> None:
    data = b"# A\r\nbody\r\n## B\r\nchild\r\n"
    sections = by_path(data)
    expected = data.index(b"## B")
    assert sections["1.1"].start_byte == expected


def test_empty_heading_is_supported() -> None:
    data = b"#\nbody\n"
    section = analyze_bytes(data).sections[0]
    assert section.heading == ""


def test_inline_formatting_is_removed_from_display_text() -> None:
    data = b"## **Parser** `architecture` and [links](https://example.com)\n"
    section = analyze_bytes(data).sections[0]
    assert section.heading == "Parser architecture and links"


def test_invalid_utf8_is_rejected() -> None:
    with pytest.raises(UnicodeDecodeError):
        analyze_bytes(b"# ok\n\xff")
