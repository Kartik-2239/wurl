import argparse
import os
from wurl.http.request import add_requests_to_parser
from wurl.http.forms import add_forms_to_parser
from pprint import pprint
from typing import Tuple
from rich.console import Console, Group
from rich.live import Live
from argparse import Namespace
from wurl.http.request import Chunk
import json
from wurl.config import get_config
from wurl.console import get_console
from wurl.http.cookies import add_cookies_to_parser
from wurl.http.headers import add_header_to_parser, parse_headers
from wurl.http.request import make_request
from wurl.http.cookies import handle_cookie_args
from wurl.formatting.resolve import resolve_formatting
from rich.progress import Progress, Task, TaskID
import sys
import time

parser = argparse.ArgumentParser()

parser.add_argument("url", help="URL to fetch")

add_header_to_parser(parser)
add_cookies_to_parser(parser)
add_requests_to_parser(parser)
add_forms_to_parser(parser)

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
    "-s", "--silent",
    action="store_true",
    help="disable progress meter"
)

parser.add_argument(
    "-S", "--show-error",
    action="store_true",
    help="Show error messages even when --silent is used"
)

parser.add_argument(
    "-f", "--fail",
    action="store_true",
    help="Fail silently on server errors (4xx, 5xx)"
)

parser.add_argument(
    "-k", "--insecure",
    action="store_true",
    help="Allow insecure server connections when using SSL"
)

parser.add_argument(
    "--raw",
    action="store_true",
    help="Use plain text output without colors or formatting"
)

parser.add_argument(
    "--no-pager",
    action="store_true",
    help="Disable pager for output"
)

parser.add_argument(
    "--pager",
    action="store_true",
    help="Force pager for output"
)

def main():
    cfg = get_config()
    if len(sys.argv) == 1:
        print_ascii_art()
        parser.print_usage()
        exit(0)
    args = parser.parse_args()
    console = get_console(use_plain_text=args.raw)


    use_pager = False
    # 1.) check for output
    # 2.) check the args for use_pager
    # 3.) then check the config for use_pager
    if args.O or args.output:
        use_pager = False
    elif args.no_pager:
        use_pager = False
    elif args.pager:
        use_pager = True
    elif cfg.format.use_pager:
        use_pager = True

    # It won't work if $Pager is not set.
    if os.environ.get("PAGER") is None:
        use_pager = False

    if args.raw:
        use_pager = False
    
    if use_pager:
        with console.pager(styles=True):
            chunk_request(console)
    else:
        chunk_request(console)

def chunk_request(console: Console):
    args = parser.parse_args()

    progress = Progress(speed_estimate_period=1, console=console, transient=True)
    text_bytes_per_second = "0"
    live = Live(Group(progress, text_bytes_per_second), console=console, refresh_per_second=10)

    task = progress.add_task("[cyan]", total=100)

    args = parser.parse_args()
    headers = parse_headers(args)
    cookies = handle_cookie_args(args)

    console = get_console(use_plain_text=args.raw)

    bytes_data = b"" # for broken responses but with one line of json

    progress_started = False
    bytes_per_second = 0

    bytes_done = 0
    first_time = None

    try:

        for chunk in make_request(
            args.url, 
            method=resolve_method(args), 
            headers=headers, 
            cookies=cookies, 
            data=args.data, 
            args=args
        ):
            if progress_started:
                progress.update(task, advance=chunk.progress if chunk.progress else 0)
                text_bytes_per_second = f"{bytes_per_second/(1024*1024):.1f} MB/s"
                live.update(Group(progress, text_bytes_per_second))
                
            if args.O or args.output:
                if first_time is None:
                    first_time = time.time()
                progress_started, bytes_done, bytes_per_second = handle_output(args, chunk, live, progress_started, first_time, bytes_done)
            else:
                bytes_data += chunk.byte_data
                if bytes_data.count(b"\n") <= 1:
                    if chunk.content_type is not None and "json" in chunk.content_type:
                        try:
                            json.loads(bytes_data.decode())
                            resolve_formatting(chunk.content_type, bytes_data, console, args.url)
                        except json.JSONDecodeError:
                            pass
                    else:
                        resolve_formatting(chunk.content_type, bytes_data, console, args.url)
                else:
                    text = chunk.byte_data.decode()
                    console.print(text, end="")
    except Exception as e:
        if args.show_error and args.silent:
            console.print(f"[error]{e}[/error]")
            exit(1)
        if args.silent and not args.show_error:
            exit(1)
        console.print(f"[error]{e}[/error]")
        exit(1)
    finally:
        if progress is not None:
            live.stop()

def handle_output(args: Namespace, chunk: Chunk, live: Live, progress_started: bool, first_time: float, bytes_done: int) -> tuple[bool, int, float]: 
    if args.output:
        name = args.output
    else:
        name = args.url.split("/")[-1] or "output"

    if not progress_started and not args.silent:
        # progress.start()
        live.start()
        progress_started = True

    with open(name, "ab") as f:
        f.write(chunk.byte_data)

    bytes_done += len(chunk.byte_data)
    cur_time = time.time()
    avg_speed = 0
    if cur_time > first_time:
        avg_speed = bytes_done / (cur_time - first_time)

    return progress_started, bytes_done, avg_speed

def resolve_method(args):
    if args.X:
        return args.X
    if args.data:
        return "POST"
    if args.form:
        return "POST"
    if args.info:
        return "HEAD"
    return "GET"

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

if __name__ == "__main__":
    main()