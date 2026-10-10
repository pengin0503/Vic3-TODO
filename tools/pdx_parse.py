"""Minimal Paradox script parser used to read game definitions.

Only what the catalog builder needs: comments, quoted strings, `key op value`
pairs, nested blocks and bare value lists. The result keeps duplicate keys as
a list of (key, op, value) tuples, because Paradox files repeat keys freely.
"""

import re

_TOKEN = re.compile(r'"(?:[^"\\]|\\.)*"|[{}]|>=|<=|!=|\?=|==|[=<>]|[^\s{}=<>!?"#]+')


class ParseError(ValueError):
    pass


def _strip_comments(text):
    out = []
    for line in text.splitlines():
        in_quote = False
        for i, ch in enumerate(line):
            if ch == '"':
                in_quote = not in_quote
            elif ch == "#" and not in_quote:
                line = line[:i]
                break
        out.append(line)
    return "\n".join(out)


def tokenize(text):
    if text.startswith("﻿"):
        text = text[1:]
    return _TOKEN.findall(_strip_comments(text))


class Block(list):
    """A list of (key, op, value) entries; bare values have key None."""

    def get(self, key, default=None):
        for k, _op, v in self:
            if k == key:
                return v
        return default

    def get_all(self, key):
        return [v for k, _op, v in self if k == key]

    def values(self):
        return [v for k, _op, v in self if k is None]


def _parse_block(tokens, pos, top_level):
    block = Block()
    while pos < len(tokens):
        tok = tokens[pos]
        if tok == "}":
            if top_level:
                raise ParseError("unbalanced closing brace at token %d" % pos)
            return block, pos + 1
        if tok == "{":
            value, pos = _parse_block(tokens, pos + 1, False)
            block.append((None, None, value))
            continue
        nxt = tokens[pos + 1] if pos + 1 < len(tokens) else None
        if nxt in ("=", "<", ">", "<=", ">=", "!=", "?=", "=="):
            if pos + 2 >= len(tokens):
                raise ParseError("missing value after %r" % tok)
            val_tok = tokens[pos + 2]
            if val_tok == "{":
                value, pos = _parse_block(tokens, pos + 3, False)
            else:
                value, pos = _unquote(val_tok), pos + 3
            block.append((_unquote(tok), nxt, value))
        else:
            block.append((None, None, _unquote(tok)))
            pos += 1
    if not top_level:
        raise ParseError("unclosed block")
    return block, pos


def _unquote(tok):
    if len(tok) >= 2 and tok[0] == '"' and tok[-1] == '"':
        return tok[1:-1]
    return tok


def parse(text):
    block, _ = _parse_block(tokenize(text), 0, True)
    return block


def brace_balance(text):
    """Return (ok, message) for brace balance outside quotes and comments."""
    depth = 0
    for lineno, line in enumerate(_strip_comments(text.lstrip("﻿")).splitlines(), 1):
        in_quote = False
        for ch in line:
            if ch == '"':
                in_quote = not in_quote
            elif not in_quote:
                if ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth < 0:
                        return False, "line %d: unexpected '}'" % lineno
        if in_quote:
            return False, "line %d: unterminated quote" % lineno
    if depth:
        return False, "%d unclosed '{'" % depth
    return True, "ok"
