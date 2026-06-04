"""Unit tests for LaTeX → Typst math translation."""

import pytest

from mdtyp.latex2typst import latex_to_typst


# --- Fractions and roots ---

@pytest.mark.parametrize("latex, expected", [
    (r"\frac{a}{b}", "frac(a, b)"),
    (r"\frac{1}{2}", "frac(1, 2)"),
    (r"\dfrac{x}{y}", "frac(x, y)"),
    (r"\tfrac{a}{b}", "frac(a, b)"),
    (r"\frac{1}{\sqrt{2}}", "frac(1, sqrt(2))"),
    (r"\frac12", "frac(1, 2)"),
    (r"\frac14", "frac(1, 4)"),
    (r"\sqrt{x}", "sqrt(x)"),
    (r"\sqrt3", "sqrt(3)"),
    (r"\sqrt[3]{x}", "root(3, x)"),
    (r"\sqrt{a^2 + b^2}", "sqrt(a^2 + b^2)"),
])
def test_fractions_and_roots(latex: str, expected: str) -> None:
    assert latex_to_typst(latex) == expected


# --- Greek letters ---

@pytest.mark.parametrize("latex, expected", [
    (r"\alpha", "alpha"),
    (r"\beta", "beta"),
    (r"\gamma", "gamma"),
    (r"\pi", "pi"),
    (r"\omega", "omega"),
    (r"\Gamma", "Gamma"),
    (r"\Delta", "Delta"),
    (r"\Omega", "Omega"),
])
def test_greek(latex: str, expected: str) -> None:
    assert latex_to_typst(latex) == expected


# --- Operators and relations ---

@pytest.mark.parametrize("latex, expected", [
    (r"\leq", "<="),
    (r"\le", "<="),
    (r"\geq", ">="),
    (r"\ge", ">="),
    (r"\neq", "!="),
    (r"\approx", "approx"),
    (r"\equiv", "equiv"),
    (r"\sim", "tilde.op"),
    (r"\propto", "prop"),
    (r"\subset", "subset"),
    (r"\subseteq", "subset.eq"),
    (r"\supseteq", "supset.eq"),
    (r"\in", "in"),
    (r"\notin", "in.not"),
    (r"\cup", "union"),
    (r"\cap", "sect"),
    (r"\cdot", "dot"),
    (r"\times", "times"),
    (r"\pm", "plus.minus"),
    (r"\pm1", "plus.minus 1"),
])
def test_operators_and_relations(latex: str, expected: str) -> None:
    assert latex_to_typst(latex) == expected


# --- Arrows ---

@pytest.mark.parametrize("latex, expected", [
    (r"\to", "->"),
    (r"\rightarrow", "->"),
    (r"\leftarrow", "<-"),
    (r"\implies", "=>"),
    (r"\iff", "<=>"),
    (r"\mapsto", "|->"),
])
def test_arrows(latex: str, expected: str) -> None:
    assert latex_to_typst(latex) == expected


# --- Big operators ---

@pytest.mark.parametrize("latex, expected", [
    (r"\sum", "sum"),
    (r"\prod", "product"),
    (r"\int", "integral"),
    (r"\iint", "integral.double"),
    (r"\oint", "integral.cont"),
])
def test_big_operators(latex: str, expected: str) -> None:
    assert latex_to_typst(latex) == expected


# --- Subscripts and superscripts ---

@pytest.mark.parametrize("latex, expected", [
    ("x^2", "x^2"),
    ("x_{12}", "x_(12)"),
    ("x^{2n}", "x^(2n)"),
    ("a_{i,j}^{k+1}", "a_(i,j)^(k+1)"),
    ("x_{B1}", 'x_("B1")'),
    ("x_i^2", "x_i^2"),
    ("B^TDB(s,t)", "B^T D B(s,t)"),
])
def test_scripts(latex: str, expected: str) -> None:
    assert latex_to_typst(latex) == expected


# --- Accents ---

@pytest.mark.parametrize("latex, expected", [
    (r"\hat{x}", "hat(x)"),
    (r"\bar{y}", "macron(y)"),
    (r"\vec{v}", "arrow(v)"),
    (r"\dot{x}", "dot(x)"),
    (r"\ddot{x}", "diaer(x)"),
    (r"\tilde{n}", "tilde(n)"),
    (r"\hat K", "hat(K)"),
    (r"\bar d", "macron(d)"),
    (r"\dot d_n", "dot(d_n)"),
    (r"\ddot d_{n+1}", "diaer(d_(n+1))"),
])
def test_accents(latex: str, expected: str) -> None:
    assert latex_to_typst(latex) == expected


# --- Font commands ---

@pytest.mark.parametrize("latex, expected", [
    (r"\mathbf{F}", "bold(F)"),
    (r"\mathrm{d}", "upright(d)"),
    (r"\mathit{x}", "italic(x)"),
    (r"\mathcal{L}", "cal(L)"),
    (r"\text{if }", '"if "'),
])
def test_font_commands(latex: str, expected: str) -> None:
    assert latex_to_typst(latex) == expected


def test_extensible_arrow_with_label() -> None:
    result = latex_to_typst(r"\text{DOFs}\xrightarrow{N}\text{field}")
    assert result == '"DOFs" arrow.r^(N) "field"'


# --- Blackboard bold ---

@pytest.mark.parametrize("latex, expected", [
    (r"\mathbb{R}", "RR"),
    (r"\mathbb{N}", "NN"),
    (r"\mathbb{Z}", "ZZ"),
    (r"\mathbb{Q}", "QQ"),
    (r"\mathbb{C}", "CC"),
])
def test_mathbb(latex: str, expected: str) -> None:
    assert latex_to_typst(latex) == expected


# --- Environments ---

def test_aligned() -> None:
    latex = r"\begin{aligned} f(x) &= x^2 \\ &= x \cdot x \end{aligned}"
    result = latex_to_typst(latex)
    assert "f(x) = x^2" in result
    assert "\\" in result  # line separator


def test_cases() -> None:
    latex = r"\begin{cases} x^2 & \text{if } x > 0 \\ 0 & \text{otherwise} \end{cases}"
    result = latex_to_typst(latex)
    assert "cases(" in result
    assert '"if "' in result
    assert '"otherwise"' in result


def test_bmatrix() -> None:
    latex = r"\begin{bmatrix} a & b \\ c & d \end{bmatrix}"
    result = latex_to_typst(latex)
    assert result == 'mat(delim: "[", a, b; c, d)'


def test_bmatrix_after_symbol_gets_separator() -> None:
    latex = r"k_e\begin{bmatrix}1&-1\\-1&1\end{bmatrix}"
    result = latex_to_typst(latex)
    assert result == 'k_e mat(delim: "[", 1, -1; -1, 1)'


def test_bmatrix_accepts_single_trailing_backslash_rows() -> None:
    latex = "\\begin{bmatrix}\n1&-1\\\n-1&1\n\\end{bmatrix}"
    result = latex_to_typst(latex)
    assert result == 'mat(delim: "[", 1, -1; -1, 1)'


def test_Bmatrix() -> None:
    latex = r"\begin{Bmatrix} d_f \\ d_s \end{Bmatrix}"
    result = latex_to_typst(latex)
    assert result == 'mat(delim: "{", d_f; d_s)'


def test_pmatrix() -> None:
    latex = r"\begin{pmatrix} 1 & 0 \\ 0 & 1 \end{pmatrix}"
    result = latex_to_typst(latex)
    assert result == 'mat(delim: "(", 1, 0; 0, 1)'


# --- Spacing ---

@pytest.mark.parametrize("latex, expected", [
    (r"\quad", "quad"),
    (r"\qquad", "wide"),
])
def test_spacing(latex: str, expected: str) -> None:
    assert latex_to_typst(latex) == expected


# --- Identifier merging prevention ---

def test_no_merge_i_pi() -> None:
    """i and \\pi should not merge into 'ipi'."""
    result = latex_to_typst(r"i\pi")
    assert result == "i pi"


def test_no_merge_m_mathbf() -> None:
    """m and \\mathbf{a} should not merge into 'mbold(a)'."""
    result = latex_to_typst(r"m\mathbf{a}")
    assert result == "m bold(a)"


def test_thin_space_dx() -> None:
    """\\, followed by dx should not merge into 'thindx'."""
    result = latex_to_typst(r"\,dx")
    assert "thin" in result
    assert '"dx"' in result


def test_subseteq_not_quoted() -> None:
    """subset.eq should not have eq quoted."""
    result = latex_to_typst(r"\subseteq")
    assert result == "subset.eq"


# --- Complex expressions ---

def test_quadratic_formula() -> None:
    latex = r"\frac{-b \pm \sqrt{b^2 - 4ac}}{2a}"
    result = latex_to_typst(latex)
    assert "frac(" in result
    assert "sqrt(" in result
    assert "plus.minus" in result


def test_euler_identity() -> None:
    result = latex_to_typst(r"e^{i\pi} + 1 = 0")
    assert "e^(i pi)" in result


def test_sum_with_limits() -> None:
    result = latex_to_typst(r"\sum_{i=1}^{n} i")
    assert "sum_(i=1)^(n)" in result


# --- Misc symbols ---

@pytest.mark.parametrize("latex, expected", [
    (r"\infty", "infinity"),
    (r"\partial", "diff"),
    (r"\nabla", "nabla"),
    (r"\forall", "forall"),
    (r"\exists", "exists"),
    (r"\emptyset", "nothing"),
])
def test_misc_symbols(latex: str, expected: str) -> None:
    assert latex_to_typst(latex) == expected


# --- Delimiters ---

@pytest.mark.parametrize("latex, expected", [
    (r"\left(", "("),
    (r"\right)", ")"),
    (r"\left[", "["),
    (r"\right]", "]"),
    (r"\{", "{"),
    (r"\}", "}"),
])
def test_delimiters(latex: str, expected: str) -> None:
    assert latex_to_typst(latex) == expected


# --- \not negation ---

@pytest.mark.parametrize("latex, expected", [
    (r"\not\Rightarrow", "arrow.r.double.not"),
    (r"\not\implies", "arrow.r.double.not"),
    (r"\not\Leftarrow", "arrow.l.double.not"),
    (r"\not\Leftrightarrow", "arrow.lr.double.not"),
    (r"\not\in", "in.not"),
    (r"\not\equiv", "eq.not"),
    (r"\not\subseteq", "subset.eq.not"),
    (r"\not =", "eq.not"),
    (r"\not <", "lt.not"),
    (r"\not >", "gt.not"),
])
def test_not_negation(latex: str, expected: str) -> None:
    assert latex_to_typst(latex) == expected


def test_not_in_expression() -> None:
    result = latex_to_typst(r"A \not\subseteq B")
    assert "subset.eq.not" in result


# --- Bare superscript star ---

@pytest.mark.parametrize("latex, expected", [
    ("P^*", "P^ast"),
    ("x^*", "x^ast"),
])
def test_bare_star_superscript(latex: str, expected: str) -> None:
    assert latex_to_typst(latex) == expected


def test_star_super_no_comment_syntax() -> None:
    result = latex_to_typst(r"E \cdot P^*/P")
    assert "^ast" in result
    assert "^*" not in result


# --- {,} thousands-separator grouping ---

@pytest.mark.parametrize("latex, expected", [
    (r"15{,}000", "15,000"),
    (r"1{,}500{,}000", "1,500,000"),
])
def test_grouped_comma(latex: str, expected: str) -> None:
    assert latex_to_typst(latex) == expected
