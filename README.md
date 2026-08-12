# wurl

`wurl` is a command-line HTTP client for making requests, it comes with Rich syntax highlighting and formatting.

## Features
- Syntax highlighting for JSON, HTML, XML, CSS, JavaScript, and more.
- Rich formatting for HTTP requests and responses.
- Image rendering in the terminal for image responses.

## Requirements

- Python 3.12 or newer
- [uv](https://docs.astral.sh/uv/)

## Installation

Install from pypi:

```sh
uv tool install wurl-cli
# or
pipx install wurl-cli
```

and use with
```sh
wurl <url>
```

Clone the repository and install its dependencies:

```sh
git clone https://github.com/Kartik-2239/wurl.git
```

```sh
uv sync
```

The CLI is exposed as `wurl`, so it can be run with:

```sh
uv run wurl <url>
```

for convenience, install it as a tool:

```sh
uv tool install -e .

# and use with just wurl
wurl --help
```

## Examples

```sh
# Fetch and display a response
uv run wurl https://example.com

# Send a JSON request body (wurl uses POST when --data is supplied)
uv run wurl https://api.example.com/items \
	-H 'Content-Type: application/json' \
	-d '{"name":"demo"}'

# Saving a response body to a file
uv run wurl https://example.com/file.zip -o file.zip

# Use plain text output without colors or formatting
uv run wurl https://example.com --use-plain-text

# For installation scripts
uv run wurl https://example.com/install.sh --use-plain-text | bash
```

## Command-line options

The required positional argument is:

| Argument | Description |
| --- | --- |
| `url` | URL to fetch. |

### CLI flags

| Option | Description |
| --- | --- |
| `-X METHOD` | Request method: `GET`, `POST`, `PUT`, `DELETE`, `PATCH`, `HEAD`, or `OPTIONS`. |
| `-d`, `--data DATA` | Send data in the request body. If no method is supplied, the method defaults to `POST`. |
| `-H HEADER` | Add a request header in `Key: Value` form. May be used more than once. |
| `-A`, `--user-agent VALUE` | Set the `User-Agent` header. |
| `-b FILE` | Read cookies from a file containing one `Key=Value` pair per line. |
| `-c FILE` | Save cookies received in the response to a file. |
| `-o FILE` | Write response to a file with a specific name |
| `-O` | Write response to a file |
| `-i`, `--include` | Include HTTP status, headers, and response body |
| `-I`, `--info` | Make a `HEAD` request and print response information only |
| `-v`, `--verbose` | Print request and response details |
| `-s`, `--silent` | Disable the progress meter and errors |
| `-S`, `--show-error` | With `--silent`, show errors before exiting |
| `-f`, `--fail` | Raise an error for HTTP 4xx and 5xx responses |
| `-L`, `--location` | Follow redirects |
| `-k`, `--insecure` | Disable TLS certificate verification |
| `-up`, `--use-plain-text` | Disable colors and Rich formatting |

## Response formatting

- Languages are syntax highlighted and formatted.
- Binary data can be saved using `-o` or `-O`.
- All the formatting and syntax highlighting can be suppressed with `--use-plain-text`.

## Configuration and customization

Wurl creates a config file `~/.wurl`. 
This file is used for customizing wurl.

You can read this file and customize it accordingly.

```toml
[theme]# wurl configuration file
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
```
