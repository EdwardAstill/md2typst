import sys
from pathlib import Path
from typing import Optional

import typer

from md2typst.converter import convert

app = typer.Typer(help="Convert Markdown documents to Typst.")


def _prepend_page_set(typst_text: str, paper: str) -> str:
    return f'#set page(paper: "{paper}")\n\n' + typst_text


@app.command()
def md2typst(
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
):
    if input is None:
        if sys.stdin.isatty():
            typer.echo("Reading from stdin… (Ctrl-D to finish)", err=True)
        md_text = sys.stdin.read()
        typst_text = convert(md_text)
        if paper:
            typst_text = _prepend_page_set(typst_text, paper)
        if output:
            output.write_text(typst_text)
            typer.echo(f"Written to {output}", err=True)
        else:
            sys.stdout.write(typst_text)
    else:
        md_text = input.read_text()
        typst_text = convert(md_text)
        if paper:
            typst_text = _prepend_page_set(typst_text, paper)
        if stdout:
            sys.stdout.write(typst_text)
        else:
            dest = output or input.with_suffix(".typ")
            dest.write_text(typst_text)
            typer.echo(f"Written to {dest}", err=True)


if __name__ == "__main__":
    app()
