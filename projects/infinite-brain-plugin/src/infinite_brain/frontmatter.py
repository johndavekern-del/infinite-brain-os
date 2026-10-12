"""Minimal YAML-subset frontmatter parser, standard library only.

The Infinite Brain repo uses a conservative slice of YAML in markdown frontmatter:
flat scalar keys, inline lists (``aliases: ["a", "b"]``), block sequences of scalars,
block sequences of single-level mappings (the ``edges:`` shape), and one level of
nested mappings. This parser covers exactly that slice so the plugin has zero
third-party dependencies. It is deliberately strict about what it supports and
tolerant about skipping lines it does not recognise.

Supported value forms:

- quoted or bare scalars, integers, floats, booleans, null
- inline lists: ``[a, "b, c", 3]``
- block sequences of scalars or of single-level mappings
- nested blocks one level deep under a mapping key
"""

from __future__ import annotations

import re
from typing import Any

_KEY_RE = re.compile(r"^[A-Za-z0-9_]+\s*:")


def _parse_scalar(text: str) -> Any:
    text = text.strip()
    if text == "":
        return None
    if len(text) >= 2 and text[0] == text[-1] and text[0] in ("\"", "'"):
        return text[1:-1]
    low = text.lower()
    if low in ("null", "~", "none"):
        return None
    if low == "true":
        return True
    if low == "false":
        return False
    try:
        return int(text)
    except ValueError:
        pass
    try:
        return float(text)
    except ValueError:
        pass
    return text


def _split_inline(inner: str) -> list[str]:
    """Split an inline list body on commas that sit outside quotes."""
    parts: list[str] = []
    buf = ""
    quote: str | None = None
    for ch in inner:
        if quote:
            buf += ch
            if ch == quote:
                quote = None
        elif ch in ("\"", "'"):
            quote = ch
            buf += ch
        elif ch == ",":
            parts.append(buf)
            buf = ""
        else:
            buf += ch
    if buf.strip() != "":
        parts.append(buf)
    return [p.strip() for p in parts]


def _parse_value(text: str) -> Any:
    text = text.strip()
    if text.startswith("[[") :
        return _parse_scalar(text)
    if text.startswith("[") and text.endswith("]"):
        inner = text[1:-1].strip()
        if inner == "":
            return []
        return [_parse_scalar(p) for p in _split_inline(inner)]
    return _parse_scalar(text)


def _logical_lines(text: str) -> list[tuple[int, str]]:
    out: list[tuple[int, str]] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped == "" or stripped.startswith("#"):
            continue
        indent = len(line) - len(line.lstrip(" "))
        out.append((indent, stripped))
    return out


def _parse_block(lines: list[tuple[int, str]], i: int, indent: int) -> tuple[Any, int]:
    if i >= len(lines):
        return None, i
    if lines[i][1] == "-" or lines[i][1].startswith("- "):
        return _parse_list(lines, i, indent)
    return _parse_map(lines, i, indent)


def _parse_list(lines: list[tuple[int, str]], i: int, indent: int) -> tuple[list, int]:
    items: list[Any] = []
    while i < len(lines) and lines[i][0] == indent and (
        lines[i][1] == "-" or lines[i][1].startswith("- ")
    ):
        content = lines[i][1][1:].strip()
        i += 1
        if content == "":
            if i < len(lines) and lines[i][0] > indent:
                value, i = _parse_block(lines, i, lines[i][0])
                items.append(value)
            else:
                items.append(None)
        elif _KEY_RE.match(content):
            key, _, rest = content.partition(":")
            key = key.strip()
            rest = rest.strip()
            item: dict[str, Any] = {}
            if rest:
                item[key] = _parse_value(rest)
            if i < len(lines) and lines[i][0] > indent:
                sub, i = _parse_map(lines, i, lines[i][0])
                if rest == "" and key not in sub:
                    # The nested block is the value of this key.
                    item[key] = sub
                else:
                    item.update(sub)
            elif rest == "":
                item[key] = None
            items.append(item)
        else:
            items.append(_parse_value(content))
    return items, i


def _parse_map(lines: list[tuple[int, str]], i: int, indent: int) -> tuple[dict, int]:
    data: dict[str, Any] = {}
    while i < len(lines) and lines[i][0] == indent and not lines[i][1].startswith("- "):
        content = lines[i][1]
        if not _KEY_RE.match(content):
            i += 1
            continue
        key, _, rest = content.partition(":")
        key = key.strip()
        rest = rest.strip()
        i += 1
        if rest:
            data[key] = _parse_value(rest)
        elif i < len(lines) and lines[i][0] > indent:
            value, i = _parse_block(lines, i, lines[i][0])
            data[key] = value
        else:
            data[key] = None
    return data, i


def loads(text: str) -> dict[str, Any]:
    """Parse a YAML-subset document into a dict."""
    lines = _logical_lines(text)
    if not lines:
        return {}
    data, _ = _parse_map(lines, 0, lines[0][0])
    return data


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    """Split markdown text into (frontmatter dict, body).

    Returns ``({}, text)`` unchanged when the file does not open with a ``---``
    fence, which is how non-node markdown is excluded from the index.
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text
    for pos in range(1, len(lines)):
        if lines[pos].strip() == "---":
            meta = loads("\n".join(lines[1:pos]))
            body = "\n".join(lines[pos + 1 :]).strip()
            return meta, body
    return {}, text
