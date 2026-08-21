import argparse

from rich.console import Console
from rich.table import Table
from rich.text import Text

from wurl.config import get_config
from wurl.console import get_console


def print_help(console: Console | None = None) -> None:
	console = console or get_console()
	colors = get_config().colors
	usage = Text("Usage:", style=colors.header)
	usage.append(" wurl [options] <url>")
	console.print(usage)
	prompt = Text("Try ")
	prompt.append("wurl --help", style=colors.request)
	prompt.append(" for help :)")
	console.print(prompt)


def print_manual(parser: argparse.ArgumentParser, console: Console | None = None) -> None:
	console = console or get_console()
	colors = get_config().colors
	usage = Text("Usage:", style=colors.header)
	usage.append(" wurl [options] <url>")
	console.print(usage)

	console.print(Text("\nOptions", style=colors.header))
	options = Table(box=None, show_header=False, padding=(0, 2), collapse_padding=True)
	options.add_column(style=colors.response, no_wrap=True)
	options.add_column()
	for action in parser._actions:
		if action.help is argparse.SUPPRESS:
			continue
		name = ", ".join(action.option_strings) if action.option_strings else action.dest
		value = action.metavar
		if value is None and action.choices:
			value = "{" + ",".join(str(choice) for choice in action.choices) + "}"
		if value:
			name = f"{name} {value}"
		options.add_row(name, action.help or "")
	console.print(options)

	console.print(Text("\nExamples", style=colors.header))
	examples = Table(box=None, show_header=False, padding=(0, 2), collapse_padding=True)
	examples.add_column(style=colors.request, no_wrap=True)
	examples.add_column()
	for command in _EXAMPLES:
		examples.add_row(command)
	console.print(examples)

_EXAMPLES = [
	"wurl https://example.com",
	"wurl -i https://example.com",
	"wurl -d '{\"name\":\"Ada\"}' https://api.example.com/users",
	"wurl -H 'Accept: application/json' https://api.example.com",
	"wurl -F 'avatar=@photo.jpg' https://api.example.com/profile",
	"wurl -L -o page.html https://example.com",
]
