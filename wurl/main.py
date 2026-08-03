import argparse
from pprint import pprint

import json
from wurl.config import get_config
from wurl.console import get_console
from wurl.http.cookies import add_cookies_to_parser
from wurl.http.headers import add_header_to_parser, parse_headers
from wurl.http.request import make_request
from wurl.http.cookies import handle_cookie_args
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
    get_config()
    if len(sys.argv) == 1:
        print_ascii_art()
        parser.print_usage()
        exit(0)

    args = parser.parse_args()
    headers = parse_headers(args)
    cookies = handle_cookie_args(args)

    console = get_console()

    bytes_data = b""
    last_bytes_data = b""

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
                bytes_data += chunk.byte_data
                text = chunk.byte_data.decode()
                if bytes_data.count(b"\n") <= 1:
                    try:
                        json.loads(bytes_data.decode())
                        resolve_formatting(chunk.content_type, bytes_data, console)
                    except json.JSONDecodeError:
                        pass
                else:
                    console.print(text, end="")
                
                # resolve_formatting(chunk.content_type, chunk.byte_data, console)
    except Exception as e:
        console.print(f"[error]{e}[/error]")
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