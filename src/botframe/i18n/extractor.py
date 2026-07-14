from __future__ import annotations

import ast
import sys
from collections.abc import Iterable, Mapping
from typing import Any, BinaryIO

type ExtractedMessage = tuple[
    int,
    str | None,
    str | tuple[str, ...],
    list[str],
]

TRANSLATABLE_CALLS = {
    "window",
    "ibutton",
    "rbutton",
}

POSITIONAL_TEXT_ARGUMENTS = {
    "window": 0,
}


def get_call_name(node: ast.Call) -> str | None:
    if isinstance(node.func, ast.Name):
        return node.func.id

    if isinstance(node.func, ast.Attribute):
        return node.func.attr

    return None


def get_static_string(node: ast.expr) -> str | None:
    if (
        isinstance(node, ast.Constant)
        and isinstance(node.value, str)
    ):
        return node.value

    return None


def find_keyword_text(node: ast.Call) -> ast.expr | None:
    for keyword in node.keywords:
        if keyword.arg == "text":
            return keyword.value

    return None


def find_text_argument(
    node: ast.Call,
    call_name: str,
) -> ast.expr | None:
    keyword_value = find_keyword_text(node)

    if keyword_value is not None:
        return keyword_value

    positional_index = POSITIONAL_TEXT_ARGUMENTS.get(
        call_name
    )

    if positional_index is None:
        return None

    if len(node.args) <= positional_index:
        return None

    return node.args[positional_index]


def format_location(
    filename: str | None,
    line: int,
) -> str:
    if filename:
        return f"{filename}:{line}"

    return f"line {line}"


def warn_dynamic_text(
    *,
    filename: str | None,
    node: ast.expr,
    call_name: str,
) -> None:
    location = format_location(
        filename,
        getattr(node, "lineno", 0),
    )

    if isinstance(node, ast.JoinedStr):
        explanation = "f-strings cannot be extracted"
    else:
        explanation = "dynamic expressions cannot be extracted"

    print(
        (
            f"Bot Frame i18n warning: {location}: "
            f"{explanation} in {call_name}(). "
            "Use a static template with placeholders."
        ),
        file=sys.stderr,
    )


class BotFrameExtractor(ast.NodeVisitor):
    def __init__(
        self,
        *,
        filename: str | None,
    ) -> None:
        self.filename = filename
        self.messages: list[ExtractedMessage] = []

    def visit_Call(self, node: ast.Call) -> Any:
        call_name = get_call_name(node)

        if call_name not in TRANSLATABLE_CALLS:
            self.generic_visit(node)
            return None

        text_node = find_text_argument(
            node,
            call_name,
        )

        if text_node is None:
            self.generic_visit(node)
            return None

        message = get_static_string(text_node)

        if message is None:
            warn_dynamic_text(
                filename=self.filename,
                node=text_node,
                call_name=call_name,
            )
            self.generic_visit(node)
            return None

        if message:
            self.messages.append(
                (
                    text_node.lineno,
                    None,
                    message,
                    [],
                )
            )

        self.generic_visit(node)
        return None


def extract_botframe(
    fileobj: BinaryIO,
    keywords: Mapping[str, Any],
    comment_tags: tuple[str, ...],
    options: Mapping[str, Any],
) -> Iterable[ExtractedMessage]:
    del keywords
    del comment_tags

    encoding = str(
        options.get(
            "encoding",
            "utf-8",
        )
    )

    filename_value = options.get("filename")
    filename = (
        str(filename_value)
        if filename_value is not None
        else None
    )

    source_bytes = fileobj.read()

    try:
        source = source_bytes.decode(encoding)
    except UnicodeDecodeError as error:
        location = filename or "<unknown file>"

        raise SyntaxError(
            f"Unable to decode {location} as {encoding}"
        ) from error

    tree = ast.parse(
        source,
        filename=filename or "<unknown>",
    )

    extractor = BotFrameExtractor(
        filename=filename,
    )
    extractor.visit(tree)

    yield from extractor.messages