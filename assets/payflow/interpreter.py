"""
PayFlow interpreter (D2 Part 2).

Executes an AST that has already been accepted by the type checker.
The implementation follows the operational semantics of D1 §4.4
literally where possible:

  * §4.4.2 [SPLIT]   — `e1 split e2` evaluates the left operand first,
                       then the right; rounds the result to the minor
                       unit of e1's currency with banker's rounding
                       (round-half-to-even).  Rounding happens AT EACH
                       step of a chain, not once at the end.

  * §4.4.3 [PAYWALL] — when-clauses are tried in source order; the
                       first whose condition evaluates to true runs its
                       body and the rest are skipped.  If none matches,
                       the (mandatory) default block runs.  The host
                       supplies `region: string` to the paywall body's
                       environment.

  * §4.7             — `&&` and `||` short-circuit left-to-right.
                       Operand evaluation order is strictly left-to-right
                       everywhere.  Functions take arguments by value.

Public interface
----------------
    Interpreter().run(program, region="US")  -> None
        Runs every paywall declaration in `program`, in source order,
        with the supplied region.  Side effects (the `show` outputs)
        go to sys.stdout.

    RuntimeFault                            : Exception class for
        user-facing runtime errors (division by zero, percent out of
        range, etc.).  Always carries a `.line` attribute.
"""

import sys
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_EVEN, getcontext
from typing import Dict, List, Optional

from ast_nodes import (
    Program, RecordDecl, PlanDecl, PlanField,
    PaywallDecl, FnDecl,
    Block, ReturnStmt, IfStmt, ShowStmt, ExprStmt,
    BinOp, SplitExpr, UnaryOp,
    IntLit, DecLit, MoneyLit, PercentLit, DurationLit,
    StringLit, BoolLit, Ident, Call, FieldAccess,
)


# Plenty of precision for intermediate split calculations; final values
# are quantized to currency minor-unit precision in `round_money`.
getcontext().prec = 50


# ===========================================================================
# Errors and internal signals
# ===========================================================================

class RuntimeFault(Exception):
    """User-facing runtime error.  Always carries a source line."""
    def __init__(self, line: int, reason: str):
        super().__init__(f"Runtime error at line {line}: {reason}")
        self.line = line
        self.reason = reason


class _ReturnSignal(Exception):
    """Internal: unwinds a function call when `return` is executed.

    Not a RuntimeFault — never escapes to the user.  Caught only in
    `_call`.
    """
    def __init__(self, value):
        self.value = value


# ===========================================================================
# Currency table
# ===========================================================================
#
# Minor-unit precision per currency.  This is the digit count we quantize
# to in `round_money`.  Adding a new currency here is the only change
# needed to support it at runtime; the lexer keyword list also needs
# updating in lockstep.

MINOR_UNITS = {
    "USD": 2,
    "EUR": 2,
    "GBP": 2,
    "TRY": 2,
    "JPY": 0,
}


def _quantum_for(currency: str) -> Decimal:
    """Return the Decimal `0.01` (or whatever the precision dictates)
    used as the quantize target for the given currency."""
    digits = MINOR_UNITS[currency]
    if digits == 0:
        return Decimal("1")
    return Decimal("1").scaleb(-digits)   # 10^-digits


def round_money(amount: Decimal, currency: str) -> Decimal:
    """Quantize `amount` to the currency's minor-unit precision using
    banker's rounding (round-half-to-even).  Implements `round_c` from
    D1 §4.4.1."""
    return amount.quantize(_quantum_for(currency), rounding=ROUND_HALF_EVEN)


# ===========================================================================
# Runtime values
# ===========================================================================
#
# These are the values that flow through the interpreter at run time.
# Python primitives stand in for `int`, `float`, `bool`, and `string`;
# the other PayFlow types get dedicated wrappers so we can dispatch on
# type and format them for output.

@dataclass(frozen=True)
class MoneyVal:
    amount:   Decimal      # always already quantized to the currency's precision
    currency: str

    def __str__(self) -> str:
        # Use the currency's minor-unit precision so e.g. JPY prints
        # as "199 JPY" and USD as "9.99 USD".
        digits = MINOR_UNITS.get(self.currency, 2)
        return f"{self.amount:.{digits}f} {self.currency}"


@dataclass(frozen=True)
class PercentVal:
    value: Decimal         # mathematical percent, e.g. Decimal("30") for 30%

    def __str__(self) -> str:
        # Strip a trailing ".0" for tidy output of whole percents.
        s = format(self.value, "f")
        if "." in s:
            s = s.rstrip("0").rstrip(".")
        return f"{s}%"


@dataclass(frozen=True)
class DurationVal:
    amount: int
    unit:   str            # canonical singular: "day", "week", "month", "year"

    def __str__(self) -> str:
        # Print plural form when amount != 1, to match the source spelling.
        unit = self.unit if self.amount == 1 else self.unit + "s"
        return f"{self.amount} {unit}"


# ===========================================================================
# Environment
# ===========================================================================

class _Env:
    """Lexical environment.  Names map to runtime values."""
    def __init__(self, parent: Optional["_Env"] = None):
        self.parent = parent
        self.bindings: Dict[str, object] = {}

    def define(self, name: str, value) -> None:
        self.bindings[name] = value

    def lookup(self, name: str, line: int):
        if name in self.bindings:
            return self.bindings[name]
        if self.parent is not None:
            return self.parent.lookup(name, line)
        # The type checker should have caught this; if we get here
        # something has drifted between the two passes.
        raise RuntimeFault(line, f"internal: name `{name}` not bound at runtime")


# ===========================================================================
# Interpreter
# ===========================================================================

class Interpreter:
    """Walk an AST and execute it."""

    def __init__(self, out=None):
        # `out` is the stream `show` writes to.  Defaults to sys.stdout
        # but can be overridden in tests for capture.
        self.out = out if out is not None else sys.stdout
        # Top-level tables populated in run().
        self.records: Dict[str, RecordDecl] = {}
        self.plans:   Dict[str, PlanDecl]   = {}
        self.fns:     Dict[str, FnDecl]     = {}

    # -- entry point ---------------------------------------------------------

    def run(self, program: Program, region: str = "US") -> None:
        """Execute every paywall in source order with the given region."""
        # Pass 1: collect declarations.  Type checker already validated
        # everything; here we just index for lookup.
        for decl in program.decls:
            if   isinstance(decl, RecordDecl):  self.records[decl.name] = decl
            elif isinstance(decl, PlanDecl):    self.plans[decl.name]   = decl
            elif isinstance(decl, FnDecl):      self.fns[decl.name]     = decl

        # Pass 2: evaluate every paywall.  Plan-field expressions are
        # evaluated lazily — on demand when a `show` references the plan.
        for decl in program.decls:
            if isinstance(decl, PaywallDecl):
                self._run_paywall(decl, region)

    # -- paywall (§4.4.3) ----------------------------------------------------

    def _run_paywall(self, decl: PaywallDecl, region: str) -> None:
        # The paywall's environment carries the host-supplied region.
        # Each when-body / default-body opens a fresh nested scope so
        # any (future) locals don't leak between clauses.
        env = _Env()
        env.define("region", region)

        for clause in decl.when_clauses:
            cond = self._eval(clause.condition, env)
            if not isinstance(cond, bool):
                # Defensive — type checker should have caught this.
                raise RuntimeFault(
                    clause.line,
                    f"internal: when-condition produced non-bool {cond!r}",
                )
            if cond:
                self._exec_block(clause.body, _Env(parent=env))
                return  # [PAYWALL-MATCH]: skip remaining clauses

        # No clause matched -> [PAYWALL-DEFAULT].
        self._exec_block(decl.default_block, _Env(parent=env))

    # -- statements ----------------------------------------------------------

    def _exec_block(self, block: Block, env: _Env) -> None:
        for stmt in block.stmts:
            self._exec(stmt, env)

    def _exec(self, stmt, env: _Env) -> None:
        if isinstance(stmt, ReturnStmt):
            value = self._eval(stmt.value, env)
            raise _ReturnSignal(value)

        if isinstance(stmt, IfStmt):
            cond = self._eval(stmt.condition, env)
            if cond is True:
                self._exec_block(stmt.then_block, _Env(parent=env))
            elif stmt.else_block is not None:
                self._exec_block(stmt.else_block, _Env(parent=env))
            return

        if isinstance(stmt, ShowStmt):
            self._exec_show(stmt, env)
            return

        if isinstance(stmt, ExprStmt):
            self._eval(stmt.expr, env)
            return

        raise RuntimeFault(
            getattr(stmt, "line", 0),
            f"internal: unknown statement {type(stmt).__name__}",
        )

    def _exec_show(self, stmt: ShowStmt, env: _Env) -> None:
        plan = self.plans.get(stmt.plan_name)
        if plan is None:
            # Type checker should have caught this.
            raise RuntimeFault(
                stmt.line, f"internal: unknown plan `{stmt.plan_name}`",
            )

        # Compute the at-price and trial values, defaulting to the plan's
        # declared fields if no clause-level override is given.
        if stmt.at_price is not None:
            price_val = self._eval(stmt.at_price, env)
        else:
            price_val = self._plan_field(plan, "price", stmt.line)

        if stmt.with_trial is not None:
            trial_val = self._eval(stmt.with_trial, env)
        else:
            # The default trial is taken from the plan if it has one;
            # if the plan has no `trial` field, we just omit it.
            trial_val = self._plan_field(plan, "trial", stmt.line, optional=True)

        # Format and emit.  Matches the requested format:
        #   "SHOWING Plan Pro at 8.99 EUR with trial 14 days"
        parts = [f"SHOWING Plan {plan.name}", f"at {price_val}"]
        if trial_val is not None:
            parts.append(f"with trial {trial_val}")
        print(" ".join(parts), file=self.out)

    def _plan_field(self, plan: PlanDecl, field_name: str, line: int,
                    *, optional: bool = False):
        """Look up a named field in a plan's declaration and evaluate
        its initializer expression.  If `optional` and the field is
        absent, returns None instead of erroring."""
        for f in plan.fields:
            if f.name == field_name:
                return self._eval(f.value, _Env())
        if optional:
            return None
        raise RuntimeFault(
            line,
            f"plan `{plan.name}` has no field `{field_name}` required by `show`",
        )

    # -- expressions ---------------------------------------------------------

    def _eval(self, expr, env: _Env):
        # Literals -----------------------------------------------------------
        if isinstance(expr, IntLit):      return expr.value
        if isinstance(expr, BoolLit):     return expr.value
        if isinstance(expr, StringLit):   return expr.value
        if isinstance(expr, DecLit):
            # We kept the raw text in parsing precisely so we can build a
            # Decimal without going through float.
            return Decimal(expr.value)
        if isinstance(expr, MoneyLit):
            amount = Decimal(expr.amount)
            return MoneyVal(
                amount=round_money(amount, expr.currency),
                currency=expr.currency,
            )
        if isinstance(expr, PercentLit):
            return PercentVal(Decimal(expr.value))
        if isinstance(expr, DurationLit):
            return DurationVal(amount=expr.amount, unit=expr.unit)

        if isinstance(expr, Ident):
            return env.lookup(expr.name, expr.line)

        if isinstance(expr, Call):
            return self._call(expr, env)

        if isinstance(expr, UnaryOp):
            return self._eval_unary(expr, env)

        if isinstance(expr, BinOp):
            return self._eval_binop(expr, env)

        if isinstance(expr, SplitExpr):
            return self._eval_split(expr, env)

        if isinstance(expr, FieldAccess):
            # Records can be declared as types but not constructed in
            # source in the current language; this path is therefore
            # dead in practice.  Kept explicit so it fails loudly if
            # we ever extend the language without updating this branch.
            raise RuntimeFault(
                expr.line,
                "field access has no runtime semantics yet: PayFlow has "
                "no record-construction syntax (see retrospective §5.1)",
            )

        raise RuntimeFault(
            getattr(expr, "line", 0),
            f"internal: unknown expression node {type(expr).__name__}",
        )

    # -- unary ---------------------------------------------------------------

    def _eval_unary(self, expr: UnaryOp, env: _Env):
        operand = self._eval(expr.operand, env)
        if expr.op == "-":
            # int / float / Decimal all support unary minus directly.
            return -operand
        if expr.op == "!":
            return not operand
        raise RuntimeFault(expr.line, f"internal: unknown unary `{expr.op}`")

    # -- binary --------------------------------------------------------------

    def _eval_binop(self, expr: BinOp, env: _Env):
        op = expr.op

        # Short-circuit logicals: evaluate left first, then *maybe* right.
        if op == "&&":
            left = self._eval(expr.left, env)
            if left is False:
                return False
            return self._eval(expr.right, env)
        if op == "||":
            left = self._eval(expr.left, env)
            if left is True:
                return True
            return self._eval(expr.right, env)

        # All other binops: strict left-to-right operand evaluation.
        left  = self._eval(expr.left, env)
        right = self._eval(expr.right, env)

        if op in ("==", "!="):
            eq = (left == right)
            return eq if op == "==" else (not eq)

        if op in ("<", "<=", ">", ">="):
            return self._eval_ordered_cmp(op, left, right, expr.line)

        if op in ("+", "-", "*", "/"):
            return self._eval_arith(op, left, right, expr.line)

        raise RuntimeFault(expr.line, f"internal: unknown binary `{op}`")

    def _eval_ordered_cmp(self, op: str, l, r, line: int) -> bool:
        # Money: compare amounts when currencies match.  Currency mismatch
        # was caught by the type checker, but we re-check defensively.
        if isinstance(l, MoneyVal) and isinstance(r, MoneyVal):
            if l.currency != r.currency:
                raise RuntimeFault(
                    line,
                    f"internal: ordering money in different currencies "
                    f"({l.currency} vs {r.currency})",
                )
            l, r = l.amount, r.amount

        if isinstance(l, DurationVal) and isinstance(r, DurationVal):
            l, r = _duration_to_days(l), _duration_to_days(r)

        if op == "<":  return l <  r
        if op == "<=": return l <= r
        if op == ">":  return l >  r
        if op == ">=": return l >= r
        raise RuntimeFault(line, f"internal: unknown ordering op `{op}`")

    def _eval_arith(self, op: str, l, r, line: int):
        # Integer-only result: both sides are bare Python ints AND neither
        # came from a Decimal-bearing wrapper.  The type checker has
        # already ensured the value combinations are well-typed.

        # money ± money (same currency) -----------------------------------
        if isinstance(l, MoneyVal) and isinstance(r, MoneyVal) and op in ("+", "-"):
            if l.currency != r.currency:
                raise RuntimeFault(
                    line,
                    f"internal: arithmetic on money in different currencies",
                )
            amount = l.amount + r.amount if op == "+" else l.amount - r.amount
            return MoneyVal(round_money(amount, l.currency), l.currency)

        # money * numeric  /  numeric * money -----------------------------
        if op == "*":
            if isinstance(l, MoneyVal) and isinstance(r, (int, float, Decimal)):
                amount = l.amount * _to_decimal(r)
                return MoneyVal(round_money(amount, l.currency), l.currency)
            if isinstance(r, MoneyVal) and isinstance(l, (int, float, Decimal)):
                amount = r.amount * _to_decimal(l)
                return MoneyVal(round_money(amount, r.currency), r.currency)

        # money / numeric --------------------------------------------------
        if op == "/" and isinstance(l, MoneyVal) and isinstance(r, (int, float, Decimal)):
            denom = _to_decimal(r)
            if denom == 0:
                raise RuntimeFault(line, "division by zero in money / numeric")
            amount = l.amount / denom
            return MoneyVal(round_money(amount, l.currency), l.currency)

        # duration ± duration ---------------------------------------------
        if isinstance(l, DurationVal) and isinstance(r, DurationVal) and op in ("+", "-"):
            # Normalise to days for arithmetic; that's the smallest unit
            # we have.  The result's unit choice is conservative: keep
            # `day` to avoid implying an exact month/year conversion in
            # the output.
            ld, rd = _duration_to_days(l), _duration_to_days(r)
            n = ld + rd if op == "+" else ld - rd
            return DurationVal(amount=n, unit="day")

        # native int / float (with int -> float widening) -----------------
        if isinstance(l, (int, float)) and isinstance(r, (int, float)) \
                and not isinstance(l, bool) and not isinstance(r, bool):
            if op == "/" and r == 0:
                raise RuntimeFault(line, "division by zero")
            # Python's mixed int/float arithmetic does the widening
            # implicitly, matching §4.5.
            if op == "+": return l + r
            if op == "-": return l - r
            if op == "*": return l * r
            if op == "/":
                # Match the type checker: int / int produces float in
                # the surface language.  Python's `/` is true division
                # so this already holds.
                return l / r

        raise RuntimeFault(
            line, f"internal: arithmetic `{op}` not handled for {type(l).__name__} and {type(r).__name__}",
        )

    # -- split (§4.4.2) ------------------------------------------------------

    def _eval_split(self, expr: SplitExpr, env: _Env) -> MoneyVal:
        # §4.4.2 rule: evaluate left, then right, then
        #   result = round_c( a * (1 - p/100) )
        # with `c` taken from the left operand's currency.
        left  = self._eval(expr.left, env)
        right = self._eval(expr.right, env)

        if not isinstance(left, MoneyVal) or not isinstance(right, PercentVal):
            # Type-checker should have caught this; defensive only.
            raise RuntimeFault(
                expr.line,
                f"internal: `split` expects (money, percent), "
                f"got ({type(left).__name__}, {type(right).__name__})",
            )

        # Domain-specific runtime error: percent must lie in [0, 100].
        # The lexer accepts `200%` syntactically, so this is the first
        # place the value-range constraint is enforced.
        if right.value < 0 or right.value > 100:
            raise RuntimeFault(
                expr.line,
                f"percent value {right} is outside the legal range "
                f"[0%, 100%] for `split`",
            )

        # Compute and round to the currency's minor unit.
        ratio = (Decimal(100) - right.value) / Decimal(100)
        amount = left.amount * ratio
        rounded = round_money(amount, left.currency)
        return MoneyVal(amount=rounded, currency=left.currency)

    # -- function call (§4.7 pass-by-value, left-to-right args) --------------

    def _call(self, expr: Call, env: _Env):
        fn = self.fns.get(expr.callee)
        if fn is None:
            raise RuntimeFault(
                expr.line, f"internal: call to unknown function `{expr.callee}`",
            )
        # Evaluate arguments strictly left-to-right.  Each becomes a
        # fresh binding in the new scope; PayFlow values are immutable,
        # so pass-by-value vs by-reference is observationally identical.
        arg_values = [self._eval(a, env) for a in expr.args]
        local = _Env()
        for (pname, _ptype), val in zip(
                [(p.name, p.type_) for p in fn.params], arg_values):
            local.define(pname, val)

        try:
            self._exec_block(fn.body, local)
        except _ReturnSignal as r:
            return r.value

        # Falling off the end of a function with a declared return type
        # would be a static error in a fuller language; here the type
        # checker doesn't yet do path-coverage analysis, so we surface
        # it at runtime.
        raise RuntimeFault(
            fn.line,
            f"function `{fn.name}` reached end of body without `return`",
        )


# ---------------------------------------------------------------------------
# Small helpers (module-private)
# ---------------------------------------------------------------------------

def _to_decimal(x) -> Decimal:
    """Coerce a Python numeric to Decimal without floating-point drift.

    int  -> Decimal(int)  (exact)
    Decimal -> itself
    float -> Decimal(str(float))  (best-effort; we don't expect float here
                                    in money paths, but keep the conversion
                                    safe in case it slips in)
    """
    if isinstance(x, Decimal):
        return x
    if isinstance(x, int):
        return Decimal(x)
    if isinstance(x, float):
        return Decimal(str(x))
    raise TypeError(f"cannot convert {x!r} to Decimal")


# Approximate day equivalents.  Used only for ordering and arithmetic
# of durations — we deliberately don't surface this conversion at the
# value level (see DurationVal __str__), because in a real billing
# context "1 month" is contractual, not 30 days.
_DAYS_PER_UNIT = {
    "day":   1,
    "week":  7,
    "month": 30,
    "year":  365,
}


def _duration_to_days(d: DurationVal) -> int:
    return d.amount * _DAYS_PER_UNIT[d.unit]
