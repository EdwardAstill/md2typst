# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`mdtyp` is a Python CLI tool that converts Markdown documents to [Typst](https://typst.app/) format. It uses `markdown-it-py` to parse Markdown into a token stream and then renders each token type into the corresponding Typst syntax. LaTeX math expressions (via `$...$` and `$$...$$`) are translated to Typst math syntax.

## Setup & Commands

This project uses [uv](https://docs.astral.sh/uv/) for dependency management. Requires Python >=3.14.

```bash
# Install dependencies and create virtualenv
uv sync

# Run the CLI
uv run mdtyp input.md                  # writes input.typ
uv run mdtyp input.md -o output.typ    # explicit output path
uv run mdtyp input.md --stdout         # print to stdout
echo "# Hello" | uv run mdtyp          # read from stdin
uv run mdtyp --all                     # convert all .md files in cwd

# Quick smoke test (no test suite exists yet)
uv run python -c "from mdtyp.converter import convert; print(convert('# Hello'))"
```

## Architecture

Three modules, two conversion stages:

1. **`mdtyp/converter.py`** — Markdown → Typst
   - Parses Markdown with `markdown-it-py` (with the `dollarmath` plugin for math).
   - Walks the flat token list via a manual index loop in `_render_tokens()`. Block-level tokens are handled there; inline tokens are dispatched to `_render_inline()`.
   - A `_Ctx` object accumulates the output string and tracks list nesting state (`list_stack`, `item_first_para`).
   - Some block tokens (headings, paragraphs, tables) consume multiple tokens at once by advancing the index manually—be careful when adding new token handlers.

2. **`mdtyp/latex2typst.py`** — LaTeX math → Typst math
   - Called for every `math_inline` and `math_block` token.
   - `latex_to_typst()` applies transformations in a strict pipeline order (each stage assumes prior stages have already run):
     1. **Environments** (`\begin{aligned}`, matrices, cases)
     2. **Structured commands** (`\frac`, `\sqrt`, accents, font commands, `\mathbb`)
     3. **Simple symbol replacements** (`_COMMANDS` list, sorted longest-first to prevent partial matches)
     4. **Script conversion** (`_{...}` → `_(...)`, `^{...}` → `^(...)`)
     5. **Multi-character identifier quoting** (wraps unknown multi-letter identifiers in `"..."` since Typst math treats consecutive letters as separate variables)
   - `_extract_braced()` is the shared helper for parsing balanced `{}`—used by all `_replace_cmd_*` functions.
   - `_TYPST_MATH_IDENTS` is the allowlist of identifiers that should NOT be quoted in stage 5.

3. **`mdtyp/config.py`** — Configuration system
   - `Config` dataclass (with nested `TableConfig`, `BlockquoteConfig`, `HrConfig`, `ImageConfig`, `CodeConfig`, `PageConfig`) holds all style settings with sensible defaults.
   - `load_config(path)` reads a TOML file; returns all-defaults `Config` if no file exists.
   - Default config path: `$XDG_CONFIG_HOME/mdtyp/config.toml` (typically `~/.config/mdtyp/config.toml`).
   - Config is threaded through `convert()` → `_Ctx` → all rendering functions. `_render_inline` receives `config` as its second argument.

4. **`mdtyp/cli.py`** — CLI entry point using [Typer](https://typer.tiangolo.com/). Handles file I/O: reads from a file or stdin, writes to a file (defaulting to `<input>.typ`) or stdout. Loads config via `--config`/`-c` flag or the default path.

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

## Configuration

Config file at `~/.config/mdtyp/config.toml` (or `$XDG_CONFIG_HOME/mdtyp/config.toml`). Override with `--config`/`-c`. All fields are optional — omitted fields use defaults.

```toml
[table]
header_bold = true     # wrap header cells in *...*
stroke = ""            # e.g. "0.5pt" — adds stroke param to #table

[blockquote]
function = "quote"     # Typst function name for blockquotes

[hr]
style = "#line(length: 100%)"   # exact Typst output for ---

[image]
use_figure = true      # false emits bare #image() without #figure wrapper
width = ""             # e.g. "80%" — adds width param to image()

[code]
block_function = ""    # e.g. "sourcecode" — wraps code blocks in #fn(...)

[page]
paper = ""             # e.g. "a4" — default paper size (CLI --paper overrides)
```
