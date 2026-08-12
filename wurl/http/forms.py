

import argparse
import os
from typing import Any


def add_forms_to_parser(parser: argparse.ArgumentParser):
    parser.add_argument(
        "-F", "--form",
        action="append",
        help="Send data as form data (application/x-www-form-urlencoded)",
    )

    parser.add_argument(
        "--form-string",
        action="append",
        help="Send data as form data (application/x-www-form-urlencoded) with string values",
    )

def resolve_forms(args: argparse.Namespace) -> tuple[dict[str, str], list[Any]]:
    form = args.form if args.form else []
    form_data = {}
    file_data: list[Any] = []
    form = {f.split("=", 1)[0]: f.split("=",1)[1] for f in form}

    for key, value in form.items():
        parts = value.strip().split(";")
        main = parts[0].strip()
        filename = None
        mime_type = None
        for part in parts:
            if part.strip().startswith("filename="):
                filename = part.split("=", 1)[1] or ""
            elif part.strip().startswith("type="):
                mime_type = part.split("=", 1)[1] or ""

        if main.startswith("@"):
            file_path = main[1:]
            if not os.path.isfile(file_path):
                raise ValueError(f"File {file_path} does not exist.")

            name = filename if filename else os.path.basename(file_path)
            with open(file_path, "rb") as file:
                content = file.read()
            if mime_type is None:
                file_data.append((key, (name, content)))
            else:
                file_data.append((key, (name, content, mime_type)))

        elif main.startswith("<"):
            file_path = main[1:]
            if not os.path.isfile(file_path):
                raise ValueError(f"File {file_path} does not exist.")

            with open(file_path, "r") as f:
                form_data[key] = f.read()
        else:
            form_data[key] = value

    form_string = args.form_string if args.form_string else []
    form_string = {f.split("=", 1)[0]: f.split("=",1)[1] for f in form_string}
    form_data.update(form_string)

    return form_data, file_data
