import subprocess
import sys
from pathlib import Path
from typing import Optional

import typer

from mdtyp.config import load_config
from mdtyp.converter import convert


def _compile_pdf(typ_path: Path) -> None:
    """Compile a .typ file to PDF using the typst CLI."""
    try:
        result = subprocess.run(
            ["typst", "compile", str(typ_path)],
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        typer.echo("Error: 'typst' command not found. Install Typst to use --pdf.", err=True)
        raise typer.Exit(1)
    if result.returncode != 0:
        typer.echo(f"typst compile failed:\n{result.stderr}", err=True)
        raise typer.Exit(result.returncode)
    pdf_path = typ_path.with_suffix(".pdf")
    typer.echo(f"Compiled to {pdf_path}", err=True)

app = typer.Typer(help="Convert Markdown documents to Typst.")


def _prepend_page_set(typst_text: str, paper: str) -> str:
    return f'#set page(paper: "{paper}")\n\n' + typst_text


@app.command()
def mdtyp(
    input: Optional[Path] = typer.Argument(
        None,
        help="Markdown file to convert. Reads from stdin if omitted.",
        exists=True,
        dir_okay=False,
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output .typ file. Defaults to <input>.typ, or stdout when reading stdin.",
        dir_okay=False,
    ),
    stdout: bool = typer.Option(
        False,
        "--stdout",
        help="Write to stdout even when an input file is given.",
    ),
    paper: Optional[str] = typer.Option(
        None,
        "--paper",
        "-p",
        help='Paper size, e.g. a4, a5, us-letter. Prepends #set page(paper: "...") to output.',
    ),
    pdf: bool = typer.Option(
        False,
        "--pdf",
        help="Compile the generated .typ file to PDF using typst.",
    ),
    all: bool = typer.Option(
        False,
        "--all",
        "-a",
        help="Convert all .md files in the current directory, each to its own .typ file.",
    ),
    config_path: Optional[Path] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to config TOML file. Defaults to ~/.config/mdtyp/config.toml.",
        exists=True,
        dir_okay=False,
    ),
):
    config = load_config(config_path)
    effective_paper = paper or config.page.paper or None

    if all:
        md_files = sorted(Path(".").glob("*.md"))
        if not md_files:
            typer.echo("No .md files found in the current directory.", err=True)
            raise typer.Exit(1)
        for md_file in md_files:
            typst_text = convert(md_file.read_text(), config)
            if effective_paper:
                typst_text = _prepend_page_set(typst_text, effective_paper)
            dest = md_file.with_suffix(".typ")
            dest.write_text(typst_text)
            typer.echo(f"Written to {dest}", err=True)
            if pdf:
                _compile_pdf(dest)
    elif input is None:
        if sys.stdin.isatty():
            typer.echo("Reading from stdin… (Ctrl-D to finish)", err=True)
        md_text = sys.stdin.read()
        typst_text = convert(md_text, config)
        if effective_paper:
            typst_text = _prepend_page_set(typst_text, effective_paper)
        if output:
            output.write_text(typst_text)
            typer.echo(f"Written to {output}", err=True)
            if pdf:
                _compile_pdf(output)
        elif pdf:
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".typ", delete=False, mode="w") as tmp:
                tmp.write(typst_text)
                tmp_path = Path(tmp.name)
            _compile_pdf(tmp_path)
            pdf_bytes = tmp_path.with_suffix(".pdf").read_bytes()
            sys.stdout.buffer.write(pdf_bytes)
            tmp_path.unlink(missing_ok=True)
            tmp_path.with_suffix(".pdf").unlink(missing_ok=True)
        else:
            sys.stdout.write(typst_text)
    else:
        md_text = input.read_text()
        typst_text = convert(md_text, config)
        if effective_paper:
            typst_text = _prepend_page_set(typst_text, effective_paper)
        if stdout and not pdf:
            sys.stdout.write(typst_text)
        else:
            dest = output or input.with_suffix(".typ")
            dest.write_text(typst_text)
            typer.echo(f"Written to {dest}", err=True)
            if pdf:
                _compile_pdf(dest)


if __name__ == "__main__":
    app()
