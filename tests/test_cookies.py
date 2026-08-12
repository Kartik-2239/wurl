from wurl.http.cookies import handle_cookie_args, read_cookies_from_file
from wurl.main import prepare_parser
from wurl.http.request import make_request

def test_args_cookies_read_write():
    import argparse
    import os
    import tempfile

    import httpx

    parser = prepare_parser(argparse.ArgumentParser())

    test_cookie_str = (
        "sessionid=abc123\n"
        "csrftoken=xyz789\n"
    )

    cookie = {
        "sessionid": "abc123",
        "csrftoken": "xyz789",
    }

    response_cookies = {
        "sessionid": "def456",
        "csrftoken": "uvw123",
    }

    with tempfile.TemporaryDirectory() as temp_cookie_file:
        cookie_file = os.path.join(temp_cookie_file, "cookies.txt")
        cookie_jar = os.path.join(temp_cookie_file, "output_cookie.txt")
        with open(cookie_file, "w") as f:
            f.write(test_cookie_str)
        args = parser.parse_args([
            "--cookie",
            cookie_file,
            "--cookie-jar",
            cookie_jar,
            "http://example.com",
        ])
        cookies = handle_cookie_args(args)
        assert cookies == cookie
        transport = httpx.MockTransport(
            lambda request: httpx.Response(
                200,
                content=b"OK",
                headers=[
                    ("Set-Cookie", "sessionid=def456"),
                    ("Set-Cookie", "csrftoken=uvw123"),
                ],
                request=request,
            )
        )
        for _ in make_request(args.url, method="GET", cookies=cookies, args=args, transport=transport):
            pass

        assert read_cookies_from_file(args.cookie_jar) == response_cookies
