
from rich.console import Console

from wurl.config import get_config


def create_table_from_csv(csv: str, name: str | None = None):
    from rich.table import Table

    from rich import box
    cfg = get_config().table
    box_style = getattr(box, cfg.box.upper(), box.ROUNDED)
    table = Table(title=name, show_edge=cfg.show_edge, show_lines=cfg.show_lines, box=box_style)
    cols = len(csv.splitlines()[0].split(","))

    for col_names in csv.splitlines()[0].split(","):
        table.add_column(col_names.strip())

    for row in csv.splitlines()[1:]:
        cells = row.split(",")
        if len(cells) < cols:
            cells.extend([""] * (cols - len(cells)))
        table.add_row(*cells)

    return table