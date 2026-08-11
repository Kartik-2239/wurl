

def add_cookies_to_parser(parser):
    parser.add_argument(
        "-c", "--cookie-jar",
        help="Save cookies to a file"
    )

    parser.add_argument(
        "-b", "--cookie",
        action="append",
        help="Send cookies from a file"
    )

def handle_cookie_args(args) -> dict[str, str] | None:
    cookies_dict = {}
    cookies = args.cookie if args.cookie else []
    
    for cookie in cookies:
        if args.cookie:
            if "=" in cookie:
                key, value = cookie.split('=', 1)
                cookies_dict[key.strip()] = value.strip()
            else:
                cookies = read_cookies_from_file(cookie)
                cookies_dict.update(cookies)

    if len(cookies_dict) == 0:
        cookies_dict = None
    return cookies_dict


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