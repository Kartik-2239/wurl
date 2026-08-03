from typing import Generator
from rich import print
import httpx
from argparse import Namespace
from pydantic import BaseModel

from wurl.http.cookies import write_cookies_to_file

class Chunk(BaseModel):
    byte_data: bytes
    content_type: str | None = None

def make_request(
        url, method="GET",
        headers: dict[str, str] | None = None, 
        cookies: dict[str, str] | None = None, 
        data: dict[str, str] | None = None,
        args: Namespace | None = None,
    ) -> Generator[Chunk, None, None]:

    url = _resolve_url(url)
    include = args.include if args else False
    verbose = args.verbose if args else False
    redirects = args.location if args else False
    info = args.info if args else False
    ignore = not (args.insecure if args else False)


    if info: method = "HEAD"

    client = httpx.Client(
        headers=headers, 
        cookies=cookies, 
        timeout=10.0, 
        follow_redirects=redirects,
        verify=ignore,
        event_hooks={
            "request": [_event_hook_request(verbose)],
            "response": [_event_hook_response(verbose)]
        }
    )
    with client.stream(method, url, data=data) as response:
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

        # body
        for chunk in response.iter_bytes():
            yield Chunk(byte_data=chunk, content_type=content_type)

def _resolve_url(url: str) -> str:
    if not url.startswith("http://") and not url.startswith("https://"):
        return "https://" + url
    return url

def _event_hook_request(verbose: bool):
    def request_hook(request: httpx.Request):
        if verbose:
            print(f"[bold green]Request:[/bold green] {request._content} {request.method} {request.url}")
            for h in request.headers:
                print(f"[bold]{str(h).capitalize()}[/bold]: {request.headers[h]}")
            print()
    return request_hook

def _event_hook_response(verbose: bool):
    def response_hook(response: httpx.Response):
        if verbose:
            print(f"[bold blue]Response:[/bold blue] {response}")
            for h in response.headers:
                print(f"[bold]{str(h).capitalize()}[/bold]: {response.headers[h]}")
            print()
    return response_hook

def _handle_include(response: httpx.Response) -> Generator[bytes, None, None]:
    yield f"[bold]{response.http_version}[/bold] [bold]{response.status_code}[/bold] {response.reason_phrase}\n".encode()
    for h in response.headers:
        yield f"[bold]{str(h).capitalize()}[/bold]: {response.headers[h]}\n".encode()
    yield b"\n"

def _handle_write_cookies(response: httpx.Response, cookies_file: str):
    cookies = response.cookies.jar
    cookies_dict = {cookie.name: cookie.value or "" for cookie in cookies}
    write_cookies_to_file(cookies_dict, cookies_file)