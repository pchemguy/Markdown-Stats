from __future__ import annotations

from pathlib import Path

from markdown_stats.cli import main


def test_cli_success(tmp_path: Path, capsys) -> None:
    target = tmp_path / "doc.md"
    target.write_bytes(b"# A\nbody\n")
    assert main([str(target)]) == 0
    captured = capsys.readouterr()
    assert "Heading level 1" in captured.out
    assert captured.err == ""


def test_cli_unreadable_target_is_error(tmp_path: Path, capsys) -> None:
    missing = tmp_path / "missing.md"
    assert main([str(missing)]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.startswith("markdown-stats: error:")
