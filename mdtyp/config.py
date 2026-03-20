"""Configuration system for md2typst."""

import dataclasses
import tomllib
from dataclasses import dataclass, field
from os import environ
from pathlib import Path


@dataclass
class TableConfig:
    header_bold: bool = True
    stroke: str = ""


@dataclass
class BlockquoteConfig:
    function: str = "quote"


@dataclass
class HrConfig:
    style: str = "#line(length: 100%)"


@dataclass
class ImageConfig:
    use_figure: bool = True
    width: str = ""


@dataclass
class CodeConfig:
    block_function: str = ""


@dataclass
class PageConfig:
    paper: str = ""


@dataclass
class Config:
    table: TableConfig = field(default_factory=TableConfig)
    blockquote: BlockquoteConfig = field(default_factory=BlockquoteConfig)
    hr: HrConfig = field(default_factory=HrConfig)
    image: ImageConfig = field(default_factory=ImageConfig)
    code: CodeConfig = field(default_factory=CodeConfig)
    page: PageConfig = field(default_factory=PageConfig)


def default_config_path() -> Path:
    xdg = environ.get("XDG_CONFIG_HOME", "")
    base = Path(xdg) if xdg else Path.home() / ".config"
    return base / "mdtyp" / "config.toml"


def load_config(path: Path | None = None) -> Config:
    """Load config from a TOML file. Returns defaults if no file exists."""
    if path is None:
        path = default_config_path()
        if not path.exists():
            return Config()
    with open(path, "rb") as f:
        data = tomllib.load(f)
    return _build_config(data)


def _build_config(data: dict) -> Config:
    """Construct a Config from parsed TOML data, keeping defaults for missing keys."""
    cfg = Config()
    for section_name in dataclasses.fields(cfg):
        section_data = data.get(section_name.name)
        if section_data and isinstance(section_data, dict):
            section_obj = getattr(cfg, section_name.name)
            for k, v in section_data.items():
                if hasattr(section_obj, k):
                    setattr(section_obj, k, v)
    return cfg
