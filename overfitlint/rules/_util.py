"""Small AST helpers shared by the rules."""
from __future__ import annotations

import ast
import math
import re


def is_number(node: ast.AST) -> bool:
    """True for a finite int/float literal (bool excluded)."""
    return (
        isinstance(node, ast.Constant)
        and isinstance(node.value, (int, float))
        and not isinstance(node.value, bool)
        and math.isfinite(node.value)
    )


def is_str(node: ast.AST) -> bool:
    return isinstance(node, ast.Constant) and isinstance(node.value, str)


def sig_digits(value: float) -> int:
    """Count significant digits in a number's shortest round-trip repr.

    0.0857 -> 3, 0.1 -> 1, 20.0 -> 1, 0.3569571510008239 -> 16, 414.45 -> 5.
    """
    if not math.isfinite(value):
        return 0
    r = repr(abs(float(value)))
    if "e" in r:
        r = r.split("e")[0]
    return len(r.replace(".", "").strip("0"))


def name_hint(node: ast.AST) -> str:
    """Best-effort dotted identifier for a value node (for name heuristics)."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = name_hint(node.value)
        return f"{base}.{node.attr}" if base else node.attr
    if isinstance(node, ast.Call):
        return name_hint(node.func)
    if isinstance(node, ast.Subscript):
        return name_hint(node.value)
    return ""


def int_const(node: ast.AST | None):
    """Return the int value if node is an int literal, else None."""
    if isinstance(node, ast.Constant) and isinstance(node.value, int) and not isinstance(node.value, bool):
        return node.value
    return None


_TICKER_RE = re.compile(r"^[A-Z]{1,5}$")

# Common all-caps tokens that look like tickers but are not (OHLCV columns,
# enums, currency/indicator abbreviations, single letters).
_TICKER_STOPWORDS = frozenset({
    "OPEN", "HIGH", "LOW", "CLOSE", "OHLC", "OHLCV", "VWAP", "TWAP",
    "DATE", "TIME", "YEAR", "DAY", "WEEK",
    "NAN", "NA", "NULL", "NONE", "TRUE", "FALSE", "AND", "OR", "NOT", "XOR",
    "BUY", "SELL", "HOLD", "LONG", "SHORT", "FLAT", "CASH", "SIDE", "FEE",
    "USD", "EUR", "GBP", "JPY", "CNY", "HKD", "AUD", "CAD", "CHF",
    "ID", "IDS", "KEY", "VAL", "ROW", "COL", "IDX", "KEYS", "ARGS",
    "MIN", "MAX", "SUM", "AVG", "MEAN", "STD", "VAR", "RET", "VOL", "PCT", "ABS",
    "MA", "EMA", "SMA", "WMA", "RSI", "ATR", "ADX", "MACD", "BB", "KDJ", "CCI",
    "GET", "SET", "PUT", "CALL", "BID", "ASK", "TODO", "FIXME", "API", "URL", "CSV",
    "Q", "H", "K", "N", "T", "X", "Y", "Z", "V", "P", "R", "D", "M", "W", "A", "B", "C",
})


def is_tickerish(s: str) -> bool:
    return bool(_TICKER_RE.match(s)) and s not in _TICKER_STOPWORDS


def collection_tickers(node: ast.AST) -> list[str]:
    """If node is a set/list/tuple dominated by ticker-like strings, return them."""
    if not isinstance(node, (ast.Set, ast.List, ast.Tuple)):
        return []
    vals = [e.value for e in node.elts if is_str(e)]
    tick = [v for v in vals if is_tickerish(v)]
    # at least two, and tickers dominate (allow at most one non-ticker string).
    if len(tick) >= 2 and len(tick) >= max(2, len(vals) - 1):
        return tick
    return []


def named_numbers(tree: ast.AST):
    """Yield (name, value_node, lineno) for every name->number binding.

    Covers module/local assignments, annotated assignments, string-keyed dict
    entries, and numeric default arguments. Shared by excessive-params,
    hardcoded-anchors and rank-position-pick.
    """
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and is_number(node.value):
                    yield target.id, node.value, node.lineno
        elif isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name) and node.value is not None and is_number(node.value):
                yield node.target.id, node.value, node.lineno
        elif isinstance(node, ast.Dict):
            for key, val in zip(node.keys, node.values):
                if is_str(key) and is_number(val):
                    yield key.value, val, key.lineno
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            args = node.args
            positional = list(args.posonlyargs) + list(args.args)
            defaults = list(args.defaults)
            for arg, default in zip(positional[len(positional) - len(defaults):], defaults):
                if is_number(default):
                    yield arg.arg, default, arg.lineno
            for arg, default in zip(args.kwonlyargs, args.kw_defaults):
                if default is not None and is_number(default):
                    yield arg.arg, default, arg.lineno
