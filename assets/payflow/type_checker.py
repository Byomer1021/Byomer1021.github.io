"""
PayFlow type checker (D2 Part 2).

Enforces the rules declared in D1 §4.5 / §4.7:

  - Strong typing: every type error is caught before execution.
  - The only implicit coercion is widening of `int` to `float` in mixed
    arithmetic.  No coercion for `money`, `percent`, `duration`, `string`.
  - Currency tags are part of `money`'s type identity: `USD` ≠ `EUR`.
  - Records use name equivalence: two record types are equivalent iff
    they share the declared name, regardless of structural similarity.

The checker is a hand-written tree walker (the textbook "visitor"
pattern dispatched on AST node class).  Type errors raise PayflowTypeError
— named with the `Payflow` prefix to avoid shadowing Python's built-in
TypeError — and every error carries a source line number.

The module is self-contained; it consumes the AST defined in
`ast_nodes.py` and produces no output on success.

Public entry points:
  - check(program)           run the type checker on a Program node;
                             raises PayflowTypeError on the first error.
  - PayflowTypeError         the exception type, with `.line` attribute.

Internal type language (see "Types" section below):
  - IntT, FloatT, BoolT, StringT      primitive scalar types
  - MoneyT(currency)                  currency-tagged money type
  - PercentT                          percent
  - DurationT                         duration (unit not in the type)
  - RecordT(name)                     named record type
  - VoidT                             internal sentinel for statements
  - ErrorT                            sentinel used after error recovery
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from ast_nodes import (
    Program, RecordDecl, Field, PlanDecl, PlanField,
    PaywallDecl, WhenClause, FnDecl, Param, Block, TypeRef,
    ReturnStmt, IfStmt, ShowStmt, ExprStmt,
    BinOp, SplitExpr, UnaryOp,
    IntLit, DecLit, MoneyLit, PercentLit, DurationLit,
    StringLit, BoolLit, Ident, Call, FieldAccess,
)


# ===========================================================================
# Errors
# ===========================================================================

class PayflowTypeError(Exception):
    """Raised on the first type error.  Always carries a line number.

    Named with the `Payflow` prefix to avoid shadowing Python's builtin.
    The message format mirrors the parser's:

        Type error at line N: <reason>
    """
    def __init__(self, line: int, reason: str):
        super().__init__(f"Type error at line {line}: {reason}")
        self.line = line
        self.reason = reason


# ===========================================================================
# Types (the internal type language)
# ===========================================================================
#
# A *type* in PayFlow's checker is one of the classes below.  Equality is
# defined by `__eq__` on each class:
#
#   - Primitive scalar types compare equal to instances of the same class.
#   - MoneyT(c1) == MoneyT(c2)  iff  c1 == c2 (currency tag part of identity).
#   - RecordT(n1) == RecordT(n2)  iff  n1 == n2 (name equivalence).
#
# `__repr__` produces the user-facing spelling used in error messages.

class Type:
    """Base class for PayFlow internal types."""
    def __repr__(self) -> str:    # pragma: no cover - subclasses override
        return type(self).__name__

    def __eq__(self, other) -> bool:
        return type(self) is type(other)

    def __hash__(self) -> int:
        return hash(type(self))


class IntT(Type):
    def __repr__(self) -> str: return "int"


class FloatT(Type):
    def __repr__(self) -> str: return "float"


class BoolT(Type):
    def __repr__(self) -> str: return "bool"


class StringT(Type):
    def __repr__(self) -> str: return "string"


@dataclass(eq=True, frozen=True)
class MoneyT(Type):
    """money carrying a currency tag.  Two MoneyT are equivalent iff their
    currency tags are equal — `USD` ≠ `EUR` even though both are money."""
    currency: str
    def __repr__(self) -> str: return f"money({self.currency})"


class PercentT(Type):
    def __repr__(self) -> str: return "percent"


class DurationT(Type):
    # Note: the unit (day/week/month/year) is a value-level property, not a
    # type-level one — `7 days + 1 month` is well-typed by §4.5.  Each
    # DurationT is interchangeable with every other DurationT.
    def __repr__(self) -> str: return "duration"


@dataclass(eq=True, frozen=True)
class RecordT(Type):
    """Named record type.  Name equivalence: two RecordT are equal iff
    their `name` fields are equal — see D1 §4.5 rationale."""
    name: str
    def __repr__(self) -> str: return self.name


class VoidT(Type):
    """Internal: type of a statement or a `show` clause.  Not user-visible."""
    def __repr__(self) -> str: return "<void>"


class ErrorT(Type):
    """Internal sentinel used in places where an error has already been
    raised and we want to keep walking the tree.  Currently unused — the
    checker stops on the first error — but reserved for future use."""
    def __repr__(self) -> str: return "<error>"


# ---------------------------------------------------------------------------
# Helpers over the type language
# ---------------------------------------------------------------------------

NUMERIC_PRIMITIVES = (IntT, FloatT)


def is_numeric(t: Type) -> bool:
    """True for int and float only.  money, percent, and duration are NOT
    numeric for the purposes of mixed-mode arithmetic — D1 §4.5."""
    return isinstance(t, NUMERIC_PRIMITIVES)


def numeric_result(a: Type, b: Type) -> Optional[Type]:
    """Result type of an int/float arithmetic op under our coercion rule:
    int + int → int; otherwise float (mixed mode widens int → float).
    Returns None if either operand is not numeric."""
    if not (is_numeric(a) and is_numeric(b)):
        return None
    if isinstance(a, FloatT) or isinstance(b, FloatT):
        return FloatT()
    return IntT()


# ===========================================================================
# Type checker
# ===========================================================================

# Map from PayFlow source-level primitive type names to internal Type
# instances.  Used when resolving TypeRef nodes from the parser.
_PRIMITIVE_BY_NAME = {
    "int":      IntT(),
    "float":    FloatT(),
    "bool":     BoolT(),
    "string":   StringT(),
    "percent":  PercentT(),
    "duration": DurationT(),
}


@dataclass
class FnSig:
    """Resolved signature of a user function."""
    params: List[Tuple[str, Type]]
    ret:    Type
    line:   int


class Scope:
    """Lexical scope: name → resolved type.  Chains via `parent`."""
    def __init__(self, parent: Optional["Scope"] = None):
        self.parent = parent
        self.bindings: Dict[str, Type] = {}

    def define(self, name: str, t: Type) -> None:
        # Shadowing within a single scope is forbidden; shadowing across
        # nested scopes is allowed and follows the usual lexical rules.
        if name in self.bindings:
            raise PayflowTypeError(
                0, f"`{name}` declared twice in the same scope"
            )
        self.bindings[name] = t

    def lookup(self, name: str) -> Optional[Type]:
        if name in self.bindings:
            return self.bindings[name]
        if self.parent is not None:
            return self.parent.lookup(name)
        return None


class TypeChecker:
    """Walks the AST and enforces D1 §4.5 / §4.7."""

    # -- entry point ---------------------------------------------------------

    def check(self, program: Program) -> None:
        # Two passes over the top level:
        #   1) collect record / plan / function declarations into tables
        #      so forward references work (D1 §4.6 commits to this).
        #   2) walk function bodies and paywall bodies with full info.

        self.records:  Dict[str, Dict[str, Type]] = {}  # name -> field types
        self.plans:    Dict[str, str] = {}              # name -> source line
        self.fns:      Dict[str, FnSig] = {}

        # Pass 1a: record declarations resolve types eagerly so later
        # record-typed fields work in pass 1b.  Records cannot reference
        # records that haven't been seen yet — we keep things linear here
        # for simplicity; if you want full forward reference among records,
        # split this further into "register names" then "resolve fields".
        for decl in program.decls:
            if isinstance(decl, RecordDecl):
                self._register_record(decl)

        # Pass 1b: plan and function signatures.
        for decl in program.decls:
            if isinstance(decl, PlanDecl):
                self._register_plan(decl)
            elif isinstance(decl, FnDecl):
                self._register_fn(decl)

        # Pass 2: function and paywall bodies.
        for decl in program.decls:
            if isinstance(decl, FnDecl):
                self._check_fn_body(decl)
            elif isinstance(decl, PaywallDecl):
                self._check_paywall(decl)
            # RecordDecl and PlanDecl have no executable body to check.

    # -- top-level registration ----------------------------------------------

    def _register_record(self, decl: RecordDecl) -> None:
        if decl.name in self.records:
            raise PayflowTypeError(
                decl.line, f"duplicate record declaration `{decl.name}`"
            )
        fields: Dict[str, Type] = {}
        for f in decl.fields:
            if f.name in fields:
                raise PayflowTypeError(
                    f.line,
                    f"duplicate field `{f.name}` in record `{decl.name}`",
                )
            fields[f.name] = self._resolve_type_ref(f.type_)
        self.records[decl.name] = fields

    def _register_plan(self, decl: PlanDecl) -> None:
        if decl.name in self.plans:
            raise PayflowTypeError(
                decl.line, f"duplicate plan declaration `{decl.name}`"
            )
        # Plans are values, not types.  We type-check each field-value
        # expression here in an empty scope (plans live at the program
        # level and may not reference function-local names).
        scope = Scope()
        for f in decl.fields:
            # Field-value expressions must type-check; we do not yet
            # constrain *which* type the field holds (no record-typed
            # plan declaration in the current language).
            self._check_expr(f.value, scope)
        self.plans[decl.name] = decl.line

    def _register_fn(self, decl: FnDecl) -> None:
        if decl.name in self.fns:
            raise PayflowTypeError(
                decl.line, f"duplicate function declaration `{decl.name}`"
            )
        seen = set()
        params: List[Tuple[str, Type]] = []
        for p in decl.params:
            if p.name in seen:
                raise PayflowTypeError(
                    p.line,
                    f"duplicate parameter `{p.name}` in function `{decl.name}`",
                )
            seen.add(p.name)
            params.append((p.name, self._resolve_type_ref(p.type_)))
        ret = self._resolve_type_ref(decl.return_type)
        self.fns[decl.name] = FnSig(params=params, ret=ret, line=decl.line)

    # -- type-reference resolution ------------------------------------------

    def _resolve_type_ref(self, ref: TypeRef) -> Type:
        """Resolve a source-level type reference to an internal Type.

        Tricky case: `money` as a type *annotation* has no currency tag at
        the source level.  We treat such annotations as MoneyT with a
        sentinel `"*"` meaning "any currency", and enforce currency
        equivalence at call sites and assignment sites by comparing the
        sentinel against concrete tags lazily.  See _types_compatible.
        """
        if ref.name == "money":
            return MoneyT(currency="*")
        if ref.name in _PRIMITIVE_BY_NAME:
            return _PRIMITIVE_BY_NAME[ref.name]
        if ref.name in self.records:
            return RecordT(name=ref.name)
        raise PayflowTypeError(
            ref.line, f"unknown type `{ref.name}`"
        )

    # -- type-compatibility helpers -----------------------------------------

    def _types_compatible(self, expected: Type, actual: Type) -> bool:
        """True if `actual` may be supplied where `expected` is required.

        Rules:
          - Identical types: compatible.
          - int → float widening: an actual `int` matches an expected `float`.
          - money currency wildcard: an expected `MoneyT("*")` (an unbound
            `money` annotation) matches any concrete `MoneyT(c)`.

        Anything else is incompatible.
        """
        if expected == actual:
            return True
        if isinstance(expected, FloatT) and isinstance(actual, IntT):
            return True
        if isinstance(expected, MoneyT) and isinstance(actual, MoneyT):
            return expected.currency == "*" or expected.currency == actual.currency
        return False

    # -- function-body and paywall-body checking -----------------------------

    def _check_fn_body(self, decl: FnDecl) -> None:
        sig = self.fns[decl.name]
        scope = Scope()
        for name, t in sig.params:
            scope.define(name, t)
        self._check_block(decl.body, scope, return_type=sig.ret)

    def _check_paywall(self, decl: PaywallDecl) -> None:
        # Implicit binding: every paywall body has `region: string` in scope.
        # See note at top of file — flagged as a design wrinkle in §4.6.
        scope = Scope()
        scope.define("region", StringT())
        for clause in decl.when_clauses:
            cond_t = self._check_expr(clause.condition, scope)
            if not isinstance(cond_t, BoolT):
                raise PayflowTypeError(
                    clause.line,
                    f"`when` condition must be bool, got {cond_t}",
                )
            # Each clause body is checked in a fresh inner scope chained
            # off the paywall scope, so `region` is visible inside it.
            self._check_block(clause.body, Scope(parent=scope),
                              return_type=None)
        self._check_block(decl.default_block, Scope(parent=scope),
                          return_type=None)

    # -- statement checking --------------------------------------------------

    def _check_block(self, block: Block, scope: Scope,
                     return_type: Optional[Type]) -> None:
        for stmt in block.stmts:
            self._check_stmt(stmt, scope, return_type)

    def _check_stmt(self, stmt, scope: Scope,
                    return_type: Optional[Type]) -> None:
        if isinstance(stmt, ReturnStmt):
            if return_type is None:
                raise PayflowTypeError(
                    stmt.line,
                    "`return` is not allowed outside a function body",
                )
            actual = self._check_expr(stmt.value, scope)
            if not self._types_compatible(return_type, actual):
                raise PayflowTypeError(
                    stmt.line,
                    f"function declares return type {return_type}, "
                    f"but `return` produces {actual}",
                )
            return

        if isinstance(stmt, IfStmt):
            cond_t = self._check_expr(stmt.condition, scope)
            if not isinstance(cond_t, BoolT):
                raise PayflowTypeError(
                    stmt.line,
                    f"`if` condition must be bool, got {cond_t}",
                )
            self._check_block(stmt.then_block, Scope(parent=scope), return_type)
            if stmt.else_block is not None:
                self._check_block(stmt.else_block, Scope(parent=scope),
                                  return_type)
            return

        if isinstance(stmt, ShowStmt):
            if stmt.plan_name not in self.plans:
                raise PayflowTypeError(
                    stmt.line,
                    f"unknown plan `{stmt.plan_name}` in `show` statement",
                )
            if stmt.at_price is not None:
                t = self._check_expr(stmt.at_price, scope)
                if not isinstance(t, MoneyT):
                    raise PayflowTypeError(
                        stmt.line,
                        f"`show … at <expr>` requires money, got {t}",
                    )
            if stmt.with_trial is not None:
                t = self._check_expr(stmt.with_trial, scope)
                if not isinstance(t, DurationT):
                    raise PayflowTypeError(
                        stmt.line,
                        f"`show … with trial <expr>` requires duration, got {t}",
                    )
            return

        if isinstance(stmt, ExprStmt):
            self._check_expr(stmt.expr, scope)
            return

        raise PayflowTypeError(
            getattr(stmt, "line", 0),
            f"internal: unknown statement node {type(stmt).__name__}",
        )

    # -- expression checking -------------------------------------------------

    def _check_expr(self, expr, scope: Scope) -> Type:
        """Return the inferred type of `expr`.  Raises on any error."""
        # Literals
        if isinstance(expr, IntLit):       return IntT()
        if isinstance(expr, DecLit):       return FloatT()
        if isinstance(expr, BoolLit):      return BoolT()
        if isinstance(expr, StringLit):    return StringT()
        if isinstance(expr, PercentLit):   return PercentT()
        if isinstance(expr, MoneyLit):     return MoneyT(currency=expr.currency)
        if isinstance(expr, DurationLit):  return DurationT()

        if isinstance(expr, Ident):
            t = scope.lookup(expr.name)
            if t is None:
                raise PayflowTypeError(
                    expr.line, f"undefined name `{expr.name}`"
                )
            return t

        if isinstance(expr, Call):
            return self._check_call(expr, scope)

        if isinstance(expr, UnaryOp):
            return self._check_unary(expr, scope)

        if isinstance(expr, BinOp):
            return self._check_binop(expr, scope)

        if isinstance(expr, SplitExpr):
            return self._check_split(expr, scope)

        if isinstance(expr, FieldAccess):
            return self._check_field_access(expr, scope)

        raise PayflowTypeError(
            getattr(expr, "line", 0),
            f"internal: unknown expression node {type(expr).__name__}",
        )

    def _check_field_access(self, expr: FieldAccess, scope: Scope) -> Type:
        target_t = self._check_expr(expr.target, scope)
        if not isinstance(target_t, RecordT):
            raise PayflowTypeError(
                expr.line,
                f"field access requires a record value, got {target_t}",
            )
        fields = self.records.get(target_t.name)
        if fields is None:
            # Defensive: a RecordT got constructed with a name not in
            # the table.  Shouldn't happen in well-formed pipelines.
            raise PayflowTypeError(
                expr.line,
                f"internal: record `{target_t.name}` has no field table",
            )
        if expr.field_name not in fields:
            raise PayflowTypeError(
                expr.line,
                f"record `{target_t.name}` has no field `{expr.field_name}`",
            )
        return fields[expr.field_name]

    def _check_call(self, expr: Call, scope: Scope) -> Type:
        sig = self.fns.get(expr.callee)
        if sig is None:
            raise PayflowTypeError(
                expr.line, f"call to undefined function `{expr.callee}`"
            )
        if len(expr.args) != len(sig.params):
            raise PayflowTypeError(
                expr.line,
                f"function `{expr.callee}` expects {len(sig.params)} "
                f"argument(s), got {len(expr.args)}",
            )
        for i, (arg_expr, (pname, ptype)) in enumerate(
                zip(expr.args, sig.params), start=1):
            arg_type = self._check_expr(arg_expr, scope)
            if not self._types_compatible(ptype, arg_type):
                # This is where name equivalence does its job:
                # passing a RecordT("RefundRule") where the parameter
                # type is RecordT("Plan") fails here even though the
                # records may be structurally identical.
                raise PayflowTypeError(
                    arg_expr.line if hasattr(arg_expr, "line") else expr.line,
                    f"function `{expr.callee}` expects argument {i} "
                    f"({pname}) of type {ptype}, got {arg_type}",
                )
        return sig.ret

    def _check_unary(self, expr: UnaryOp, scope: Scope) -> Type:
        t = self._check_expr(expr.operand, scope)
        if expr.op == "-":
            if not is_numeric(t):
                raise PayflowTypeError(
                    expr.line,
                    f"unary `-` requires int or float, got {t}",
                )
            return t
        if expr.op == "!":
            if not isinstance(t, BoolT):
                raise PayflowTypeError(
                    expr.line,
                    f"unary `!` requires bool, got {t}",
                )
            return BoolT()
        raise PayflowTypeError(
            expr.line, f"internal: unknown unary operator `{expr.op}`",
        )

    def _check_binop(self, expr: BinOp, scope: Scope) -> Type:
        op = expr.op
        lt = self._check_expr(expr.left, scope)
        rt = self._check_expr(expr.right, scope)

        # Logical ----------------------------------------------------------
        if op in ("&&", "||"):
            if not (isinstance(lt, BoolT) and isinstance(rt, BoolT)):
                raise PayflowTypeError(
                    expr.line,
                    f"`{op}` requires bool operands, got {lt} and {rt}",
                )
            return BoolT()

        # Comparison -------------------------------------------------------
        if op in ("==", "!="):
            # Equality across any pair of equal types.  No cross-type
            # equality (e.g., comparing money to float is a type error).
            if not self._types_compatible(lt, rt) \
                    and not self._types_compatible(rt, lt):
                raise PayflowTypeError(
                    expr.line,
                    f"cannot compare {lt} and {rt} for equality",
                )
            return BoolT()

        if op in ("<", "<=", ">", ">="):
            # Ordered comparison: numeric, money (same currency), or duration.
            if is_numeric(lt) and is_numeric(rt):
                return BoolT()
            if isinstance(lt, MoneyT) and isinstance(rt, MoneyT):
                if lt.currency != rt.currency:
                    raise PayflowTypeError(
                        expr.line,
                        f"cannot order money in different currencies "
                        f"({lt.currency} vs {rt.currency})",
                    )
                return BoolT()
            if isinstance(lt, DurationT) and isinstance(rt, DurationT):
                return BoolT()
            raise PayflowTypeError(
                expr.line,
                f"`{op}` requires numeric, money, or duration operands; "
                f"got {lt} and {rt}",
            )

        # Arithmetic -------------------------------------------------------
        if op in ("+", "-", "*", "/"):
            # int/float case (the one place coercion happens)
            num = numeric_result(lt, rt)
            if num is not None:
                return num

            # money ± money (additive only)
            if op in ("+", "-") and isinstance(lt, MoneyT) and isinstance(rt, MoneyT):
                if lt.currency != rt.currency:
                    raise PayflowTypeError(
                        expr.line,
                        f"cannot {op} money in different currencies "
                        f"({lt.currency} vs {rt.currency})",
                    )
                return MoneyT(currency=lt.currency)

            # money * int|float  and  int|float * money
            if op == "*":
                if isinstance(lt, MoneyT) and is_numeric(rt):
                    return MoneyT(currency=lt.currency)
                if is_numeric(lt) and isinstance(rt, MoneyT):
                    return MoneyT(currency=rt.currency)

            # money / int|float  →  money (scaling down)
            if op == "/" and isinstance(lt, MoneyT) and is_numeric(rt):
                return MoneyT(currency=lt.currency)

            # duration + duration  →  duration (units handled at runtime)
            if op in ("+", "-") and isinstance(lt, DurationT) and isinstance(rt, DurationT):
                return DurationT()

            # Explicitly refused, to make the message specific:
            if isinstance(lt, MoneyT) and is_numeric(rt) and op in ("+", "-"):
                raise PayflowTypeError(
                    expr.line,
                    f"cannot {op} {rt} to/from money; PayFlow does not "
                    f"coerce numeric types to money (D1 §4.5)",
                )
            if isinstance(lt, PercentT) or isinstance(rt, PercentT):
                raise PayflowTypeError(
                    expr.line,
                    f"`percent` does not participate in arithmetic; use "
                    f"`split` instead (got {lt} {op} {rt})",
                )

            raise PayflowTypeError(
                expr.line,
                f"`{op}` is not defined on {lt} and {rt}",
            )

        raise PayflowTypeError(
            expr.line, f"internal: unknown binary operator `{op}`",
        )

    def _check_split(self, expr: SplitExpr, scope: Scope) -> Type:
        lt = self._check_expr(expr.left, scope)
        rt = self._check_expr(expr.right, scope)
        if not isinstance(lt, MoneyT):
            raise PayflowTypeError(
                expr.line,
                f"left operand of `split` must be money, got {lt}",
            )
        if not isinstance(rt, PercentT):
            raise PayflowTypeError(
                expr.line,
                f"right operand of `split` must be percent, got {rt}",
            )
        # Result currency is the *left* operand's currency (D1 §4.4.2 [SPLIT]).
        return MoneyT(currency=lt.currency)


# ===========================================================================
# Public entry point
# ===========================================================================

def check(program: Program) -> None:
    """Run the type checker on a parsed Program.  Raises PayflowTypeError
    on the first error; returns None on success."""
    TypeChecker().check(program)
