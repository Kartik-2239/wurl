from rich.console import Console

from wurl.config import get_config
from wurl.formatting.language import resolve_language
from wurl.formatting.utils import format_json, is_printable

def resolve_formatting(content_type: str | None, content: bytes, console: Console, url: str | None = None):
    write_text(content_type, content, console, url)



def write_text(content_type: str | None, content: bytes, console: Console, url: str | None = None):
    cfg = get_config()
    if not is_printable(content):
        main_type = ""
        ext = ""
        if content_type is not None and "image" in content_type:
            main_type = content_type.split("/")[0]
            ext = content_type.split("/")[1]
        else:
            import mimetypes
            main_type, ext = mimetypes.guess_type(url) if url else (None, None)
        if main_type is not None and "image" in main_type and url is not None:
            _write_image(url)
            exit(0)
            return
        console.print("[error]Binary data cannot be displayed in the terminal. Use `-o` to save the binary in a file. [/error]")
        exit(1)
        return
    language = resolve_language(content_type)
    if language is None:
        console.print(content.decode())
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

def _write_image(url):
    from term_image.image import from_url
    image = from_url(url)
    image.draw(h_align="left")