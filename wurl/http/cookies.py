

def add_cookies_to_parser(parser):
    parser.add_argument(
        "-c",
        help="Save cookies to a file"
    )

    parser.add_argument(
        "-b",
        help="Send cookies from a file"
    )

def handle_cookie_args(args) -> dict[str, str] | None:
    cookies = {}
    if args.b:
        cookies = read_cookies_from_file(args.b)
    if len(cookies) == 0:
        cookies = None
    return cookies

def read_cookies_from_file(file_path: str) -> dict[str, str]:
    cookies = {}
    try:
        with open(file_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        cookies[key.strip()] = value.strip()
                    else:
                        raise ValueError(f"Invalid cookie format: '{line}'. Expected 'Key=Value'.")
    except FileNotFoundError:
        print(f"Cookie file '{file_path}' not found.")
    return cookies

def write_cookies_to_file(cookies: dict[str, str], file_path: str):
    if len(cookies) == 0:
        return
    with open(file_path, "w") as f:
        for key, value in cookies.items():
            f.write(f"{key}={value}\n")