from typing import Generator, Literal, TypeAlias
from urllib.parse import quote
import httpx
import argparse
from argparse import ArgumentParser, Namespace
from pydantic import BaseModel

from wurl.config import get_config
from wurl.http.cookies import write_cookies_to_file
from wurl.http.forms import resolve_forms
from wurl.http.verbose import HTTPTransportVerbose

class _RedirectClient(httpx.Client):
    """httpx.Client that can keep the original method on chosen redirect codes (curl's --post301/2/3)."""
    def __init__(self, *args, keep_method_on: frozenset | set = frozenset(), **kwargs):
        super().__init__(*args, **kwargs)
        self._keep_method_on = keep_method_on

    def _redirect_method(self, request: httpx.Request, response: httpx.Response) -> str:
        if response.status_code in self._keep_method_on:
            return request.method
        return super()._redirect_method(request, response)

def resolve_data(args: Namespace) -> str | bytes | None:
    if args.json is not None:
        return args.json
    if args.upload_file:
        with open(args.upload_file, "rb") as f:
            return f.read()
    if args.data_urlencode:
        parts = []
        for item in args.data_urlencode:
            key, sep, value = item.partition("=")
            parts.append(f"{key}={quote(value)}" if sep else quote(item))
        return "&".join(parts)
    return args.data_raw or args.data_binary or args.data

def add_requests_to_parser(parser: ArgumentParser):
    parser.add_argument(
        "--timeout",
        default=10,
        help="Set the request timeout in seconds (default: 10)",
    )

    parser.add_argument(
        "--retries",
        default=3,
        help="Set the number of retries for failed requests (default: 3)",
    )

    parser.add_argument(
        "--http2",
        action="store_true",
        help="Enable HTTP/2 support",
    )

    parser.add_argument(
        "--proxy",
        help="Set a proxy URL for the request (e.g., http://proxy.example.com:8080)",
    )

    parser.add_argument(
        "-k", "--insecure",
        action="store_true",
        help="Allow insecure server connections when using SSL"
    )

    parser.add_argument(
        "--cert",
        help="Path to the client certificate file",
    )
    parser.add_argument(
        "--key",
        help="Path to the client key file",
    )
    parser.add_argument(
        "--cacert",
        help="Path to the CA certificate file",
    )
    parser.add_argument(
        "-4", "--ipv4",
        action="store_true",
        help=argparse.SUPPRESS
    )
    parser.add_argument(
        "-6", "--ipv6",
        action="store_true",
        help=argparse.SUPPRESS
    )

    parser.add_argument(
        "--max-redirects", "--max-redirs",
        type=int,
        default=10,
        dest="max_redirects",
        help="Set the maximum number of redirects to follow",
    )

    parser.add_argument(
        "--post301", action="store_true", help="Do not convert POST to GET after a 301 redirect"
    )
    parser.add_argument(
        "--post302", action="store_true", help="Do not convert POST to GET after a 302 redirect"
    )
    parser.add_argument(
        "--post303", action="store_true", help="Do not convert POST to GET after a 303 redirect"
    )

    parser.add_argument("-u", "--user", help="Server user and password, in the form user:pass, for Basic auth")
    parser.add_argument("--json", help="Send data as JSON (sets Content-Type/Accept, implies POST)")
    parser.add_argument("-G", "--get", action="store_true", help="Put the -d data into the URL as a query string and use GET")
    parser.add_argument("--data-raw", help="Send data in request body (like -d)")
    parser.add_argument("--data-binary", help="Send data in request body exactly as-is (like -d)")
    parser.add_argument("--data-urlencode", action="append", help="Send URL-encoded data (name=value) in request body")
    parser.add_argument("-T", "--upload-file", help="Upload the given file via PUT")
    parser.add_argument("-D", "--dump-header", help="Write response headers to FILE")
    parser.add_argument("-m", "--max-time", type=float, help="Maximum time in seconds for the whole request")
    parser.add_argument("--connect-timeout", type=float, help="Maximum time in seconds for the connection phase")
    parser.add_argument("-w", "--write-out", help="Print info after the transfer (e.g. '%%{http_code} %%{time_total}')")
    parser.add_argument("-C", "--continue-at", type=int, help="Resume a download at OFFSET bytes")
    parser.add_argument("--compressed", action="store_true", help="Request a compressed response (handled automatically)")

class ResponseStatus(BaseModel):
    type: Literal["status"] = "status"
    http_version: str
    status_code: int
    reason_phrase: str

class ResponseHeader(BaseModel):
    type: Literal["header"] = "header"
    key: str
    value: str

class ResponseBody(BaseModel):
    type: Literal["body"] = "body"
    byte_data: bytes
    content_type: str | None = None
    progress: float | None = None

ResponseEvent: TypeAlias = ResponseStatus | ResponseHeader | ResponseBody

def make_request(
        url, method: str,
        headers: dict[str, str] | None = None, 
        cookies: dict[str, str] | None = None, 
        data: str | bytes | None = None,
        include: bool = False,
        verbose: bool = False,
        redirects: bool = False,
        info: bool = False,
        ignore: bool = False,
        raw: bool = False,
        args: Namespace | None = None,
        transport: httpx.HTTPTransport | None = None
    ) -> Generator[ResponseEvent, None, None]:

    if args is None:
        raise ValueError("args cannot be None.")

    url = _resolve_url(url)

    cfg = get_config().http

    redirects = (args.location if args else False) or cfg.follow_redirects

    form_data, file_data = resolve_forms(args) if args else (None, None)

    if data and form_data:
        raise ValueError("Cannot use both --data and --form options at the same time.")

    cert, key, cacert = _resolve_certificates(args) if args else (None, None, None)

    local_address = "0.0.0.0" if args.ipv4 else "::" if args.ipv6 else None
    resolved_t = transport if transport else (HTTPTransportVerbose(local_address=local_address) if verbose else httpx.HTTPTransport(local_address=local_address))

    auth = tuple(args.user.split(":", 1)) if args.user and ":" in args.user else ((args.user, "") if args.user else None)

    timeout = cfg.timeout if args.timeout is None else args.timeout
    if args.max_time:
        timeout = args.max_time
    if args.connect_timeout:
        timeout = httpx.Timeout(timeout, connect=args.connect_timeout)

    if args.continue_at:
        headers = {**(headers or {}), "Range": f"bytes={args.continue_at}-"}

    keep_method_on = {code for code, flag in ((301, args.post301), (302, args.post302), (303, args.post303)) if flag}

    client = _RedirectClient(
        transport=resolved_t,
        headers=headers,
        cookies=cookies,
        timeout=timeout,
        proxy=args.proxy if args.proxy else None,
        follow_redirects=redirects,
        http2=args.http2 if args.http2 else False,
        verify=cacert if cacert else ignore,
        cert=(cert if cert and not key else (cert, key) if cert and key else None),
        max_redirects=args.max_redirects,
        auth=auth,
        keep_method_on=keep_method_on,
    )
    with client.stream(
        method, 
        url, 
        content=data if isinstance(data, (str, bytes)) else None,
        data=form_data,
        files=file_data if file_data else None,
    ) as response:
        length = 0
        if response.headers.get("Content-Length") is not None:
            length = int(response.headers.get("Content-Length"))

        if args.dump_header:
            _dump_headers(response, args.dump_header)
        if include or info:
            yield from _response_metadata(response)
        content_type = response.headers.get("Content-Type", None)
        _handle_write_cookies(response, args.cookie_jar) if args and args.cookie_jar else None
        if info:
            return

        if args is not None and args.fail:
            response.raise_for_status()

        # body
        for chunk in response.iter_bytes():
            if args and args.raw:
                yield ResponseBody(byte_data=chunk, content_type=None, progress=(len(chunk) / length * 100) if length > 0 else None)
            else:
                yield ResponseBody(byte_data=chunk, content_type=content_type, progress=(len(chunk) / length * 100) if length > 0 else None)

def _resolve_certificates(args: Namespace) -> tuple[str | None, str | None, str | None]:
    cert = args.cert if args.cert else None
    key = args.key if args.key else None
    cacert = args.cacert if args.cacert else None
    return cert, key, cacert

def _dump_headers(response: httpx.Response, file_path: str):
    with open(file_path, "w") as f:
        f.write(f"{response.http_version} {response.status_code} {response.reason_phrase}\r\n")
        for key, value in response.headers.multi_items():
            f.write(f"{key}: {value}\r\n")


def _resolve_url(url: str) -> str:
    if not url.startswith("http://") and not url.startswith("https://"):
        return "https://" + url
    return url

def _response_metadata(response: httpx.Response) -> Generator[ResponseStatus | ResponseHeader, None, None]:
    yield ResponseStatus(
        http_version=response.http_version,
        status_code=response.status_code,
        reason_phrase=response.reason_phrase,
    )
    for key, value in response.headers.multi_items():
        yield ResponseHeader(key=key, value=value)

def _handle_write_cookies(response: httpx.Response, cookies_file: str):
    cookies = response.cookies.jar
    print("cookies", cookies)
    cookies_dict = {cookie.name: cookie.value or "" for cookie in cookies}
    print("dict", cookies_dict)
    write_cookies_to_file(cookies_dict, cookies_file)
