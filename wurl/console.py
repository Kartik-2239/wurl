from rich.console import Console
from rich.theme import Theme

from wurl.config import get_config

_console: Console | None = None


def get_console(use_plain_text: bool = False) -> Console:
    global _console
    if _console is None:
        cfg = get_config()
        theme = Theme(
            {
                "error": cfg.colors.error,
                "request": cfg.colors.request,
                "response": cfg.colors.response,
                "header": cfg.colors.header,
            }
        )
        _console = Console(theme=theme, color_system=cfg.theme.color_system) # type: ignore hehe :)
        if use_plain_text:
            _console = Console(theme=None, color_system=None, force_terminal=True, no_color=True)
            _console.print = print # type: ignore :)
    return _console
