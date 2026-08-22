import argparse
from urllib.parse import parse_qs

import httpx
from wurl.main import prepare_parser

from wurl.http.request import ResponseBody, ResponseHeader, ResponseStatus, make_request

def test_data_json():
    import argparse
    parser = prepare_parser(argparse.ArgumentParser(add_help=False))
    args = parser.parse_args([
        "--data",
        "{\"key1\": \"value1\", \"key2\": \"value2\"}",
        "http://example.com",
    ])
    # print(args.data)
    def handler(request):
        assert request.method == "POST"
        assert request.url == httpx.URL("http://example.com")
        assert request.headers["Content-Type"] == "application/json"
        assert request.content == b'{"key1": "value1", "key2": "value2"}'
        print(request.content)
        return httpx.Response(200, content=b"OK", request=request, headers={"Content-Type": "application/json"})
    events = list(make_request(args.url[0], method="POST", data=args.data, args=args, headers={"Content-Type": "application/json"}, include=True, transport=httpx.MockTransport(handler)))

    assert isinstance(events[0], ResponseStatus)
    assert events[0].status_code == 200
    assert events[0].http_version == "HTTP/1.1"
    assert any(
        isinstance(event, ResponseHeader)
        and event.key == "content-type"
        and event.value == "application/json"
        for event in events
    )
    assert isinstance(events[-1], ResponseBody)
    assert events[-1].byte_data == b"OK"

def test_form_text_fields():
    parser = prepare_parser(argparse.ArgumentParser(add_help=False))
    args = parser.parse_args([
        "-F", "name=Jack",
        "--form-string", "handle=@jack_handle",
        "http://example.com",
    ])

    def handler(request: httpx.Request):
        assert request.method == "POST"
        assert request.headers["Content-Type"] == "application/x-www-form-urlencoded"
        assert parse_qs(request.content.decode()) == {
            "name": ["Jack"],
            "handle": ["@jack_handle"],
        }
        return httpx.Response(200, content=b"OK", request=request)

    events = list(make_request(
        args.url[0],
        method="POST",
        args=args,
        transport=httpx.MockTransport(handler),
    ))

    assert isinstance(events[-1], ResponseBody)
    assert events[-1].byte_data == b"OK"


def test_form_file_upload(tmp_path):
    upload = tmp_path / "source.txt"
    upload.write_bytes(b"uploaded contents")
    parser = prepare_parser(argparse.ArgumentParser(add_help=False))
    args = parser.parse_args([
        "-F", f"document=@{upload};filename=report.txt;type=text/plain",
        "http://example.com",
    ])

    def handler(request: httpx.Request):
        content_type = request.headers["Content-Type"]
        assert content_type.startswith("multipart/form-data; boundary=")
        assert b'name="document"; filename="report.txt"' in request.content
        assert b"Content-Type: text/plain" in request.content
        assert b"uploaded contents" in request.content
        return httpx.Response(201, content=b"created", request=request)

    events = list(make_request(
        args.url[0],
        method="POST",
        args=args,
        include=True,
        transport=httpx.MockTransport(handler),
    ))

    assert isinstance(events[0], ResponseStatus)
    assert events[0].status_code == 201
    assert isinstance(events[-1], ResponseBody)
    assert events[-1].byte_data == b"created"


def test_form_field_reads_value_from_file(tmp_path):
    value_file = tmp_path / "description.txt"
    value_file.write_text("from a file")
    parser = prepare_parser(argparse.ArgumentParser(add_help=False))
    args = parser.parse_args([
        "-F", f"description=<{value_file}",
        "http://example.com",
    ])

    def handler(request: httpx.Request):
        assert request.headers["Content-Type"] == "application/x-www-form-urlencoded"
        assert request.content == b"description=from+a+file"
        return httpx.Response(200, content=b"OK", request=request)

    events = list(make_request(
        args.url[0],
        method="POST",
        args=args,
        transport=httpx.MockTransport(handler),
    ))

    assert isinstance(events[-1], ResponseBody)
    assert events[-1].byte_data == b"OK"