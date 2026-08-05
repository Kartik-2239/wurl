import sys
import tomllib
from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel

CONFIG_PATH = Path.home() / ".wurl"

DEFAULT_CONFIG = """\
# wurl configuration file
# Styles accept any Rich style string: https://rich.readthedocs.io/en/stable/style.html

[theme]
# Pygments theme for syntax highlighting (e.g. one-dark, dracula, monokai, nord)
syntax = "one-dark"
# Rich color system: "standard", "256", "truecolor", or "windows"
color_system = "standard"

[colors]
error = "red"
request = "bold green"
response = "bold blue"
header = "bold"

[syntax]
indent_guides = false
word_wrap = true
background_color = "default"

[format]
json_indent = 2
html_indent = 3
use_pager = true

[table]
# Box drawing style: ASCII, ASCII2, SQUARE, ROUNDED, HEAVY, DOUBLE,
# MINIMAL, SIMPLE, HEAVY_HEAD, SQUARE_DOUBLE_HEAD, NONE ...
box = "ROUNDED"
show_edge = true
show_lines = true

[http]
timeout = 10.0
user_agent = "wurl/1.0"
follow_redirects = false
"""


class ThemeConfig(BaseModel):
    syntax: str = "one-dark"
    color_system: str = "standard"


class ColorsConfig(BaseModel):
    error: str = "red"
    request: str = "bold green"
    response: str = "bold blue"
    header: str = "bold"


class SyntaxConfig(BaseModel):
    indent_guides: bool = False
    word_wrap: bool = True
    background_color: str = "default"


class FormatConfig(BaseModel):
    json_indent: int = 2
    html_indent: int = 3
    use_pager: bool = True


class TableConfig(BaseModel):
    box: str = "ROUNDED"
    show_edge: bool = True
    show_lines: bool = True


class HttpConfig(BaseModel):
    timeout: float = 10.0
    user_agent: str = "wurl/1.0"
    follow_redirects: bool = False


class Config(BaseModel):
    theme: ThemeConfig = ThemeConfig()
    colors: ColorsConfig = ColorsConfig()
    syntax: SyntaxConfig = SyntaxConfig()
    format: FormatConfig = FormatConfig()
    table: TableConfig = TableConfig()
    http: HttpConfig = HttpConfig()


def load_config() -> Config:
    if not CONFIG_PATH.exists():
        CONFIG_PATH.write_text(DEFAULT_CONFIG)
        return Config()
    try:
        data = tomllib.loads(CONFIG_PATH.read_text())
        return Config.model_validate(data)
    except (tomllib.TOMLDecodeError, ValueError) as e:
        print(f"wurl: invalid config at {CONFIG_PATH}, using defaults ({e})", file=sys.stderr)
        return Config()


@lru_cache(maxsize=1)
def get_config() -> Config:
    return load_config()
