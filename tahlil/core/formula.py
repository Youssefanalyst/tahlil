from __future__ import annotations
import ast
import math
import re
from typing import Any, Callable, Dict


_ALLOWED_BINOPS = (
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.Mod,
    ast.Pow,
    ast.FloorDiv,
)
_ALLOWED_UNARYOPS = (ast.UAdd, ast.USub, ast.Not)
_ALLOWED_BOOLOPS = (ast.And, ast.Or)
_ALLOWED_CMPOPS = (
    ast.Eq,
    ast.NotEq,
    ast.Lt,
    ast.LtE,
    ast.Gt,
    ast.GtE,
)
_ALLOWED_NODES = (
    ast.Expression,
    ast.BinOp,
    ast.UnaryOp,
    ast.Call,
    ast.BoolOp,
    ast.Compare,
    ast.Name,
    ast.Constant,
    ast.Load,
    ast.Store,
    ast.Del,
    ast.expr,
    ast.operator,
    ast.boolop,
    ast.cmpop,
    ast.unaryop,
)


def _rewrite_cell_refs(expr: str) -> str:
    pattern = re.compile(r"\b([A-Za-z]{1,3})(\d{1,6})(?::([A-Za-z]{1,3})(\d{1,6}))?\b")

    def repl(m: re.Match[str]) -> str:
        c1, r1 = m.group(1).upper(), m.group(2)
        c2, r2 = m.group(3), m.group(4)
        if c2 and r2:
            return f'RANGE("{c1}{r1}", "{c2.upper()}{r2}")'
        return f'CELL("{c1}{r1}")'

    return pattern.sub(repl, expr)


def _col_to_name(col: int) -> str:
    n = col + 1
    out = []
    while n:
        n, rem = divmod(n - 1, 26)
        out.append(chr(ord('A') + rem))
    return ''.join(reversed(out))


def _name_to_col(name: str) -> int:
    n = 0
    for ch in name.upper():
        if not ('A' <= ch <= 'Z'):
            raise ValueError("bad column")
        n = n * 26 + (ord(ch) - ord('A') + 1)
    return n - 1


def _address_to_index(addr: str) -> tuple[int, int]:
    m = re.fullmatch(r"([A-Za-z]{1,3})(\d{1,6})", addr.strip())
    if not m:
        raise ValueError("bad address")
    col = _name_to_col(m.group(1))
    row = int(m.group(2)) - 1
    if row < 0 or col < 0:
        raise ValueError("bad address")
    return row, col


def _index_to_address(row: int, col: int) -> str:
    return f"{_col_to_name(col)}{row + 1}"


def _validate(node: ast.AST) -> None:
    if not isinstance(node, _ALLOWED_NODES):
        raise ValueError("disallowed expression")
    for child in ast.iter_child_nodes(node):
        _validate(child)
    if isinstance(node, ast.BinOp) and not isinstance(node.op, _ALLOWED_BINOPS):
        raise ValueError("disallowed operator")
    if isinstance(node, ast.UnaryOp) and not isinstance(node.op, _ALLOWED_UNARYOPS):
        raise ValueError("disallowed operator")
    if isinstance(node, ast.BoolOp) and not isinstance(node.op, _ALLOWED_BOOLOPS):
        raise ValueError("disallowed boolean operator")
    if isinstance(node, ast.Compare):
        for op in node.ops:
            if not isinstance(op, _ALLOWED_CMPOPS):
                raise ValueError("disallowed comparison operator")
    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name):
            raise ValueError("disallowed call")
        name = node.func.id.upper()
        if name not in {"ABS", "ROUND", "MIN", "MAX", "SUM", "AVG", "AVERAGE", "CELL", "RANGE", "IF", "AND", "OR", "NOT"}:
            raise ValueError("disallowed function")


def _to_number(x: Any) -> float | None:
    if x is None:
        return None
    if isinstance(x, (int, float)):
        return float(x)
    try:
        return float(str(x))
    except Exception:
        return None


def evaluate_expression(expr: str, cell_resolver: Callable[[str], Any]) -> Any:
    s = _rewrite_cell_refs(expr)
    s = s.replace("<>", "!=")
    node = ast.parse(s, mode="eval")
    _validate(node)

    def CELL(address: str) -> Any:
        return cell_resolver(address)

    def RANGE(a1: str, a2: str) -> list[Any]:
        r1, c1 = _address_to_index(a1)
        r2, c2 = _address_to_index(a2)
        rlo, rhi = (r1, r2) if r1 <= r2 else (r2, r1)
        clo, chi = (c1, c2) if c1 <= c2 else (c2, c1)
        out: list[Any] = []
        for r in range(rlo, rhi + 1):
            for c in range(clo, chi + 1):
                out.append(cell_resolver(_index_to_address(r, c)))
        return out

    def SUM(*args: Any) -> float:
        nums = []
        for a in args:
            if isinstance(a, (list, tuple)):
                for v in a:
                    n = _to_number(v)
                    if n is not None:
                        nums.append(n)
            else:
                n = _to_number(a)
                if n is not None:
                    nums.append(n)
        return float(sum(nums))

    def MIN(*args: Any) -> float | None:
        vals = [n for n in (_to_number(a) for a in args) if n is not None]
        return min(vals) if vals else None

    def MAX(*args: Any) -> float | None:
        vals = [n for n in (_to_number(a) for a in args) if n is not None]
        return max(vals) if vals else None

    def AVG(*args: Any) -> float | None:
        vals = [n for n in (_to_number(a) for a in args) if n is not None]
        return float(sum(vals)) / len(vals) if vals else None

    def AVERAGE(*args: Any) -> float | None:
        return AVG(*args)

    def IF(cond: Any, a: Any, b: Any) -> Any:
        return a if bool(cond) else b

    def AND(*args: Any) -> bool:
        return all(bool(x) for x in args)

    def OR(*args: Any) -> bool:
        return any(bool(x) for x in args)

    def NOT(x: Any) -> bool:
        return not bool(x)

    env: Dict[str, Any] = {
        "ABS": abs,
        "ROUND": round,
        "MIN": MIN,
        "MAX": MAX,
        "SUM": SUM,
        "AVG": AVG,
        "AVERAGE": AVERAGE,
        "CELL": CELL,
        "RANGE": RANGE,
        "IF": IF,
        "PI": math.pi,
        "E": math.e,
        "TRUE": True,
        "FALSE": False,
        "AND": AND,
        "OR": OR,
        "NOT": NOT,
    }
    code = compile(node, "<formula>", "eval")
    return eval(code, {"__builtins__": {}}, env)
