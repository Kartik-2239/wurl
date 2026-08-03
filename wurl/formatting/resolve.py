from rich.console import Console

from wurl.config import get_config
from wurl.formatting.language import resolve_language
from wurl.formatting.utils import format_json, is_printable

def resolve_formatting(content_type: str | None, content: bytes, console: Console):
    if content_type is None:
        console.print(content.decode(), end='')
        return
    write_text(content_type, content, console)



def write_text(content_type: str | None, content: bytes, console: Console):
    cfg = get_config()
    if not is_printable(content):
        console.print("[error]Binary data cannot be displayed in the terminal. Use `-o` to save the binary in a file. [/error]")
        exit(1)
        return
    language = resolve_language(content_type)
    if language is None:
        console.print(content.decode(), end='')
        return

    if language == "json":
        content = format_json(content, indent=cfg.format.json_indent)

    if language == "csv":
        from wurl.formatting.table import create_table_from_csv
        table = create_table_from_csv(content.decode())
        console.print(table)
        return

    if language == "html":
        from yattag import indent
        content = indent(string=content.decode(), indentation=' ' * cfg.format.html_indent)
        content = str(content).encode('utf-8')

    from rich.syntax import Syntax
    syntax = Syntax(content.decode(), language, background_color=cfg.syntax.background_color, theme=cfg.theme.syntax, indent_guides=cfg.syntax.indent_guides, word_wrap=cfg.syntax.word_wrap)
    console.print(syntax)
    