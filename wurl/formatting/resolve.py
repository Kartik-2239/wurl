from rich.console import Console

from wurl.formatting.language import resolve_language
from rich.console import Console

from wurl.formatting.utils import format_json, is_printable

def resolve_formatting(content_type: str | None, content: bytes, console: Console):
    if content_type is None:
        console.print(content.decode(), end='')
        return
    write_text(content_type, content, console)



def write_text(content_type: str | None, content: bytes, console: Console):
    if not is_printable(content):
        console.print("[red]Binary data cannot be displayed in the terminal. Use `-o` to save the binary in a file. [/red]")
        exit(1)
        return
    language = resolve_language(content_type)
    if language is None:
        console.print(content.decode(), end='')
        return

    if language == "json":
        content = format_json(content)

    if language == "csv":
        from wurl.formatting.table import create_table_from_csv
        table = create_table_from_csv(content.decode())
        console.print(table)
        return

    if language == "html":
        from yattag import indent
        content = indent(string=content.decode(), indentation='   ')
        content = str(content).encode('utf-8')

    from rich.syntax import Syntax
    syntax = Syntax(content.decode(), language, background_color="default", theme="one-dark", indent_guides=False, word_wrap=True)
    console.print(syntax)
    