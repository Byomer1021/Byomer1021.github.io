"""
PayFlow AST node definitions.

Every node carries a `line` attribute (the source line it originated from)
so that later phases — type checker, interpreter — can produce error
messages anchored at the right place. The line is captured at the point
the parser commits to building the node.

The dump() method on Program prints an indented tree. Individual nodes
implement _dump(indent) which returns a list of lines.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Union


# ---------------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------------

class Node:
    """Base class. All AST nodes have a source line number."""
    line: int = 0

    def _dump(self, indent: int) -> List[str]:
        # Default fallback: class name and any non-private attributes.
        pad = "  " * indent
        out = [f"{pad}{type(self).__name__}"]
        for k, v in self.__dict__.items():
            if k == "line":
                continue
            if isinstance(v, Node):
                out.append(f"{pad}  {k}:")
                out.extend(v._dump(indent + 2))
            elif isinstance(v, list):
                out.append(f"{pad}  {k}: [")
                for item in v:
                    if isinstance(item, Node):
                        out.extend(item._dump(indent + 2))
                    else:
                        out.append(f"{pad}    {item!r}")
                out.append(f"{pad}  ]")
            else:
                out.append(f"{pad}  {k} = {v!r}")
        return out


# ---------------------------------------------------------------------------
# Program / top-level declarations
# ---------------------------------------------------------------------------

@dataclass
class Program(Node):
    decls: List["TopDecl"] = field(default_factory=list)
    line: int = 1

    def dump(self) -> str:
        lines = ["Program"]
        for d in self.decls:
            lines.extend(d._dump(1))
        return "\n".join(lines)


@dataclass
class RecordDecl(Node):
    name: str
    fields: List["Field"]
    line: int = 0


@dataclass
class Field(Node):
    name: str
    type_: "TypeRef"
    line: int = 0


@dataclass
class PlanDecl(Node):
    name: str
    fields: List["PlanField"]
    line: int = 0


@dataclass
class PlanField(Node):
    name: str
    value: "Expr"
    line: int = 0


@dataclass
class PaywallDecl(Node):
    name: str
    when_clauses: List["WhenClause"]
    default_block: "Block"
    line: int = 0


@dataclass
class WhenClause(Node):
    condition: "Expr"
    body: "Block"
    line: int = 0


@dataclass
class FnDecl(Node):
    name: str
    params: List["Param"]
    return_type: "TypeRef"
    body: "Block"
    line: int = 0


@dataclass
class Param(Node):
    name: str
    type_: "TypeRef"
    line: int = 0


TopDecl = Union[RecordDecl, PlanDecl, PaywallDecl, FnDecl]


# ---------------------------------------------------------------------------
# Types (as parsed; type checker resolves identifier types later)
# ---------------------------------------------------------------------------

@dataclass
class TypeRef(Node):
    """A type reference as written in the source.

    `name` is one of the primitive type keywords or a user-declared
    record name (an IDENT that the type checker will resolve).
    """
    name: str
    line: int = 0


# ---------------------------------------------------------------------------
# Statements / blocks
# ---------------------------------------------------------------------------

@dataclass
class Block(Node):
    stmts: List["Stmt"]
    line: int = 0


@dataclass
class ReturnStmt(Node):
    value: "Expr"
    line: int = 0


@dataclass
class IfStmt(Node):
    condition: "Expr"
    then_block: Block
    else_block: Optional[Block] = None
    line: int = 0


@dataclass
class ShowStmt(Node):
    """`show IDENT (at EXPR)? (with trial EXPR)? ;`

    We bake the at-most-once / fixed-order rule into the AST: the parser
    rejects repeated clauses, so by the time we have a ShowStmt either
    field is None or set exactly once.
    """
    plan_name: str
    at_price: Optional["Expr"] = None
    with_trial: Optional["Expr"] = None
    line: int = 0


@dataclass
class ExprStmt(Node):
    expr: "Expr"
    line: int = 0


Stmt = Union[ReturnStmt, IfStmt, ShowStmt, ExprStmt]


# ---------------------------------------------------------------------------
# Expressions
# ---------------------------------------------------------------------------

@dataclass
class BinOp(Node):
    """Arithmetic / comparison / logical binary expression.

    The `op` string is the source operator: '+', '-', '*', '/',
    '==', '!=', '<', '<=', '>', '>=', '&&', '||'.
    `split` gets its own node (SplitExpr) because its semantics
    (currency-aware, rounded) are different enough to warrant the
    distinction at the AST level — this makes type-checking and
    interpretation cleaner later.
    """
    op: str
    left: "Expr"
    right: "Expr"
    line: int = 0


@dataclass
class SplitExpr(Node):
    """Domain-specific left-associative `a split b`.

    Always has two operands. Chains like `a split b split c` build
    nested SplitExpr nodes left-associatively in the parser.
    """
    left: "Expr"
    right: "Expr"
    line: int = 0


@dataclass
class UnaryOp(Node):
    op: str  # '-' or '!'
    operand: "Expr"
    line: int = 0


@dataclass
class IntLit(Node):
    value: int
    line: int = 0


@dataclass
class DecLit(Node):
    value: str  # kept as string to avoid float rounding before semantic phase
    line: int = 0


@dataclass
class MoneyLit(Node):
    amount: str  # raw decimal text (e.g. "9.99")
    currency: str  # e.g. "USD"
    line: int = 0


@dataclass
class PercentLit(Node):
    value: str  # raw text without the trailing %
    line: int = 0


@dataclass
class DurationLit(Node):
    amount: int
    unit: str  # canonicalised: "day", "week", "month", "year"
    line: int = 0


@dataclass
class StringLit(Node):
    value: str
    line: int = 0


@dataclass
class BoolLit(Node):
    value: bool
    line: int = 0


@dataclass
class Ident(Node):
    name: str
    line: int = 0


@dataclass
class Call(Node):
    callee: str  # IDENT — PayFlow has no first-class function values
    args: List["Expr"]
    line: int = 0


@dataclass
class FieldAccess(Node):
    """`target . field_name` — record field projection.

    The target must evaluate to a record value at run time; the type
    checker resolves it via the record-type table.  Chaining is
    expressed by nesting (e.g. `a.b.c` is FieldAccess(FieldAccess(a, 'b'), 'c')).
    """
    target: "Expr"
    field_name: str
    line: int = 0


Expr = Union[
    BinOp, SplitExpr, UnaryOp,
    IntLit, DecLit, MoneyLit, PercentLit, DurationLit,
    StringLit, BoolLit, Ident, Call, FieldAccess,
]
