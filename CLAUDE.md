# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`md2typst` is a Python CLI tool that converts Markdown documents to [Typst](https://typst.app/) format. It uses `markdown-it-py` to parse Markdown into a token stream and then renders each token type into the corresponding Typst syntax. LaTeX math expressions (via `$...$` and `$$...$$`) are translated to Typst math syntax.

## Setup & Commands

This project uses [uv](https://docs.astral.sh/uv/) for dependency management.

```bash
# Install dependencies and create virtualenv
uv sync

# Run the CLI
uv run md2typst input.md                  # writes input.typ
uv run md2typst input.md -o output.typ    # explicit output path
uv run md2typst input.md --stdout         # print to stdout
echo "# Hello" | uv run md2typst          # read from stdin

# Run tests (no test suite yet — test manually or add pytest)
uv run python -c "from md2typst.converter import convert; print(convert('# Hello'))"
```

## Architecture

The conversion pipeline has two stages:

1. **`md2typst/converter.py`** — Markdown → Typst
   Parses Markdown with `markdown-it-py` (with the `dollarmath` plugin for math). Walks the flat token list produced by `md.parse()` using a manual index loop in `_render_tokens()`. Block-level tokens are handled there; inline tokens are handled recursively by `_render_inline()`. A `_Ctx` object accumulates the output string and tracks list nesting state (`list_stack` and `item_first_para`).

2. **`md2typst/latex2typst.py`** — LaTeX math → Typst math
   Called for every `math_inline` and `math_block` token. The `latex_to_typst()` function applies a pipeline of transformations: environment handling (`\begin{aligned}`, matrices, cases), structured commands (`\frac`, `\sqrt`, accents, font commands), simple symbol replacements (`_COMMANDS` list, sorted longest-first to prevent partial matches), script conversion (`_{...}` → `_(...)`), and finally multi-character identifier quoting (wraps unknown multi-letter identifiers in `"..."` since Typst math treats consecutive letters as separate variables).

3. **`md2typst/cli.py`** — CLI entry point using [Typer](https://typer.tiangolo.com/). Handles file I/O: reads from a file or stdin, writes to a file (defaulting to `<input>.typ`) or stdout.

## Key Markdown → Typst Mappings

| Markdown | Typst |
|---|---|
| `# H1` … `###### H6` | `= H1` … `====== H6` |
| `**bold**` | `*bold*` |
| `_italic_` | `_italic_` |
| `~~strike~~` | `#strike[...]` |
| `[text](url)` | `#link("url")[text]` |
| `![alt](src)` | `#figure(image("src"), caption: [alt])` |
| `> quote` | `#quote[...]` |
| `---` | `#line(length: 100%)` |
| `$...$` / `$$...$$` | `$...$` (with LaTeX→Typst math translation) |
| Tables | `#table(columns: N, align: (...), ...)` |
