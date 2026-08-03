import argparse
from pprint import pprint
from wurl.http.cookies import add_cookies_to_parser
from wurl.http.headers import add_header_to_parser, parse_headers
from wurl.http.request import make_request
from wurl.http.cookies import handle_cookie_args
from rich.console import Console
from wurl.formatting.resolve import resolve_formatting
import sys


parser = argparse.ArgumentParser()

parser.add_argument("url", help="URL to fetch")

add_header_to_parser(parser)
add_cookies_to_parser(parser)

parser.add_argument(
    "-X", 
    choices=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"],
    help="Specify request method (GET, POST, etc.)"
)

parser.add_argument(
    "-d", "--data",
    help="Send data in request body (for POST/PUT/PATCH requests)"
)

parser.add_argument(
    "-o", "--output",
    help="Write response body to a file instead of stdout"
)

parser.add_argument(
    "-O",
    action="store_true",
    help="Write response body to a file instead of stdout"
)

parser.add_argument(
    "-v", "--verbose",
    action="store_true",
    help="Enable verbose output (request/response details)"
)

parser.add_argument(
    "-L", "--location",
    action="store_true",
    help="Follow redirects"
)

parser.add_argument(
    "-k", "--insecure",
    action="store_true",
    help="Allow insecure server connections when using SSL"
)

def main():
    if len(sys.argv) == 1:
        print_ascii_art()
        parser.print_usage()
        exit(0)

    args = parser.parse_args()
    headers = parse_headers(args)
    cookies = handle_cookie_args(args)

    console = Console(theme=None, color_system="standard")
    binary_error_shown = False
    try:
        for chunk in make_request(args.url, method=args.X or "GET", headers=headers, cookies=cookies, data=args.data, args=args):
            if args.O:
                name = args.url.split("/")[-1] or "output"
                with open(name, "ab") as f:
                    f.write(chunk.byte_data)
            elif args.output:
                with open(args.output, "ab") as f:
                    f.write(chunk.byte_data)
            else:
                resolve_formatting(chunk.content_type, chunk.byte_data, console)
    except Exception as e:
        console.print(f"[red]{e}[/red]")
        exit(1)


def print_ascii_art():
    art =r"""
██╗    ██╗██╗   ██╗██████╗ ██╗
██║    ██║██║   ██║██╔══██╗██║
██║ █╗ ██║██║   ██║██████╔╝██║
██║███╗██║██║   ██║██╔══██╗██║
╚███╔███╔╝╚██████╔╝██║  ██║███████╗
 ╚══╝╚══╝  ╚═════╝ ╚═╝  ╚═╝╚══════╝
""".strip()
    for line in art.splitlines():
        print(" " + line)
    print()