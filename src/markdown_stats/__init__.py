"""Public API for Markdown section byte statistics.

The package analyzes Markdown source from its original UTF-8 byte stream so that
reported section sizes reflect the file exactly while heading recognition follows
CommonMark parsing semantics.
"""

from .analysis import Analysis, Section, analyze_bytes, analyze_file
from .report import render_markdown_report, render_report

__all__ = [
    "Analysis",
    "Section",
    "analyze_bytes",
    "analyze_file",
    "render_markdown_report",
    "render_report",
]
