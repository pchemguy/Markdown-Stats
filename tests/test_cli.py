from __future__ import annotations

from pathlib import Path

import pytest

from markdown_stats.cli import main, markdown_output_path


def test_cli_success_defaults_to_stdout(tmp_path: Path, capsys) -> None:
    target = tmp_path / "doc.md"
    target.write_bytes(b"# A\nbody\n")
    assert main([str(target)]) == 0
    captured = capsys.readouterr()
    assert "Heading level 1" in captured.out
    assert captured.err == ""
    assert not (tmp_path / "doc.stats.md").exists()


@pytest.mark.parametrize("format_name", ["stdout", "console", "con"])
def test_console_format_aliases_write_stdout(
    format_name: str, tmp_path: Path, capsys
) -> None:
    target = tmp_path / "doc.md"
    target.write_bytes(b"# A\nbody\n")

    assert main([str(target), "--format", format_name]) == 0
    captured = capsys.readouterr()

    assert "Heading level 1" in captured.out
    assert "Path" in captured.out
    assert captured.err == ""
    assert not (tmp_path / "doc.stats.md").exists()


@pytest.mark.parametrize("format_name", ["markdown", "md"])
def test_markdown_format_aliases_write_sibling_stats_file(
    format_name: str, tmp_path: Path, capsys
) -> None:
    target = tmp_path / "dev.md"
    target.write_bytes(b"# A\nbody\n## B\nchild\n")

    assert main([str(target), "--format", format_name]) == 0
    captured = capsys.readouterr()
    output = tmp_path / "dev.stats.md"

    assert captured.out == ""
    assert captured.err == ""
    assert output.exists()
    rendered = output.read_text(encoding="utf-8")
    assert rendered.startswith("# Heading level 1\n")
    assert "| Path | Bytes | Heading |" in rendered
    assert "## Heading level 2 — parent 1: A" in rendered
    assert "| 1.1 |" in rendered


def test_markdown_output_replaces_final_suffix(tmp_path: Path) -> None:
    assert markdown_output_path(tmp_path / "dev.md") == tmp_path / "dev.stats.md"
    assert markdown_output_path(tmp_path / "dev.markdown") == tmp_path / "dev.stats.md"
    assert markdown_output_path(tmp_path / "README") == tmp_path / "README.stats.md"


def test_markdown_format_does_not_modify_source(tmp_path: Path) -> None:
    target = tmp_path / "dev.md"
    original = b"# A\r\nbody\r\n"
    target.write_bytes(original)

    assert main([str(target), "--format", "md"]) == 0

    assert target.read_bytes() == original
    assert (tmp_path / "dev.stats.md").read_bytes().endswith(b"\n")


def test_markdown_format_reports_write_error(tmp_path: Path, capsys) -> None:
    target = tmp_path / "doc.md"
    target.write_bytes(b"# A\n")
    output = tmp_path / "doc.stats.md"
    output.mkdir()

    assert main([str(target), "--format", "md"]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.startswith("markdown-stats: error:")


def test_cli_unreadable_target_is_error(tmp_path: Path, capsys) -> None:
    missing = tmp_path / "missing.md"
    assert main([str(missing)]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.startswith("markdown-stats: error:")
