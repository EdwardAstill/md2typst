"""Markdown to Typst converter using markdown-it-py token stream."""

from __future__ import annotations

from markdown_it import MarkdownIt
from markdown_it.token import Token
from mdit_py_plugins.dollarmath import dollarmath_plugin

from mdtyp.config import Config
from mdtyp.latex2typst import latex_to_typst


def convert(md_text: str, config: Config | None = None) -> str:
    md = MarkdownIt().enable("table")
    dollarmath_plugin(md, double_inline=True)
    tokens = md.parse(md_text)
    ctx = _Ctx(config or Config())
    _render_tokens(tokens, ctx)
    return ctx.out.strip() + "\n"


class _Ctx:
    def __init__(self, config: Config):
        self.out = ""
        self.config = config
        self.list_stack: list[str] = []  # "bullet" | "ordered"
        self.item_first_para: bool = False  # True right after list_item_open

    def write(self, s: str):
        self.out += s


def _render_tokens(tokens: list[Token], ctx: _Ctx):
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        t = tok.type

        # --- headings: consume open + inline + close ---
        if t == "heading_open":
            level = int(tok.tag[1])
            prefix = "=" * level
            inline = tokens[i + 1]
            ctx.write(f"\n{prefix} {_render_inline(inline.children or [], ctx.config)}\n\n")
            i += 3
            continue

        # --- paragraphs ---
        elif t == "paragraph_open":
            inline = tokens[i + 1]
            text = _render_inline(inline.children or [], ctx.config)
            if ctx.list_stack and ctx.item_first_para:
                # first paragraph of a list item → emit marker
                depth = len(ctx.list_stack) - 1
                indent = "  " * depth
                kind = ctx.list_stack[-1]
                marker = "+" if kind == "ordered" else "-"
                ctx.write(f"{indent}{marker} {text}\n")
                ctx.item_first_para = False
            elif ctx.list_stack:
                # continuation paragraph inside a list item
                depth = len(ctx.list_stack) - 1
                indent = "  " * (depth + 1)
                ctx.write(f"{indent}{text}\n")
            else:
                ctx.write(text + "\n\n")
            i += 3  # paragraph_open, inline, paragraph_close
            continue

        # --- fenced code blocks ---
        elif t == "fence":
            info = tok.info.strip() if tok.info else ""
            content = tok.content.rstrip("\n")
            fn = ctx.config.code.block_function
            if fn:
                lang_attr = f'lang: "{info}", ' if info else ""
                ctx.write(f"#{fn}({lang_attr}```\n{content}\n```)\n\n")
            elif info:
                ctx.write(f"```{info}\n{content}\n```\n\n")
            else:
                ctx.write(f"```\n{content}\n```\n\n")

        elif t == "code_block":
            content = tok.content.rstrip("\n")
            fn = ctx.config.code.block_function
            if fn:
                ctx.write(f"#{fn}(```\n{content}\n```)\n\n")
            else:
                ctx.write(f"```\n{content}\n```\n\n")

        # --- lists ---
        elif t == "bullet_list_open":
            ctx.list_stack.append("bullet")

        elif t == "ordered_list_open":
            ctx.list_stack.append("ordered")

        elif t in ("bullet_list_close", "ordered_list_close"):
            ctx.list_stack.pop()
            if not ctx.list_stack:
                ctx.write("\n")

        elif t == "list_item_open":
            ctx.item_first_para = True

        elif t == "list_item_close":
            pass

        # --- blockquotes ---
        elif t == "blockquote_open":
            j = i + 1
            content_parts = []
            nesting = 0
            while j < len(tokens):
                inner = tokens[j]
                if inner.type == "blockquote_open":
                    nesting += 1
                elif inner.type == "blockquote_close":
                    if nesting == 0:
                        i = j
                        break
                    nesting -= 1
                elif inner.type == "inline":
                    content_parts.append(_render_inline(inner.children or [], ctx.config))
                j += 1
            body = "\n\n".join(content_parts)
            fn = ctx.config.blockquote.function
            ctx.write(f"#{fn}[\n{body}\n]\n\n")

        elif t == "hr":
            ctx.write(ctx.config.hr.style + "\n\n")

        elif t == "html_block":
            ctx.write(f"/* HTML: {tok.content.strip()} */\n\n")

        # --- math ---
        elif t == "math_block":
            content = latex_to_typst(tok.content.strip())
            ctx.write(f"$ {content} $\n\n")

        # --- tables ---
        elif t == "table_open":
            i, table_out = _render_table(tokens, i, ctx.config)
            ctx.write(table_out)
            continue

        i += 1


def _render_table(tokens: list[Token], start: int, config: Config) -> tuple[int, str]:
    """Consume table tokens and return (new_index, typst_table_string)."""
    alignments: list[str] = []
    header_cells: list[str] = []
    body_rows: list[list[str]] = []
    in_head = False
    in_body = False
    current_row: list[str] = []
    i = start + 1

    while i < len(tokens):
        t = tokens[i].type
        if t == "thead_open":
            in_head = True
        elif t == "thead_close":
            in_head = False
        elif t == "tbody_open":
            in_body = True
        elif t == "tbody_close":
            in_body = False
        elif t == "tr_open":
            current_row = []
        elif t == "tr_close":
            if in_head:
                header_cells = current_row[:]
            elif in_body:
                body_rows.append(current_row[:])
        elif t in ("th_open", "td_open"):
            style = tokens[i].attrGet("style") or ""
            if "left" in style:
                alignments.append("left")
            elif "right" in style:
                alignments.append("right")
            elif "center" in style:
                alignments.append("center")
            elif not in_body or not alignments:
                alignments.append("auto")
        elif t == "inline":
            current_row.append(_render_inline(tokens[i].children or [], config))
        elif t == "table_close":
            i += 1
            break
        i += 1

    cols = len(header_cells) or (len(body_rows[0]) if body_rows else 1)
    col_spec = ", ".join(alignments[:cols])

    lines = ["#table("]
    lines.append(f"  columns: {cols},")
    lines.append(f"  align: ({col_spec},),")
    if config.table.stroke:
        lines.append(f"  stroke: {config.table.stroke},")

    for cell in header_cells:
        if config.table.header_bold:
            lines.append(f"  [*{cell}*],")
        else:
            lines.append(f"  [{cell}],")
    for row in body_rows:
        for cell in row:
            lines.append(f"  [{cell}],")
    lines.append(")\n")

    return i, "\n".join(lines)


def _render_inline(children: list[Token], config: Config) -> str:
    out = ""
    i = 0
    while i < len(children):
        tok = children[i]
        t = tok.type

        if t == "text":
            out += tok.content.replace("$", r"\$")

        elif t == "softbreak":
            out += " "

        elif t == "hardbreak":
            out += "\\\n"

        elif t == "code_inline":
            out += f"`{tok.content}`"

        elif t == "strong_open":
            j = i + 1
            inner = []
            while j < len(children) and children[j].type != "strong_close":
                inner.append(children[j])
                j += 1
            out += f"*{_render_inline(inner, config)}*"
            i = j

        elif t == "em_open":
            j = i + 1
            inner = []
            while j < len(children) and children[j].type != "em_close":
                inner.append(children[j])
                j += 1
            out += f"_{_render_inline(inner, config)}_"
            i = j

        elif t == "s_open":
            j = i + 1
            inner = []
            while j < len(children) and children[j].type != "s_close":
                inner.append(children[j])
                j += 1
            out += f"#strike[{_render_inline(inner, config)}]"
            i = j

        elif t == "link_open":
            href = tok.attrGet("href") or ""
            j = i + 1
            inner = []
            while j < len(children) and children[j].type != "link_close":
                inner.append(children[j])
                j += 1
            label = _render_inline(inner, config)
            out += f'#link("{href}")[{label}]'
            i = j

        elif t == "image":
            src = tok.attrGet("src") or ""
            alt = tok.attrGet("alt") or ""
            img_cfg = config.image
            width_arg = f", width: {img_cfg.width}" if img_cfg.width else ""
            if img_cfg.use_figure:
                out += f'#figure(image("{src}"{width_arg}), caption: [{alt}])'
            else:
                out += f'#image("{src}"{width_arg})'

        elif t == "math_inline":
            out += f"${latex_to_typst(tok.content)}$"

        elif t == "html_inline":
            out += f"/* {tok.content.strip()} */"

        i += 1

    return out
