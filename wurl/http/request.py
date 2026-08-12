from typing import Generator, Literal, TypeAlias
import httpx
from argparse import ArgumentParser, Namespace
from pydantic import BaseModel

from wurl.config import get_config
from wurl.http.cookies import write_cookies_to_file
from wurl.http.forms import resolve_forms
from wurl.http.verbose import HTTPTransportVerbose

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
        data: dict[str, str] | None = None,
        include: bool = False,
        verbose: bool = False,
        redirects: bool = False,
        info: bool = False,
        ignore: bool = False,
        raw: bool = False,
        args: Namespace | None = None,
        transport: httpx.BaseTransport | None = None
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

    client = httpx.Client(
        transport=transport if transport else (HTTPTransportVerbose() if verbose else None),
        headers=headers,
        cookies=cookies,
        timeout=cfg.timeout if args.timeout is None else args.timeout,
        proxy=args.proxy if args.proxy else None,
        follow_redirects=redirects,
        http2=args.http2 if args.http2 else False,
        verify=cacert if cacert else ignore,
        cert=(cert if cert and not key else (cert, key) if cert and key else None),
    )
    with client.stream(
        method, 
        url, 
        data=data or form_data,
        files=file_data if file_data else None,
    ) as response:
        length = 0
        if response.headers.get("Content-Length") is not None:
            length = int(response.headers.get("Content-Length"))

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
