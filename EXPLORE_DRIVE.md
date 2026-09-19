---
url: https://chatgpt.com/c/6aae2289-9dfc-83eb-89a7-2e3f0eecb4e2
---

## 📗 Problem Statement and Lib Selection

> [!NOTE] Prompt
> 
> Of the three libs
> 
>   - mistune
>   - markdown-it-py
>   - myst-parser
> 
> which is best fit for producing per heading markdown section byte counts with proper handling (no splits, of course) of any headings inside fenced blocks. I need to make a table listing every highest level heading with gross byte count in document order, then next level, same thing, and so on. There must be a clear header labelling a block of same-level headings. Within the same level, insert a header, identifying the parent "indexed dotted path": 2.4.1 - second highest-level headings (1-based index), fourth next level within that block, first next level within that block.

Of those three, **`markdown-it-py` is the best fit** for this task.

Its main advantage is exactly what you need: it produces a flat block-token stream in source order, and block tokens carry `map=[line_begin, line_end]` source-line coordinates. Headings are explicit `heading_open` tokens with tags such as `h1`, `h2`, etc.; fenced code is emitted as a single `fence` block token, so heading-looking text inside a fence is never exposed as a heading token. ([Markdown It Py][1])

### Comparison

| Library              | Fit      | Why                                                                                                                                                                                                                                                                             |
| -------------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **`markdown-it-py`** | **Best** | Explicit block token stream, heading level readily available, source line maps built in, CommonMark fence handling, little machinery beyond what you need.                                                                                                                      |
| `mistune`            | Adequate | Fast and has an AST mode, but its public AST interface is more oriented toward parsed structure/rendering than precise source-span processing. You would likely do more bookkeeping to recover exact source boundaries. ([Mistune][2])                                          |
| `myst-parser`        | Overkill | Ultimately uses `markdown-it-py` tokens itself, then adds MyST/Sphinx/docutils machinery. Unless your input is specifically MyST Markdown and you need its directives/roles semantics, you're adding dependencies without gaining anything for this problem. ([MyST Parser][3]) |

So I would use:

```python
from markdown_it import MarkdownIt

md = MarkdownIt("commonmark")
tokens = md.parse(text)
```

and inspect only:

```python
token.type == "heading_open"
```

with:

```python
level = int(token.tag[1])   # h1 -> 1, h2 -> 2, ...
start_line = token.map[0]
```

The parser's `map` is explicitly a `[line_begin, line_end]` source map. ([Markdown It Py][1])

### Your section model

There is one important semantic point in your requirement: I would **not equate "highest level" with H1**.

Suppose the file contains:

```markdown
## First

### A

#### A1

## Second

### B
```

Here the document's highest heading level is `2`, so `##` constitutes hierarchy level 1:

```text
1       First
1.1     A
1.1.1   A1
2       Second
2.1     B
```

That seems to match your description of:

> `2.4.1` = second highest-level heading, fourth next-level heading within it, first next-level heading within that.

You can therefore derive the hierarchy from the **actual heading levels encountered**, rather than assuming `#` must exist.

There is a subtle question around skipped Markdown levels:

```markdown
## Parent
#### Child
```

I would treat `#### Child` as the next structural level and give it:

```text
1.1
```

rather than inventing a nonexistent H3 parent. That produces a hierarchy based on existing sections, which is generally more useful for this report.

### Computing gross byte counts

I would keep parsing and byte accounting separate.

Parse the Markdown as Unicode text so `markdown-it-py` can identify genuine headings. Separately retain the original file bytes and construct a mapping:

```text
source line number -> starting byte offset
```

Then every heading gets an exact byte offset corresponding to the beginning of its Markdown source line.

For a heading at hierarchy depth `D`, its **gross section** should run from:

```text
start of this heading
```

through:

```text
start of the next heading whose hierarchy depth <= D
```

or EOF if there isn't one.

This means a parent's gross size deliberately includes all descendants.

For example:

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

the gross measurements are conceptually:

```text
A   = from "## A"  through just before "## B"
A1  = from "### A1" through just before "### A2"
A2  = from "### A2" through just before "## B"
B   = from "## B" through EOF
```

So you don't need source spans for every Markdown construct. **You only need parser-confirmed heading start positions.**

That is another reason `markdown-it-py` fits particularly well.

### Output organization

I understand your requested table organization as something like:

```text
Heading level 1

Path   Heading                         Bytes
1      Introduction                    12,481
2      Architecture                    38,194
3      Implementation                  21,705


Heading level 2 — parent 1: Introduction

Path   Heading                         Bytes
1.1    Purpose                          4,100
1.2    Scope                            8,381


Heading level 2 — parent 2: Architecture

Path   Heading                         Bytes
2.1    Components                      14,992
2.2    Data model                      23,202


Heading level 3 — parent 2.2: Data model

Path    Heading                        Bytes
2.2.1   Records                         8,817
2.2.2   Indexes                        14,385
```

I think this is cleaner than emitting all level-2 headings in one undifferentiated table, because your requested parent indexed dotted path is explicit.

One adjustment I would make to the terminology: label these **structural levels** rather than Markdown heading levels if skipped heading levels are permitted. For example:

```text
Section level 1
Section level 2 — parent 2
Section level 3 — parent 2.4
```

Then an H4 can legitimately be structural level 2 beneath an H2 without the output misleadingly calling it "heading level 3."

#### One implementation detail worth preserving

Do **not** derive byte counts from:

```python
len(text_slice.encode("utf-8"))
```

unless you've explicitly defined the input as normalized UTF-8 text.

If the requirement really is **file byte counts**, read the file as bytes and calculate offsets against those original bytes. Decode a copy for Markdown parsing. That preserves CRLF vs LF, BOMs, non-ASCII characters, and even whatever exact final-newline state the file has.

`markdown-it-py` then supplies the syntactic truth—"this source line is a heading, this apparent heading is inside a fence"—while the original byte buffer supplies the byte-count truth.

**I would choose `markdown-it-py` without introducing either of the other two.** MyST in particular is built on top of the same markdown-it token machinery, so it would mostly add an abstraction layer you don't need. ([MyST Parser][4])

[1]: https://markdown-it-py.readthedocs.io/en/latest/api/markdown_it.token.html "markdown_it.token module — markdown-it-py"
[2]: https://mistune.lepture.com/en/latest/upgrade.html "Upgrade Guide - Mistune 3.2.1 documentation"
[3]: https://myst-parser.readthedocs.io/en/latest/ "🔎 Overview"
[4]: https://myst-parser.readthedocs.io/en/v0.17.2/api/parsers.html "Parse MyST Markdown"

---
---

## 📗 Output Format

> [!NOTE] Prompt
> 
> ```
> 
> Heading level 1
> 
> Path   Heading                         Bytes
> 1      Introduction                    12,481
> 2      Architecture                    38,194
> 3      Implementation                  21,705
> 
> 
> Heading level 2 — parent 1: Introduction
> 
> Path   Heading                         Bytes
> 1.1    Purpose                          4,100
> 1.2    Scope                            8,381
> 
> 
> Heading level 2 — parent 2: Architecture
> 
> Path   Heading                         Bytes
> 2.1    Components                      14,992
> 2.2    Data model                      23,202
> 
> 
> Heading level 3 — parent 2.2: Data model
> 
> Path    Heading                        Bytes
> 2.2.1   Records                         8,817
> 2.2.2   Indexes                        14,385
> ```
> 
> looks good. But heading can be long, so Bytes goes BEFORE Heading

Agreed. Put the fixed-width numeric field before the potentially long heading text:

```text
Heading level 1

Path   Bytes     Heading
1      12,481    Introduction
2      38,194    Architecture
3      21,705    Implementation


Heading level 2 — parent 1: Introduction

Path   Bytes     Heading
1.1     4,100    Purpose
1.2     8,381    Scope


Heading level 2 — parent 2: Architecture

Path   Bytes     Heading
2.1    14,992    Components
2.2    23,202    Data model


Heading level 3 — parent 2.2: Data model

Path    Bytes     Heading
2.2.1    8,817    Records
2.2.2   14,385    Indexes
```

That also makes alignment easier: `Path` and `Bytes` can have bounded widths, while `Heading` simply consumes the remainder of the line.

---
---

## 📗 SPEC

> [!NOTE] Prompt
> 
> Generate a compact SPEC for this utility to be use with a coding agent. The target is provided via CLI.

Below is a compact implementation-oriented SPEC suitable for handing directly to a coding agent.

``````text
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
``````

One implementation detail I would keep exactly as specified is the distinction between **Markdown heading level** and **structural depth**; that avoids pathological behavior on perfectly valid documents that begin at `##` or skip from `##` to `####`.

---
---

## 📗 Implementation

> [!NOTE] Prompt
> 
> Proceed to full implementation

Implemented the full utility as an installable Python package.

It includes the `markdown-stats TARGET` CLI, `markdown-it-py` parsing, exact original-byte accounting, dotted structural paths, gross parent section sizes, grouped/aligned output, SPEC, README, and automated tests. Fenced-code pseudo-headings are ignored; ATX and Setext headings are supported; skipped Markdown heading levels do not create phantom hierarchy levels.

Validation completed successfully:

```text
21 passed
```

I also smoke-tested both direct source execution and an installed package build using Setuptools.

---
---

## 📗 Markdown Output

> [!NOTE] Prompt
> 
> Extend SPEC, codebase, tests, and docs:  
> Include optional --format flag:  
> `stdout` or `console` or `con` - default - current behaviour.  
> `markdown` or `md` - produce Markdown output (for file path/dev.md produce path/dev.stats.md) with all tables formatted as markdown tables and section headings using markdown headings.

Implemented the format extension across SPEC, code, tests, and README.

The CLI now supports `--format stdout|console|con` for the existing stdout behavior and `--format markdown|md` for Markdown file output. Markdown mode replaces the target’s final suffix with `.stats.md`—for example, `path/dev.md` → `path/dev.stats.md`—uses Markdown headings corresponding to structural depth, and emits proper pipe tables with a right-aligned `Bytes` column.

Additional details covered include suffixless targets, escaping `|` and backslashes in heading table cells, preserving the source file unchanged, UTF-8/LF report output, and propagating report-file write errors. The package version is now `0.2.0`.

Validation:

```text
33 passed
```

I also ran an end-to-end Markdown generation against the project SPEC and verified the generated hierarchy and tables.

---
---

## 📗 Docstrings

> [!NOTE] Prompt
> 
> Add pro docstrings to code modules

Added professional docstrings throughout the codebase, including:

* every Python module;
* public dataclasses and their attributes;
* public properties and functions;
* CLI entry points and path derivation;
* internal parsing/report helpers where their contracts are non-obvious;
* explicit `Args`, `Returns`, and `Raises` sections where useful.

No behavior was changed.

Validation remains clean:

```text
33 passed
```

I also verified that every module, class, and function in `src/markdown_stats` has a docstring.
