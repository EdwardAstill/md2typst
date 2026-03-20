import sys
from pathlib import Path
from typing import Optional

import typer

from mdtyp.config import load_config
from mdtyp.converter import convert

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
        else:
            sys.stdout.write(typst_text)
    else:
        md_text = input.read_text()
        typst_text = convert(md_text, config)
        if effective_paper:
            typst_text = _prepend_page_set(typst_text, effective_paper)
        if stdout:
            sys.stdout.write(typst_text)
        else:
            dest = output or input.with_suffix(".typ")
            dest.write_text(typst_text)
            typer.echo(f"Written to {dest}", err=True)


if __name__ == "__main__":
    app()
