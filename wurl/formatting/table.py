
from rich.console import Console


def create_table_from_csv(csv: str, name: str | None = None):
    from rich.table import Table

    from rich import box
    table = Table(title=name, show_edge=True, show_lines=True, box=box.ROUNDED)
    cols = len(csv.splitlines()[0].split(","))

    for col_names in csv.splitlines()[0].split(","):
        table.add_column(col_names.strip())

    for row in csv.splitlines()[1:]:
        cells = row.split(",")
        if len(cells) < cols:
            cells.extend([""] * (cols - len(cells)))
        table.add_row(*cells)

    return table