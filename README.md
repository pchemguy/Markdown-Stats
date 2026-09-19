# Markdown Stats

A small CLI utility that reports the **gross byte size** of each Markdown heading-defined section. Parent section sizes include all descendant sections. Heading-looking text inside fenced code blocks is ignored because headings are recognized by `markdown-it-py`, not by regular expressions.

> [!IMPORTANT]
> 
> **AI-Assisted Development Disclosure**
> 
> This project has been developed with extensive generative-AI assistance. Assistance covered project exploration, design discussion, specification development, implementation, testing, technical review, and documentation. See [AI_DISCLOSURE.md](AI_DISCLOSURE.md) for further details. Responsibility for the published software remains with the maintainer.

## Install

```console
python -m pip install .
```

## Use

```console
markdown-stats TARGET [--format FORMAT]
```

For example:

```console
markdown-stats docs/dev/SPEC.md
markdown-stats docs/dev/SPEC.md --format md
```

`--format` accepts:

- `stdout`, `console`, or `con` — default console output to stdout;
- `markdown` or `md` — write a sibling Markdown report file.

For Markdown output, the target's final suffix is replaced with `.stats.md`:

```text
path/dev.md -> path/dev.stats.md
```

A suffixless target such as `README` produces `README.stats.md`. Markdown mode writes no report to stdout and does not modify the source file.

## Console output

Console output is grouped first by structural heading level and then by parent:

```text
Heading level 1

Path   Bytes   Heading
1      12,481   Introduction
2      38,194   Architecture


Heading level 2 — parent 2: Architecture

Path   Bytes   Heading
2.1    14,992   Components
2.2    23,202   Data model
```

The console renderer sizes `Path` and `Bytes` columns to each table and right-aligns byte counts.

## Markdown output

Markdown output uses Markdown headings for group headers and pipe tables for data. The group heading level matches the structural level being reported:

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

Literal Markdown table delimiters in heading text are escaped so they remain in a single `Heading` cell.

## Semantics

The hierarchy is based on headings actually present in the document. It does not require `#` headings and does not invent missing levels. Thus:

```markdown
## Parent
#### Child
```

produces paths `1` and `1.1`.

A section starts at the first byte of its heading source line and ends just before the next heading at the same structural depth or a shallower one, or at EOF. Counts are taken from the original file bytes, preserving UTF-8 byte width, BOM, CRLF/LF, and final-newline state.

Content before the first heading is not reported.

## Development

```console
pytest
```
