# Markdown Section Byte Statistics — SPEC

## 1. Purpose

Implement a small CLI utility that analyzes a Markdown file and reports the gross byte size of every heading-defined section.

The utility shall:

* parse Markdown structurally rather than with regular expressions;
* ignore heading-like text inside fenced code blocks;
* preserve document order;
* derive a hierarchical dotted path for every heading;
* report sections grouped by structural depth and parent;
* support console and Markdown report formats;
* measure section sizes against the original file bytes.

Use `markdown-it-py` for Markdown parsing.

## 2. CLI

Invocation:

```text
markdown-stats TARGET [--format FORMAT]
```

`TARGET` is the path to the Markdown file to analyze.

Example:

```text
markdown-stats docs/dev/SPEC.md
markdown-stats docs/dev/SPEC.md --format md
```

`--format` is optional and accepts these aliases:

* `stdout`, `console`, or `con` — console output; this is the default and preserves the existing behavior;
* `markdown` or `md` — Markdown file output.

In console mode, write the report to stdout.

In Markdown mode, write a sibling report file by replacing the target's final suffix with `.stats.md`. For example:

```text
path/dev.md -> path/dev.stats.md
```

If the target has no suffix, append `.stats.md`, for example `README -> README.stats.md`. Markdown mode shall not write the report to stdout and shall not modify the target file. The generated Markdown file shall be UTF-8 with LF newlines.

Diagnostics are written to stderr.

A successful run exits with status `0`. Invalid CLI usage, an unreadable/invalid target, or failure to write the Markdown report exits nonzero.

## 3. Input handling

Read the target file as raw bytes.

Decode a copy for Markdown parsing as UTF-8. UTF-8 BOM shall be accepted.

Byte counts shall always refer to the original file bytes, not to re-encoded or newline-normalized text.

Therefore byte accounting shall preserve exactly:

* UTF-8 multibyte characters;
* LF versus CRLF line endings;
* a UTF-8 BOM, if present;
* the presence or absence of the final newline.

Do not modify, normalize, or rewrite the target.

## 4. Markdown parsing

Parse the decoded Markdown with `markdown-it-py` using CommonMark-compatible block parsing.

Only parser-recognized heading blocks constitute headings.

In particular, heading-like text inside fenced code blocks shall not create sections.

Support both normal Markdown heading forms recognized by the parser, including ATX and Setext headings.

For each heading retain at least:

* Markdown heading level;
* source start line;
* rendered/plain heading text;
* hierarchical path;
* gross byte count.

## 5. Structural hierarchy

The report hierarchy is based on headings that actually occur in the document, not on an assumption that the document starts at `#`.

The shallowest Markdown heading level present is structural level 1.

A heading belongs beneath the nearest preceding heading having a lower Markdown heading level.

If Markdown heading levels are skipped, do not invent missing intermediate sections.

Example:

```markdown
## Parent
#### Child
```

produces:

```text
1      Parent
1.1    Child
```

The dotted path uses 1-based sibling indexes.

Example:

```text
2.4.1
```

means:

* second structural-level-1 section;
* fourth child of that section;
* first child of that subsection.

## 6. Section boundaries and byte counts

A section begins at the first byte of its heading source line.

Its gross section extends up to, but excludes, the first byte of the next heading that is at the same structural depth or any shallower structural depth.

If no such heading follows, the section extends through EOF.

Therefore a parent's gross byte count includes all descendant subsections.

Example:

```markdown
## A
text

### A1
text

### A2
text

## B
text
```

The sections are:

```text
A   = start of "## A"  through byte before "## B"
A1  = start of "### A1" through byte before "### A2"
A2  = start of "### A2" through byte before "## B"
B   = start of "## B" through EOF
```

Content before the first heading is not reported and is not included in any section.

## 7. Source-position mapping

`markdown-it-py` source maps are line-oriented. Build an independent mapping from source line number to byte offset in the original byte buffer.

The mapping must correctly support:

* LF;
* CRLF;
* a final line without a newline;
* empty lines;
* non-ASCII UTF-8 content.

Use parser-recognized heading start lines together with this byte-offset table to derive exact section byte boundaries.

Do not compute final byte counts by slicing decoded text and calling `.encode()`.

## 8. Output organization

Both output formats use the same logical grouping and row order.

First emit all structural-level-1 headings in document order. Then emit structural-level-2 headings grouped by parent, and continue similarly for deeper levels. Each group has a descriptive header.

The columns shall always appear in this order:

```text
Path   Bytes   Heading
```

`Heading` is last because heading text may be long. Byte counts use thousands separators. Heading text is never truncated.

### 8.1 Console format

`stdout`, `console`, and `con` render plain-text tables to stdout.

Top-level example:

```text
Heading level 1

Path   Bytes     Heading
1      12,481    Introduction
2      38,194    Architecture
3      21,705    Implementation
```

Nested example:

```text
Heading level 2 — parent 2: Architecture

Path   Bytes     Heading
2.1    14,992    Components
2.2    23,202    Data model
```

Within each console table, size `Path` and `Bytes` columns from the rows in that table and right-align `Bytes`. Separate table groups clearly with blank lines.

### 8.2 Markdown format

`markdown` and `md` render a valid Markdown document to the `.stats.md` output file.

Use Markdown headings for group headers, with the Markdown heading level equal to the structural level being reported. Use Markdown pipe tables for all data tables and right-align the `Bytes` column via the table alignment row.

Example:

```markdown
# Heading level 1

| Path | Bytes | Heading |
| :--- | ---: | :--- |
| 1 | 12,481 | Introduction |
| 2 | 38,194 | Architecture |

## Heading level 2 — parent 2: Architecture

| Path | Bytes | Heading |
| :--- | ---: | :--- |
| 2.1 | 14,992 | Components |
| 2.2 | 23,202 | Data model |
```

Escape heading text as required so literal Markdown table delimiters, especially `|`, cannot split a cell.

## 9. Heading text

Use the textual content of the parsed heading for display rather than the raw Markdown heading source.

Inline Markdown syntax should not appear merely because it was used to format the heading.

For example:

```markdown
## **Parser** architecture
```

should display approximately as:

```text
Parser architecture
```

Do not include the Markdown heading marker itself.

## 10. Empty and unusual documents

If the document contains no headings, complete successfully and emit a concise indication that no headings were found.

The implementation shall also handle correctly:

* a single heading;
* heading-level jumps;
* repeated heading text;
* empty headings accepted by the parser;
* fenced blocks containing `#` or Setext-like text;
* headings immediately adjacent to one another;
* Unicode heading text;
* CRLF input;
* a file without a trailing newline.

## 11. Implementation constraints

Keep the utility small and deterministic.

Prefer a straightforward pipeline:

```text
read bytes
→ decode Markdown
→ parse heading tokens
→ build line-to-byte offsets
→ construct heading hierarchy
→ calculate gross section boundaries
→ group rows by structural depth and parent
→ render selected format
→ stdout or .stats.md
```

Keep analysis independent of report rendering so console and Markdown formats consume the same section model and byte counts.

Do not implement Markdown heading recognition manually.

Do not use regular expressions as the authority for heading detection.

Do not add MyST or Sphinx dependencies.

## 12. Acceptance conditions

The implementation is complete when automated tests demonstrate that:

1. ordinary ATX headings are detected in source order;
2. Setext headings are detected;
3. apparent headings inside fenced code blocks are ignored;
4. hierarchy paths are correct for normal and skipped heading levels;
5. sibling numbering is 1-based and scoped to each parent;
6. parent gross byte counts include descendant sections;
7. section boundaries terminate at the next heading of equal or shallower structural depth;
8. final sections terminate exactly at EOF;
9. byte counts are exact for UTF-8, CRLF, BOM, and no-final-newline inputs;
10. content before the first heading is excluded;
11. output groups headings by structural level and parent;
12. output columns are ordered `Path`, `Bytes`, `Heading`;
13. long heading text is not truncated;
14. headings inside fenced blocks never split sections;
15. omitted `--format`, `--format stdout`, `--format console`, and `--format con` all produce the existing console report on stdout;
16. `--format markdown` and `--format md` produce the sibling `.stats.md` file and no report on stdout;
17. Markdown group headers use Markdown heading syntax matching structural level;
18. Markdown reports use valid pipe tables with a right-aligned `Bytes` column and escaped heading-cell delimiters;
19. Markdown output naming replaces the final target suffix with `.stats.md`, or appends `.stats.md` when the target has no suffix;
20. Markdown output does not modify the source target and write failures are reported as errors.
