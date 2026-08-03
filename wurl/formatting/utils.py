def format_json(content: bytes, indent: int = 2):
    import json
    try:
        raw = content.decode()
        formatted = json.dumps(json.loads(raw), indent=indent)
        return formatted.encode()
    except json.JSONDecodeError:
        return content


def is_printable(data: bytes) -> bool:
    try:
        data.decode("utf-8")
        return True
    except UnicodeDecodeError:
        return False