

from argparse import Namespace


def add_header_to_parser(parser):
    parser.add_argument(
        "-H",
        action="append",
        help="Add custom header to request (can be used multiple times)"
    )

    parser.add_argument(
        "-A", "--user-agent",
        help="Set User-Agent header"
    )

    parser.add_argument(
        "-i", "--include",
        action="store_true",
        help="Include response headers in output"
    )

    parser.add_argument(
        "-I", "--info",
        action="store_true",
        help="Print response headers and status code only"
    )



def parse_headers(args: Namespace) -> dict[str, str]:
    headers_list = args.H if args.H else []
    headers = {}
    headers = _add_header(headers, "User-Agent", args.user_agent or "wurl/1.0")
    for header in headers_list:
        if ':' in header:
            key, value = header.split(':', 1)
            headers[key.strip()] = value.strip()
        else:
            raise ValueError(f"Invalid header format: '{header}'. Expected 'Key: Value'.")
    return headers


def _add_header(headers: dict[str, str], key: str, value: str) -> dict[str, str]:
    headers[key] = value
    return headers