# Markdown Section Byte Statistics — SPEC

## 1. Purpose

Implement a small CLI utility that analyzes a Markdown file and reports the gross byte size of every heading-defined section.

The utility shall parse Markdown structurally with `markdown-it-py`, ignore heading-like text inside fenced code blocks, preserve document order, derive hierarchical dotted paths, group output by structural depth and parent, and measure section sizes against the original file bytes.

## 2. CLI

```text
markdown-stats TARGET
```

`TARGET` is the Markdown file. Write the report to stdout and diagnostics to stderr. Success exits `0`; invalid CLI usage or an unreadable/invalid target exits nonzero.

## 3. Input and byte accounting

Read the target as raw bytes and decode a copy as UTF-8 for parsing. Accept a UTF-8 BOM. Byte counts always refer to original bytes, preserving UTF-8 multibyte characters, LF/CRLF, BOM, and final-newline state. Do not rewrite or normalize the target.

## 4. Parsing and hierarchy

Use CommonMark parsing through `markdown-it-py`. Only parser-recognized ATX/Setext headings create sections; heading-like content in fenced blocks does not.

The shallowest contextual heading is structural level 1. A heading belongs under the nearest preceding heading whose Markdown heading level is lower. Skipped Markdown levels do not create phantom structural levels. Sibling indexes are 1-based and scoped to each parent; paths such as `2.4.1` encode those sibling indexes.

## 5. Gross section size

A section begins at the first byte of its heading source line and extends to, but excludes, the first byte of the next heading at the same or shallower structural depth; otherwise it extends through EOF. Parent gross size therefore includes descendants. Content before the first heading is excluded.

Map parser source lines independently to byte offsets in the original byte stream. Do not derive final byte counts by re-encoding text slices.

## 6. Output

Emit plain text. First list all structural-level-1 headings in document order, then each deeper level grouped by parent, preserving document order.

```text
Heading level 2 — parent 2: Architecture

Path   Bytes     Heading
2.1    14,992    Components
2.2    23,202    Data model
```

Columns are `Path`, `Bytes`, `Heading`. Right-align `Bytes`, use thousands separators, size `Path` and `Bytes` per table, and never truncate heading text. Display parsed heading text without Markdown formatting markers.

If no headings exist, succeed and emit a concise indication.

## 7. Acceptance

Tests shall cover ATX and Setext headings; fenced-block false headings; normal and skipped levels; 1-based scoped paths; gross parent counts; equal/shallower termination; EOF termination; UTF-8, CRLF, BOM, and no-final-newline byte exactness; pre-heading exclusion; output grouping; column order; long headings; and CLI success/error behavior.
