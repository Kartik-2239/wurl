

def format_json(content: bytes):
    import json
    raw = content.decode()
    formatted = json.dumps(json.loads(raw), indent=2)
    return formatted.encode()


def is_printable(data: bytes) -> bool:
    try:
        data.decode("utf-8")
        return True
    except UnicodeDecodeError:
        return False