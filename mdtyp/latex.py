"""Markdown to LaTeX converter using markdown-it-py token stream."""

from __future__ import annotations

from collections.abc import Callable

from markdown_it import MarkdownIt
from markdown_it.token import Token
from mdit_py_plugins.dollarmath import dollarmath_plugin

_LATEX_ESCAPE = str.maketrans({
    "\\": r"\textbackslash{}",
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
})

_HEADING_COMMANDS = {
    1: "section",
    2: "subsection",
    3: "subsubsection",
    4: "paragraph",
    5: "subparagraph",
    6: "subparagraph",
}


class _LatexCtx:
    """Accumulate LaTeX output while walking a markdown-it token stream."""

    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.i = 0
        self._parts: list[str] = []
        self.list_stack: list[str] = []
        self.item_first_para = False

    def current(self) -> Token:
        """Return the current token."""
        return self.tokens[self.i]

    def peek(self, offset: int = 1) -> Token | None:
        """Return a token relative to the current index, if it exists."""
        idx = self.i + offset
        return self.tokens[idx] if idx < len(self.tokens) else None

    def advance(self, n: int = 1) -> None:
        """Move the current token index forward."""
        self.i += n

    def has_more(self) -> bool:
        """Return whether there are tokens left to render."""
        return self.i < len(self.tokens)

    @property
    def out(self) -> str:
        """Return all output written so far."""
        return "".join(self._parts)

    def write(self, text: str) -> None:
        """Append text to the rendered output."""
        self._parts.append(text)

    def sub_context(self, tokens: list[Token]) -> _LatexCtx:
        """Create a child context for recursively rendered blocks."""
        return _LatexCtx(tokens)


# Handler signature: (children, index) -> (rendered_string, new_index)
_InlineHandler = Callable[[list[Token], int], tuple[str, int]]
_BlockHandler = Callable[[_LatexCtx], None]


def convert_to_latex(md_text: str) -> str:
    """Convert Markdown text to LaTeX markup."""
    md = MarkdownIt().enable("table").enable("strikethrough")
    dollarmath_plugin(md, double_inline=True)
    tokens = md.parse(md_text)
    ctx = _LatexCtx(tokens)
    _render_tokens(ctx)
    return ctx.out.strip() + "\n"


def escape_latex(text: str) -> str:
    """Escape characters that have special meaning in LaTeX text mode."""
    return text.translate(_LATEX_ESCAPE)


def _escape_braced_argument(text: str) -> str:
    """Escape only the characters that would break a LaTeX braced argument."""
    return text.replace("\\", r"\textbackslash{}").replace("{", r"\{").replace("}", r"\}")


def _collect_until(
    children: list[Token], start: int, close_type: str,
) -> tuple[list[Token], int]:
    """Collect inline tokens until close_type is reached."""
    j = start
    inner: list[Token] = []
    while j < len(children) and children[j].type != close_type:
        inner.append(children[j])
        j += 1
    return inner, j


def _render_inline(children: list[Token]) -> str:
    """Render a list of inline tokens to LaTeX markup."""
    out = ""
    i = 0
    while i < len(children):
        tok = children[i]
        handler = _INLINE_HANDLERS.get(tok.type)
        if handler:
            result, i = handler(children, i)
            out += result
        else:
            i += 1
    return out


def _handle_text(children: list[Token], i: int) -> tuple[str, int]:
    return escape_latex(children[i].content), i + 1


def _handle_softbreak(children: list[Token], i: int) -> tuple[str, int]:
    return " ", i + 1


def _handle_hardbreak(children: list[Token], i: int) -> tuple[str, int]:
    return "\\\\\n", i + 1


def _handle_code_inline(children: list[Token], i: int) -> tuple[str, int]:
    return f"\\texttt{{{escape_latex(children[i].content)}}}", i + 1


def _handle_math_inline(children: list[Token], i: int) -> tuple[str, int]:
    return f"${children[i].content}$", i + 1


def _handle_html_inline(children: list[Token], i: int) -> tuple[str, int]:
    return f"% HTML: {children[i].content.strip()}", i + 1


def _handle_image(children: list[Token], i: int) -> tuple[str, int]:
    tok = children[i]
    src = _escape_braced_argument(str(tok.attrGet("src") or ""))
    alt = escape_latex(tok.content or "")
    caption = f"\n\\caption{{{alt}}}" if alt else ""
    return (
        "\\begin{figure}[h]\n"
        "\\centering\n"
        f"\\includegraphics{{{src}}}"
        f"{caption}\n"
        "\\end{figure}",
        i + 1,
    )


def _handle_strong(children: list[Token], i: int) -> tuple[str, int]:
    inner, j = _collect_until(children, i + 1, "strong_close")
    content = _render_inline(inner)
    return (f"\\textbf{{{content}}}" if content else ""), j + 1


def _handle_em(children: list[Token], i: int) -> tuple[str, int]:
    inner, j = _collect_until(children, i + 1, "em_close")
    content = _render_inline(inner)
    return (f"\\emph{{{content}}}" if content else ""), j + 1


def _handle_strikethrough(children: list[Token], i: int) -> tuple[str, int]:
    inner, j = _collect_until(children, i + 1, "s_close")
    return f"\\sout{{{_render_inline(inner)}}}", j + 1


def _handle_link(children: list[Token], i: int) -> tuple[str, int]:
    href = _escape_braced_argument(str(children[i].attrGet("href") or ""))
    inner, j = _collect_until(children, i + 1, "link_close")
    label = _render_inline(inner)
    return f"\\href{{{href}}}{{{label}}}", j + 1


_INLINE_HANDLERS: dict[str, _InlineHandler] = {
    "text": _handle_text,
    "softbreak": _handle_softbreak,
    "hardbreak": _handle_hardbreak,
    "code_inline": _handle_code_inline,
    "math_inline": _handle_math_inline,
    "html_inline": _handle_html_inline,
    "image": _handle_image,
    "strong_open": _handle_strong,
    "em_open": _handle_em,
    "s_open": _handle_strikethrough,
    "link_open": _handle_link,
}


def _handle_heading(ctx: _LatexCtx) -> None:
    level = int(ctx.current().tag[1])
    command = _HEADING_COMMANDS[level]
    inline_tok = ctx.peek()
    content = _render_inline(inline_tok.children or []) if inline_tok else ""
    ctx.write(f"\\{command}{{{content}}}\n\n")
    ctx.advance(3)


def _handle_paragraph(ctx: _LatexCtx) -> None:
    inline_tok = ctx.peek()
    text = _render_inline(inline_tok.children or []) if inline_tok else ""
    if ctx.list_stack:
        prefix = "" if ctx.item_first_para else "\n"
        ctx.write(f"{prefix}{text}\n")
        ctx.item_first_para = False
    else:
        ctx.write(text + "\n\n")
    ctx.advance(3)


def _handle_fence(ctx: _LatexCtx) -> None:
    content = ctx.current().content.rstrip("\n")
    ctx.write(f"\\begin{{verbatim}}\n{content}\n\\end{{verbatim}}\n\n")
    ctx.advance()


def _handle_code_block(ctx: _LatexCtx) -> None:
    content = ctx.current().content.rstrip("\n")
    ctx.write(f"\\begin{{verbatim}}\n{content}\n\\end{{verbatim}}\n\n")
    ctx.advance()


def _handle_bullet_list_open(ctx: _LatexCtx) -> None:
    ctx.list_stack.append("bullet")
    ctx.write("\\begin{itemize}\n")
    ctx.advance()


def _handle_ordered_list_open(ctx: _LatexCtx) -> None:
    ctx.list_stack.append("ordered")
    ctx.write("\\begin{enumerate}\n")
    ctx.advance()


def _handle_list_close(ctx: _LatexCtx) -> None:
    list_type = ctx.list_stack.pop()
    env = "enumerate" if list_type == "ordered" else "itemize"
    ctx.write(f"\\end{{{env}}}\n")
    if not ctx.list_stack:
        ctx.write("\n")
    ctx.advance()


def _handle_list_item_open(ctx: _LatexCtx) -> None:
    ctx.item_first_para = True
    ctx.write("\\item ")
    ctx.advance()


def _handle_list_item_close(ctx: _LatexCtx) -> None:
    ctx.advance()


def _handle_blockquote(ctx: _LatexCtx) -> None:
    j = ctx.i + 1
    nesting = 0
    inner_tokens = []
    while j < len(ctx.tokens):
        tok = ctx.tokens[j]
        if tok.type == "blockquote_open":
            nesting += 1
        elif tok.type == "blockquote_close":
            if nesting == 0:
                break
            nesting -= 1
        inner_tokens.append(tok)
        j += 1
    inner_ctx = ctx.sub_context(inner_tokens)
    _render_tokens(inner_ctx)
    body = inner_ctx.out.strip()
    ctx.write(f"\\begin{{quote}}\n{body}\n\\end{{quote}}\n\n")
    ctx.i = j + 1


def _handle_hr(ctx: _LatexCtx) -> None:
    ctx.write(r"\noindent\rule{\linewidth}{0.4pt}" + "\n\n")
    ctx.advance()


def _handle_html_block(ctx: _LatexCtx) -> None:
    ctx.write(f"% HTML: {ctx.current().content.strip()}\n\n")
    ctx.advance()


def _handle_math_block(ctx: _LatexCtx) -> None:
    content = ctx.current().content.strip()
    ctx.write(f"\\[\n{content}\n\\]\n\n")
    ctx.advance()


def _handle_table(ctx: _LatexCtx) -> None:
    alignments, header_cells, body_rows = _parse_table_data(ctx)
    ctx.write(_format_table(alignments, header_cells, body_rows))


def _parse_table_data(
    ctx: _LatexCtx,
) -> tuple[list[str], list[str], list[list[str]]]:
    """Parse table tokens from ctx, advancing past them."""
    alignments: list[str] = []
    header_cells: list[str] = []
    body_rows: list[list[str]] = []
    in_head = False
    in_body = False
    current_row: list[str] = []
    ctx.advance()

    while ctx.has_more():
        tok = ctx.current()
        token_type = tok.type
        if token_type == "thead_open":
            in_head = True
        elif token_type == "thead_close":
            in_head = False
        elif token_type == "tbody_open":
            in_body = True
        elif token_type == "tbody_close":
            in_body = False
        elif token_type == "tr_open":
            current_row = []
        elif token_type == "tr_close":
            if in_head:
                header_cells = current_row[:]
            elif in_body:
                body_rows.append(current_row[:])
        elif token_type in ("th_open", "td_open"):
            style = str(tok.attrGet("style") or "")
            if "right" in style:
                alignments.append("r")
            elif "center" in style:
                alignments.append("c")
            elif not in_body or not alignments:
                alignments.append("l")
        elif token_type == "inline":
            current_row.append(_render_inline(tok.children or []))
        elif token_type == "table_close":
            ctx.advance()
            break
        ctx.advance()

    return alignments, header_cells, body_rows


def _format_table(
    alignments: list[str], header_cells: list[str], body_rows: list[list[str]],
) -> str:
    """Format parsed table data into a LaTeX tabular environment."""
    cols = len(header_cells) or (len(body_rows[0]) if body_rows else 1)
    col_spec = "".join(alignments[:cols]) or "l" * cols
    lines = [f"\\begin{{tabular}}{{{col_spec}}}"]
    if header_cells:
        header = " & ".join(f"\\textbf{{{cell}}}" if cell else "" for cell in header_cells)
        lines.append(header + r" \\")
        lines.append(r"\hline")
    for row in body_rows:
        lines.append(" & ".join(row) + r" \\")
    lines.append(r"\end{tabular}")
    return "\n".join(lines) + "\n\n"


_BLOCK_HANDLERS: dict[str, _BlockHandler] = {
    "heading_open": _handle_heading,
    "paragraph_open": _handle_paragraph,
    "fence": _handle_fence,
    "code_block": _handle_code_block,
    "bullet_list_open": _handle_bullet_list_open,
    "ordered_list_open": _handle_ordered_list_open,
    "bullet_list_close": _handle_list_close,
    "ordered_list_close": _handle_list_close,
    "list_item_open": _handle_list_item_open,
    "list_item_close": _handle_list_item_close,
    "blockquote_open": _handle_blockquote,
    "hr": _handle_hr,
    "html_block": _handle_html_block,
    "math_block": _handle_math_block,
    "table_open": _handle_table,
}


def _render_tokens(ctx: _LatexCtx) -> None:
    """Process block-level tokens by dispatching to registered handlers."""
    while ctx.has_more():
        handler = _BLOCK_HANDLERS.get(ctx.current().type)
        if handler:
            handler(ctx)
        else:
            ctx.advance()
