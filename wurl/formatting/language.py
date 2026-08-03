

def resolve_language(content_type: str | None) -> str | None:
    if not content_type:
        return None

    mime = content_type.split(";", 1)[0].strip().lower()

    mapping = {
        "application/json": "json",
        "application/xml": "xml",
        "application/sql": "sql",
        "application/javascript": "javascript",
        "application/x-javascript": "javascript",
        "application/yaml": "yaml",
        "application/x-ndjson": "json",
        "application/jsonl": "json",
        "application/json-seq": "json",
    }

    if mime in mapping:
        return mapping[mime]

    if mime.startswith("text/"):
        lang = mime[5:].removeprefix("x-")

        aliases = {
            "plain": None,
            "javascript": "javascript",
            "xml": "xml",
            "html": "html",
            "css": "css",
            "markdown": "markdown",
            "x-python": "python",
            "python": "python",
            "x-go": "go",
            "go": "go",
            "x-java-source": "java",
            "x-c": "c",
            "x-c++src": "cpp",
            "x-shellscript": "bash",
        }

        return aliases.get(lang, lang)

    return None