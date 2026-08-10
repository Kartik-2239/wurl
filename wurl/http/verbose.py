from typing import Any, Iterable, Mapping
from rich.console import Console
from wurl.console import get_console
import httpx
import ssl

async def log_trace(name, info):
    print_trace_event(name, info)


class HTTPTransportVerbose(httpx.HTTPTransport):

    def handle_request(self, request):
        request.extensions["trace"] = log_trace_sync
        return super().handle_request(request)


def log_trace_sync(name: str, info: dict[str, Any]):
    print_trace_event(name, info)


def print_trace_event(name: str, info: Mapping[str, Any]) -> None:
    console = get_console()
    for line in format_trace_event(name, info):
        console.print(line)


def format_trace_event(name: str, info: Mapping[str, Any]) -> list[str]:
    if name.endswith(".failed"):
        return [f"* {name}: {_format_exception(info.get('exception'))}"]

    if name == "connection.connect_tcp.started":
        host = info.get("host")
        port = info.get("port")
        lines = [f"* Trying {host}:{port}..."]
        if info.get("local_address") is not None:
            lines.append(f"* Local address: {info['local_address']}")
        if info.get("timeout") is not None:
            lines.append(f"* TCP timeout: {info['timeout']}s")
        if info.get("socket_options"):
            lines.append(f"* Socket options: {_format_socket_options(info['socket_options'])}")
        return lines

    if name == "connection.connect_tcp.complete":
        stream = info.get("return_value")
        client_addr = _get_extra_info(stream, "client_addr")
        server_addr = _get_extra_info(stream, "server_addr")
        if client_addr and server_addr:
            return [f"* TCP connected: \n client: {_format_addr(client_addr)} \n server: {_format_addr(server_addr)}"]
        if server_addr:
            return [f"* TCP connected to {_format_addr(server_addr)}"]
        return ["* TCP connected"]

    if name == "connection.start_tls.started":
        lines = [f"* TLS handshake starting for {info.get('server_hostname')}"]
        timeout = info.get("timeout")
        if timeout is not None:
            lines.append(f"* TLS timeout: {timeout}s")
        ssl_context = info.get("ssl_context")
        if ssl_context is not None:
            lines.extend(_format_ssl_context(ssl_context))
        return lines

    if name == "connection.start_tls.complete":
        return _format_tls_complete(info.get("return_value"))

    if name in {
        "http11.send_request_headers.started",
        "http2.send_request_headers.started",
    }:
        return _format_request_headers(info.get("request"), http2=name.startswith("http2"))

    if name in {
        "http11.send_request_headers.complete",
        "http2.send_request_headers.complete",
    }:
        return ["* Request headers sent"]

    if name in {
        "http11.send_request_body.started",
        "http2.send_request_body.started",
    }:
        request = info.get("request")
        method = _decode(getattr(request, "method", b"request"))
        return [f"* Sending {method} request body"]

    if name in {
        "http11.send_request_body.complete",
        "http2.send_request_body.complete",
    }:
        return ["* Request body sent"]

    if name in {
        "http11.receive_response_headers.started",
        "http2.receive_response_headers.started",
    }:
        return ["* Waiting for response headers"]

    if name == "http11.receive_response_headers.complete":
        return _format_response_headers(info.get("return_value"), http2=False)

    if name == "http2.receive_response_headers.complete":
        return _format_response_headers(info.get("return_value"), http2=True)

    if name in {
        "http11.receive_response_body.started",
        "http2.receive_response_body.started",
    }:
        return ["* Receiving response body"]

    if name in {
        "http11.receive_response_body.complete",
        "http2.receive_response_body.complete",
    }:
        return ["* Response body received"]

    if name in {
        "http11.response_closed.started",
        "http2.response_closed.started",
    }:
        return ["* Closing response stream"]

    if name in {
        "http11.response_closed.complete",
        "http2.response_closed.complete",
    }:
        return ["* Response stream closed"]

    return _format_unknown_event(name, info)


def _format_request_headers(request: Any, http2: bool) -> list[str]:
    if request is None:
        return ["* Sending request headers"]

    method = _decode(getattr(request, "method", b""))
    url = getattr(request, "url", None)
    target = _decode(getattr(url, "target", b"/"))
    version = "HTTP/2" if http2 else "HTTP/1.1"
    lines = [f"> {method} {target} {version}"]
    for key, value in getattr(request, "headers", []):
        lines.append(f"> {_decode(key)}: {_decode(value)}")
    return lines


def _format_response_headers(value: Any, http2: bool) -> list[str]:
    if not value:
        return ["< Response headers received"]

    if http2:
        status, headers = value
        http_version = "HTTP/2"
        reason_phrase = ""
    else:
        http_version_bytes, status, reason_phrase_bytes, headers = value
        http_version = _decode(http_version_bytes)
        reason_phrase = _decode(reason_phrase_bytes)

    status_line = f"< {http_version} {status}"
    if reason_phrase:
        status_line += f" {reason_phrase}"

    lines = [status_line]
    for key, value in headers:
        lines.append(f"< {_decode(key)}: {_decode(value)}")
    return lines


def _format_tls_complete(stream: Any) -> list[str]:
    ssl_object = _get_extra_info(stream, "ssl_object")
    if ssl_object is None:
        return ["* TLS established"]

    lines = []
    version = _call_ssl_method(ssl_object, "version")
    cipher = _call_ssl_method(ssl_object, "cipher")
    if cipher:
        cipher_name = cipher[0]
        lines.append(f"* TLS established: {version} / {cipher_name}")
    elif version:
        lines.append(f"* TLS established: {version}")
    else:
        lines.append("* TLS established")

    alpn = _call_ssl_method(ssl_object, "selected_alpn_protocol")
    if alpn:
        lines.append(f"* ALPN protocol: {alpn}")

    certificate = _call_ssl_method(ssl_object, "getpeercert")
    if certificate:
        lines.extend(_format_certificate(certificate))
    return lines


def _format_certificate(certificate: Mapping[str, Any]) -> list[str]:
    lines = ["* Server certificate:"]
    subject = _format_distinguished_name(certificate.get("subject"))
    issuer = _format_distinguished_name(certificate.get("issuer"))
    if subject:
        lines.append(f"*  subject: {subject}")
    if issuer:
        lines.append(f"*  issuer: {issuer}")
    if certificate.get("notBefore"):
        lines.append(f"*  starts: {certificate['notBefore']}")
    if certificate.get("notAfter"):
        lines.append(f"*  expires: {certificate['notAfter']}")
    san = certificate.get("subjectAltName")
    if san:
        names = ", ".join(f"{kind}:{value}" for kind, value in san)
        lines.append(f"*  subjectAltName: {names}")
    return lines


def _format_distinguished_name(value: Any) -> str:
    if not value:
        return ""

    parts = []
    for group in value:
        for key, item in group:
            parts.append(f"{key}={item}")
    return ", ".join(parts)


def _format_ssl_context(ssl_context: ssl.SSLContext) -> list[str]:
    lines = []
    verify_mode = ssl.VerifyMode(ssl_context.verify_mode).name
    lines.append(f"* TLS verify mode: {verify_mode}")
    lines.append(f"* TLS check hostname: {ssl_context.check_hostname}")
    minimum = _format_tls_version(ssl_context.minimum_version)
    maximum = _format_tls_version(ssl_context.maximum_version)
    if minimum or maximum:
        lines.append(f"* TLS versions: {minimum or 'default'} to {maximum or 'default'}")
    return lines


def _format_tls_version(value: ssl.TLSVersion) -> str:
    if value in {ssl.TLSVersion.MINIMUM_SUPPORTED, ssl.TLSVersion.MAXIMUM_SUPPORTED}:
        return ""
    return value.name.replace("TLSv", "TLS ").replace("_", ".")


def _format_unknown_event(name: str, info: Mapping[str, Any]) -> list[str]:
    lines = [f"* {name}"]
    for key, value in info.items():
        if key == "return_value":
            continue
        lines.append(f"*  {key}: {_format_value(value)}")
    return lines


def _format_socket_options(value: Iterable[Any]) -> str:
    return ", ".join(_format_value(option) for option in value)


def _format_exception(value: Any) -> str:
    if value is None:
        return "failed"
    return f"{value.__class__.__name__}: {value}"


def _format_value(value: Any) -> str:
    if isinstance(value, bytes):
        return _decode(value)
    return str(value)


def _format_addr(value: Any) -> str:
    if isinstance(value, tuple) and len(value) >= 2:
        return f"{value[0]}:{value[1]}"
    return str(value)


def _decode(value: Any) -> str:
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    if value is None:
        return ""
    return str(value)


def _get_extra_info(stream: Any, name: str) -> Any:
    get_extra_info = getattr(stream, "get_extra_info", None)
    if get_extra_info is None:
        return None
    try:
        return get_extra_info(name)
    except Exception:
        return None


def _call_ssl_method(ssl_object: Any, name: str) -> Any:
    method = getattr(ssl_object, name, None)
    if method is None:
        return None
    try:
        return method()
    except Exception:
        return None

if __name__ == "__main__":
    with httpx.Client(transport=HTTPTransportVerbose()) as client:
        client.get("https://lightcode.kartik.lol/install")