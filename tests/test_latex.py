"""Unit tests for the Markdown → LaTeX converter."""

from mdtyp.latex import convert_to_latex


# --- Blocks ---


def test_heading() -> None:
    result = convert_to_latex("# Heading")
    assert "\\section{Heading}" in result


def test_unordered_list() -> None:
    result = convert_to_latex("- one\n- two")
    assert "\\begin{itemize}" in result
    assert "\\item one" in result
    assert "\\item two" in result
    assert "\\end{itemize}" in result


def test_ordered_list() -> None:
    result = convert_to_latex("1. one\n2. two")
    assert "\\begin{enumerate}" in result
    assert "\\item one" in result
    assert "\\item two" in result
    assert "\\end{enumerate}" in result


def test_blockquote() -> None:
    result = convert_to_latex("> quoted")
    assert "\\begin{quote}\nquoted\n\\end{quote}" in result


def test_table() -> None:
    md = "| A | B |\n|---|:--:|\n| 1 | 2 |"
    result = convert_to_latex(md)
    assert "\\begin{tabular}{lc}" in result
    assert "\\textbf{A} & \\textbf{B}" in result
    assert "1 & 2" in result


# --- Inline formatting ---


def test_inline_formatting() -> None:
    result = convert_to_latex("**bold** _em_ ~~gone~~ `code`")
    assert "\\textbf{bold}" in result
    assert "\\emph{em}" in result
    assert "\\sout{gone}" in result
    assert "\\texttt{code}" in result


def test_link_and_image() -> None:
    result = convert_to_latex("[site](https://example.com)\n\n![Alt](image.png)")
    assert "\\href{https://example.com}{site}" in result
    assert "\\includegraphics{image.png}" in result
    assert "\\caption{Alt}" in result


# --- Math and escaping ---


def test_math_is_preserved() -> None:
    result = convert_to_latex("$\\frac{1}{2}$\n\n$$\nx^2\n$$")
    assert "$\\frac{1}{2}$" in result
    assert "\\[\nx^2\n\\]" in result


def test_escape_special_chars() -> None:
    result = convert_to_latex("# $ & % _ { }")
    assert "\\$" in result
    assert "\\&" in result
    assert "\\%" in result
    assert "\\_" in result
    assert "\\{" in result
    assert "\\}" in result
