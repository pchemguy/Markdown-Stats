# Markdown Section Byte Statistics — SPEC

## 1. Purpose

Implement a small CLI utility that analyzes a Markdown file and reports the gross byte size of every heading-defined section.

The utility shall:

* parse Markdown structurally rather than with regular expressions;
* ignore heading-like text inside fenced code blocks;
* preserve document order;
* derive a hierarchical dotted path for every heading;
* report sections grouped by structural depth and parent;
* measure section sizes against the original file bytes.

Use `markdown-it-py` for Markdown parsing.

## 2. CLI

Invocation:

```text
markdown-stats TARGET
```

`TARGET` is the path to the Markdown file to analyze.

Example:

```text
markdown-stats docs/dev/SPEC.md
```

The report is written to stdout.

Diagnostics are written to stderr.

A successful run exits with status `0`. Invalid CLI usage or an unreadable/invalid target exits nonzero.

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

Output plain text tables.

First emit all structural-level-1 headings in document order.

Then emit structural-level-2 headings, grouped by their parent.

Continue similarly for deeper levels.

Each group has a descriptive header.

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

Deeper example:

```text
Heading level 3 — parent 2.2: Data model

Path    Bytes     Heading
2.2.1    8,817    Records
2.2.2   14,385    Indexes
```

The columns shall appear in this order:

```text
Path   Bytes   Heading
```

`Heading` is last because heading text may be long.

Within each table:

* preserve document order;
* right-align `Bytes`;
* format byte counts with thousands separators;
* size `Path` and `Bytes` columns from the rows in that table;
* do not truncate heading text.

Separate table groups clearly with blank lines.

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
→ render report
```

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
14. headings inside fenced blocks never split sections.
