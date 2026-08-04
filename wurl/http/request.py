from typing import Generator
import httpx
from argparse import Namespace
from pydantic import BaseModel
from rich.console import Console

from wurl.config import get_config
from wurl.console import get_console
from wurl.http.cookies import write_cookies_to_file

class Chunk(BaseModel):
    byte_data: bytes
    content_type: str | None = None
    progress: float | None = None

def make_request(
        url, method="GET",
        headers: dict[str, str] | None = None, 
        cookies: dict[str, str] | None = None, 
        data: dict[str, str] | None = None,
        args: Namespace | None = None,
    ) -> Generator[Chunk, None, None]:

    url = _resolve_url(url)
    cfg = get_config().http
    include = args.include if args else False
    verbose = args.verbose if args else False
    redirects = (args.location if args else False) or cfg.follow_redirects
    info = args.info if args else False
    ignore = not (args.insecure if args else False)

    console = get_console(use_plain_text=args.use_plain_text if args else False)


    if info: method = "HEAD"

    client = httpx.Client(
        headers=headers,
        cookies=cookies,
        timeout=cfg.timeout,
        follow_redirects=redirects,
        verify=ignore,
        event_hooks={
            "request": [_event_hook_request(verbose, console=console)],
            "response": [_event_hook_response(verbose, console=console)],
        }
    )
    with client.stream(method, url, data=data) as response:
        length = 0
        if response.headers.get("Content-Length") is not None:
            length = int(response.headers.get("Content-Length"))

        # headers and stuff
        if include or info:
            for chunk in _handle_include(response):
                yield Chunk(byte_data=chunk, content_type=None)

        if include:
            yield Chunk(byte_data=b"\n", content_type=None)
        content_type = response.headers.get("Content-Type", None)
        _handle_write_cookies(response, args.c) if args and args.c else None
        if info:
            return

        if args is not None and args.fail:
            response.raise_for_status()

        # body
        for chunk in response.iter_bytes():
            if args and args.use_plain_text:
                yield Chunk(byte_data=chunk, content_type=None, progress=(len(chunk) / length * 100) if length > 0 else None)
            else:
                yield Chunk(byte_data=chunk, content_type=content_type, progress=(len(chunk) / length * 100) if length > 0 else None)

def _resolve_url(url: str) -> str:
    if not url.startswith("http://") and not url.startswith("https://"):
        return "https://" + url
    return url

def _event_hook_request(verbose: bool, console: Console):
    def request_hook(request: httpx.Request):
        if verbose:
            console.print(f"[request]Request:[/request] {request._content} {request.method} {request.url}")
            for h in request.headers:
                console.print(f"[header]{str(h).capitalize()}[/header]: {request.headers[h]}")
            console.print()
    return request_hook

def _event_hook_response(verbose: bool, console: Console):
    def response_hook(response: httpx.Response):
        if verbose:
            console.print(f"[response]Response:[/response] {response}")
            for h in response.headers:
                console.print(f"[header]{str(h).capitalize()}[/header]: {response.headers[h]}")
            console.print()
    return response_hook

def _handle_include(response: httpx.Response) -> Generator[bytes, None, None]:
    yield f"[header]{response.http_version}[/header] [header]{response.status_code}[/header] {response.reason_phrase}\n".encode()
    for h in response.headers:
        yield f"[header]{str(h).capitalize()}[/header]: {response.headers[h]}\n".encode()
    yield b"\n"

def _handle_write_cookies(response: httpx.Response, cookies_file: str):
    cookies = response.cookies.jar
    cookies_dict = {cookie.name: cookie.value or "" for cookie in cookies}
    write_cookies_to_file(cookies_dict, cookies_file)