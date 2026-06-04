# mdtyp

Convert Markdown documents to [Typst](https://typst.app/) format from the command line, with a built-in interactive file browser.

---

## Installation

Requires Python ≥ 3.14 and [uv](https://docs.astral.sh/uv/).

```bash
uv tool install git+https://github.com/EdwardAstill/mdtyp
```

To compile to PDF (`--pdf` and TUI `p` action), also install [Typst](https://github.com/typst/typst).

---

## Usage

### Interactive browser (TUI)

Run `mdtyp` with no arguments to open the file browser:

```
mdtyp
```

```
┌─ mdtyp ──────────────────────────────────────────┐
│ /home/user/documents                              │
├───────────────────────────────────────────────────┤
│ ▶ projects/                                       │
│ ▶ notes/                                          │
│   readme.md                                       │
│   todo.md                                         │
│   image.png                                       │
├───────────────────────────────────────────────────┤
│ q Quit  o Editor  t → Typst  p → PDF             │
└───────────────────────────────────────────────────┘
```

**Navigation**

| Key | Action |
|---|---|
| `↑` / `↓` or `j` / `k` | Move selection |
| `Enter` | Open folder |
| `←` / `h` / `Backspace` | Go up one level |
| `q` | Quit |

**File actions** (available when a `.md` file is selected)

| Key | Action |
|---|---|
| `o` | Open in `$EDITOR` |
| `t` | Convert to Typst — writes `.typ` beside the source file |
| `p` | Convert to PDF — writes `.typ` then compiles with `typst` |

Hidden files and directories are not shown. Folders are listed before files. Non-Markdown files are visible but have no actions.

---

### CLI

Convert a single file:

```bash
mdtyp input.md              # writes input.typ
mdtyp input.md -o out.typ   # explicit output path
mdtyp input.md --stdout     # print to stdout
mdtyp input.md --pdf        # also compile to PDF with typst
mdtyp input.md --latex      # writes input.tex
```

Convert all `.md` files in the current directory:

```bash
mdtyp --all
mdtyp --all --pdf
mdtyp --all --latex
```

Read from stdin:

```bash
echo "# Hello" | mdtyp
echo "# Hello" | mdtyp -o hello.typ
cat notes.md | mdtyp --stdout
cat notes.md | mdtyp --latex --stdout
```

Set paper size:

```bash
mdtyp input.md --paper a4
mdtyp input.md --paper us-letter
```

Use a custom config file:

```bash
mdtyp input.md --config my-config.toml
```

---

## Markdown → LaTeX output

Use `--latex` to render Markdown to LaTeX instead of Typst:

```bash
mdtyp input.md --latex             # writes input.tex
mdtyp input.md --latex --stdout    # print LaTeX to stdout
mdtyp --all --latex                # convert all .md files to .tex
```

The LaTeX renderer preserves Markdown math as LaTeX math and maps common Markdown features to standard LaTeX constructs, including sections, emphasis, lists, blockquotes, tables, links, images, and verbatim code blocks. Documents that use links, images, or strikethrough may need the usual LaTeX packages such as `hyperref`, `graphicx`, or `ulem` in the surrounding document preamble.

---

## Markdown → Typst mapping

| Markdown | Typst |
|---|---|
| `# H1` … `###### H6` | `= H1` … `====== H6` |
| `**bold**` | `*bold*` |
| `_italic_` | `_italic_` |
| `~~strike~~` | `#strike[...]` |
| `` `code` `` | `` `code` `` |
| `[text](url)` | `#link("url")[text]` |
| `![alt](src)` | `#figure(image("src"), caption: [alt])` |
| `> quote` | `#quote[...]` |
| `---` | `#line(length: 100%)` |
| `$...$` | `$...$` (with LaTeX → Typst math translation) |
| `$$...$$` | `$ ... $` (display math) |
| Tables | `#table(columns: N, ...)` |
| Fenced code blocks | ` ```lang ... ``` ` |

### LaTeX math translation

Math expressions are translated from LaTeX to Typst syntax automatically:

| LaTeX | Typst |
|---|---|
| `\frac{a}{b}` | `frac(a, b)` |
| `\sqrt{x}` | `sqrt(x)` |
| `\alpha`, `\beta`, `\pi` … | `alpha`, `beta`, `pi` … |
| `x_{i}`, `x^{2}` | `x_(i)`, `x^(2)` |
| `\mathbf{F}` | `bold(F)` |
| `\mathbb{R}` | `RR` |
| `\begin{aligned}…\end{aligned}` | Typst aligned block |
| `\begin{pmatrix}…\end{pmatrix}` | Typst matrix |

---

## Configuration

Config file location: `~/.config/mdtyp/config.toml` (or `$XDG_CONFIG_HOME/mdtyp/config.toml`).

All fields are optional — omitted fields use defaults.

```toml
[table]
header_bold = true   # wrap header cells in *...*
stroke = ""          # e.g. "0.5pt" — adds stroke: param to #table

[blockquote]
function = "quote"   # Typst function name used for blockquotes

[hr]
style = "#line(length: 100%)"   # exact Typst output for ---

[image]
use_figure = true    # false emits bare #image() without #figure wrapper
width = ""           # e.g. "80%" — adds width: param to image()

[code]
block_function = ""  # e.g. "sourcecode" — wraps code blocks: #sourcecode[...]

[page]
paper = ""           # default paper size, e.g. "a4" (--paper flag overrides)
```

---

## Development

```bash
# Run tests
uv run pytest tests/ -v

# Update the snapshot test after intentional output changes
uv run mdtyp examples/everything.md -o examples/everything.typ

# Quick smoke test
uv run python -c "from mdtyp.converter import convert; print(convert('# Hello'))"
```

### Architecture

```
mdtyp/
├── cli.py          CLI entry point (Typer) + TUI launch
├── tui.py          Interactive file browser (Textual)
├── converter.py    convert(md_text) → typst_text
├── ctx.py          Ctx: token stream + output accumulator
├── handlers.py     Block-level token handlers
├── inline.py       Inline token rendering
├── latex2typst.py  LaTeX math → Typst math translation
└── config.py       Config dataclass + TOML loader
```

The conversion pipeline:

```
Markdown text
    → markdown-it-py (with dollarmath + strikethrough plugins)
    → token stream
    → Ctx + render_tokens()  [handlers.py / inline.py]
    → latex_to_typst()       [latex2typst.py, math tokens only]
    → Typst text
```
