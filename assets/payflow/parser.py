"""
PayFlow recursive-descent parser.

Hand-written. One method per non-terminal of the EBNF given in D1 §4.3.
Left-associativity of binary operators is encoded by loops, never by
self-recursion-before-operator-consume — see _parse_or_expr through
_parse_split_expr / _parse_add_expr / _parse_mul_expr below.

Conventions
-----------
- _peek()                  : look at the current token without consuming
- _check(kind, value=None) : True if current token matches; does not consume
- _accept(kind, value)     : consume-if-match, returning the Token or None
- _expect(kind, value, msg): consume-or-raise. The msg is the human-friendly
                             "what we expected" phrase used in error messages.

All errors raised by the parser are ParseError, which carries the line
number of the offending token. The error message format is

    Parse error at line N: <reason> (got <kind> <value>)
"""

from typing import List, Optional

from ast_nodes import (
    Program, RecordDecl, Field, PlanDecl, PlanField,
    PaywallDecl, WhenClause, FnDecl, Param, Block, TypeRef,
    ReturnStmt, IfStmt, ShowStmt, ExprStmt,
    BinOp, SplitExpr, UnaryOp,
    IntLit, DecLit, MoneyLit, PercentLit, DurationLit,
    StringLit, BoolLit, Ident, Call, FieldAccess,
)
from lexer import (
    Token, tokenize,
    TK_IDENT, TK_INT, TK_DEC, TK_PCT, TK_STR, TK_KW, TK_OP, TK_SEP, TK_EOF,
)


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------

class ParseError(Exception):
    """Raised when the parser cannot continue.

    The line number is always the line of the offending token, which is
    either the token the parser was trying to consume or — at EOF — the
    last line of the source.
    """
    def __init__(self, line: int, reason: str, got: Optional[Token] = None):
        if got is not None:
            full = f"Parse error at line {line}: {reason} (got {got.kind} {got.value!r})"
        else:
            full = f"Parse error at line {line}: {reason}"
        super().__init__(full)
        self.line = line
        self.reason = reason


# ---------------------------------------------------------------------------
# Constants drawn from the EBNF
# ---------------------------------------------------------------------------

PRIMITIVE_TYPE_KEYWORDS = {
    "int", "float", "bool", "money", "percent", "duration", "string",
}
CURRENCY_KEYWORDS = {"USD", "EUR", "TRY", "GBP", "JPY"}
DURATION_UNIT_KEYWORDS = {
    "day", "days", "week", "weeks",
    "month", "months", "year", "years",
}
COMPARISON_OPS = {"==", "!=", "<", "<=", ">", ">="}


def _canonical_unit(unit: str) -> str:
    """Map plural duration unit names back to their singular canonical form."""
    if unit.endswith("s"):
        return unit[:-1]
    return unit


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.i = 0

    # -- low-level helpers -------------------------------------------------------

    def _peek(self, offset: int = 0) -> Token:
        idx = self.i + offset
        if idx >= len(self.tokens):
            return self.tokens[-1]  # EOF token
        return self.tokens[idx]

    def _at_end(self) -> bool:
        return self._peek().kind == TK_EOF

    def _check(self, kind: str, value: Optional[str] = None) -> bool:
        t = self._peek()
        if t.kind != kind:
            return False
        return value is None or t.value == value

    def _accept(self, kind: str, value: Optional[str] = None) -> Optional[Token]:
        if self._check(kind, value):
            t = self.tokens[self.i]
            self.i += 1
            return t
        return None

    def _expect(self, kind: str, value: Optional[str], description: str) -> Token:
        t = self._peek()
        if t.kind == kind and (value is None or t.value == value):
            self.i += 1
            return t
        raise ParseError(t.line, f"expected {description}", got=t)

    # -- entry point -------------------------------------------------------------

    def parse_program(self) -> Program:
        prog = Program(decls=[], line=self._peek().line)
        while not self._at_end():
            decl = self._parse_top_decl()
            prog.decls.append(decl)
        return prog

    # -- top-level declarations --------------------------------------------------

    def _parse_top_decl(self):
        t = self._peek()
        if t.kind == TK_KW:
            if t.value == "record":  return self._parse_record_decl()
            if t.value == "plan":    return self._parse_plan_decl()
            if t.value == "paywall": return self._parse_paywall_decl()
            if t.value == "fn":      return self._parse_fn_decl()
        raise ParseError(
            t.line,
            "expected a top-level declaration "
            "(`record`, `plan`, `paywall`, or `fn`)",
            got=t,
        )

    def _parse_record_decl(self) -> RecordDecl:
        kw = self._expect(TK_KW, "record", "`record` keyword")
        name_tok = self._expect(TK_IDENT, None, "record name (identifier)")
        self._expect(TK_SEP, "{", "`{` to open record body")
        fields: List[Field] = []
        if not self._check(TK_SEP, "}"):
            fields.append(self._parse_field())
            while self._accept(TK_SEP, ";"):
                if self._check(TK_SEP, "}"):
                    break  # trailing semicolon is allowed
                fields.append(self._parse_field())
        self._expect(TK_SEP, "}", "`}` to close record body")
        return RecordDecl(name=name_tok.value, fields=fields, line=kw.line)

    def _parse_field(self) -> Field:
        name_tok = self._expect(TK_IDENT, None, "field name (identifier)")
        self._expect(TK_SEP, ":", "`:` between field name and type")
        type_ref = self._parse_type()
        return Field(name=name_tok.value, type_=type_ref, line=name_tok.line)

    def _parse_plan_decl(self) -> PlanDecl:
        kw = self._expect(TK_KW, "plan", "`plan` keyword")
        name_tok = self._expect(TK_IDENT, None, "plan name (identifier)")
        self._expect(TK_SEP, "{", "`{` to open plan body")
        fields: List[PlanField] = []
        if not self._check(TK_SEP, "}"):
            fields.append(self._parse_plan_field())
            while self._accept(TK_SEP, ";"):
                if self._check(TK_SEP, "}"):
                    break
                fields.append(self._parse_plan_field())
        self._expect(TK_SEP, "}", "`}` to close plan body")
        return PlanDecl(name=name_tok.value, fields=fields, line=kw.line)

    def _parse_plan_field(self) -> PlanField:
        name_tok = self._expect(TK_IDENT, None, "plan field name (identifier)")
        self._expect(TK_SEP, ":", "`:` between plan field name and value")
        value = self._parse_expr()
        return PlanField(name=name_tok.value, value=value, line=name_tok.line)

    def _parse_paywall_decl(self) -> PaywallDecl:
        kw = self._expect(TK_KW, "paywall", "`paywall` keyword")
        name_tok = self._expect(TK_IDENT, None, "paywall name (identifier)")
        self._expect(TK_SEP, "{", "`{` to open paywall body")

        when_clauses: List[WhenClause] = []
        while self._check(TK_KW, "when"):
            when_clauses.append(self._parse_when_clause())

        # default clause is mandatory by the grammar (exhaustiveness baked in)
        if not self._check(TK_KW, "default"):
            t = self._peek()
            raise ParseError(
                t.line,
                "every `paywall` block must end with a `default` clause",
                got=t,
            )
        default_kw = self._expect(TK_KW, "default", "`default` keyword")
        default_block = self._parse_block()

        self._expect(TK_SEP, "}", "`}` to close paywall body")
        return PaywallDecl(
            name=name_tok.value,
            when_clauses=when_clauses,
            default_block=default_block,
            line=kw.line,
        )

    def _parse_when_clause(self) -> WhenClause:
        kw = self._expect(TK_KW, "when", "`when` keyword")
        cond = self._parse_expr()
        body = self._parse_block()
        return WhenClause(condition=cond, body=body, line=kw.line)

    def _parse_fn_decl(self) -> FnDecl:
        kw = self._expect(TK_KW, "fn", "`fn` keyword")
        name_tok = self._expect(TK_IDENT, None, "function name (identifier)")
        self._expect(TK_SEP, "(", "`(` to open parameter list")
        params: List[Param] = []
        if not self._check(TK_SEP, ")"):
            params.append(self._parse_param())
            while self._accept(TK_SEP, ","):
                params.append(self._parse_param())
        self._expect(TK_SEP, ")", "`)` to close parameter list")
        self._expect(TK_OP, "->", "`->` before return type")
        ret_type = self._parse_type()
        body = self._parse_block()
        return FnDecl(
            name=name_tok.value, params=params,
            return_type=ret_type, body=body, line=kw.line,
        )

    def _parse_param(self) -> Param:
        name_tok = self._expect(TK_IDENT, None, "parameter name (identifier)")
        self._expect(TK_SEP, ":", "`:` between parameter name and type")
        type_ref = self._parse_type()
        return Param(name=name_tok.value, type_=type_ref, line=name_tok.line)

    # -- types -------------------------------------------------------------------

    def _parse_type(self) -> TypeRef:
        t = self._peek()
        if t.kind == TK_KW and t.value in PRIMITIVE_TYPE_KEYWORDS:
            self.i += 1
            return TypeRef(name=t.value, line=t.line)
        if t.kind == TK_IDENT:
            self.i += 1
            return TypeRef(name=t.value, line=t.line)
        raise ParseError(
            t.line,
            "expected a type (one of int, float, bool, money, percent, "
            "duration, string, or a record name)",
            got=t,
        )

    # -- statements / blocks -----------------------------------------------------

    def _parse_block(self) -> Block:
        open_tok = self._expect(TK_SEP, "{", "`{` to open block")
        stmts = []
        while not self._check(TK_SEP, "}"):
            if self._at_end():
                raise ParseError(
                    self._peek().line,
                    "unexpected end of file inside block (missing `}`?)",
                )
            stmts.append(self._parse_stmt())
        self._expect(TK_SEP, "}", "`}` to close block")
        return Block(stmts=stmts, line=open_tok.line)

    def _parse_stmt(self):
        t = self._peek()
        if t.kind == TK_KW and t.value == "return":
            return self._parse_return_stmt()
        if t.kind == TK_KW and t.value == "if":
            return self._parse_if_stmt()
        if t.kind == TK_KW and t.value == "show":
            return self._parse_show_stmt()
        # else fall through to expression statement
        expr = self._parse_expr()
        self._expect(TK_SEP, ";", "`;` to terminate expression statement")
        return ExprStmt(expr=expr, line=expr.line)

    def _parse_return_stmt(self) -> ReturnStmt:
        kw = self._expect(TK_KW, "return", "`return`")
        value = self._parse_expr()
        self._expect(TK_SEP, ";", "`;` after return expression")
        return ReturnStmt(value=value, line=kw.line)

    def _parse_if_stmt(self) -> IfStmt:
        kw = self._expect(TK_KW, "if", "`if`")
        self._expect(TK_SEP, "(", "`(` after `if`")
        cond = self._parse_expr()
        self._expect(TK_SEP, ")", "`)` after `if` condition")
        then_blk = self._parse_block()
        else_blk = None
        if self._accept(TK_KW, "else"):
            else_blk = self._parse_block()
        return IfStmt(condition=cond, then_block=then_blk,
                      else_block=else_blk, line=kw.line)

    def _parse_show_stmt(self) -> ShowStmt:
        """Enforces: each clause appears at most once, in any order.

        This fixes the looseness of the original EBNF, where
        `{ "at" expr | "with" "trial" expr }` allowed repeats — the
        flaw I flagged as point #8 of the E1 critique.
        """
        kw = self._expect(TK_KW, "show", "`show`")
        plan_tok = self._expect(TK_IDENT, None, "plan name after `show`")

        at_price = None
        with_trial = None
        while True:
            if self._check(TK_KW, "at"):
                at_tok = self._peek()
                if at_price is not None:
                    raise ParseError(
                        at_tok.line,
                        "duplicate `at` clause in `show` statement",
                        got=at_tok,
                    )
                self.i += 1
                at_price = self._parse_expr()
                continue
            if self._check(TK_KW, "with"):
                with_tok = self._peek()
                if with_trial is not None:
                    raise ParseError(
                        with_tok.line,
                        "duplicate `with trial` clause in `show` statement",
                        got=with_tok,
                    )
                self.i += 1
                # `trial` is a contextual keyword: it is an ordinary
                # identifier in every context except immediately after
                # `with`, where it must appear.
                trial_tok = self._peek()
                if not (trial_tok.kind == TK_IDENT and trial_tok.value == "trial"):
                    raise ParseError(
                        trial_tok.line,
                        "expected `trial` after `with` in `show` statement",
                        got=trial_tok,
                    )
                self.i += 1
                with_trial = self._parse_expr()
                continue
            break

        self._expect(TK_SEP, ";", "`;` to terminate `show` statement")
        return ShowStmt(
            plan_name=plan_tok.value,
            at_price=at_price,
            with_trial=with_trial,
            line=kw.line,
        )

    # -- expressions: precedence climbing via the EBNF chain --------------------
    #
    # expr        -> or_expr
    # or_expr     -> and_expr  ( "||" and_expr )*           (left-assoc)
    # and_expr    -> cmp_expr  ( "&&" cmp_expr )*           (left-assoc)
    # cmp_expr    -> split_expr ( CMP_OP split_expr )?      (non-chain)
    # split_expr  -> add_expr  ( "split" add_expr )*        (left-assoc)
    # add_expr    -> mul_expr  ( ("+"|"-") mul_expr )*      (left-assoc)
    # mul_expr    -> unary     ( ("*"|"/") unary )*         (left-assoc)
    # unary       -> ("-" | "!") unary  |  primary
    # primary     -> ... (literals, idents, calls, parens) ...
    #
    # Left-associativity is enforced by accumulating into a `left` variable
    # in a loop, NOT by recursing on the same level.

    def _parse_expr(self):
        return self._parse_or_expr()

    def _parse_or_expr(self):
        left = self._parse_and_expr()
        while self._check(TK_OP, "||"):
            op_tok = self.tokens[self.i]; self.i += 1
            right = self._parse_and_expr()
            left = BinOp(op="||", left=left, right=right, line=op_tok.line)
        return left

    def _parse_and_expr(self):
        left = self._parse_cmp_expr()
        while self._check(TK_OP, "&&"):
            op_tok = self.tokens[self.i]; self.i += 1
            right = self._parse_cmp_expr()
            left = BinOp(op="&&", left=left, right=right, line=op_tok.line)
        return left

    def _parse_cmp_expr(self):
        left = self._parse_split_expr()
        if self._peek().kind == TK_OP and self._peek().value in COMPARISON_OPS:
            op_tok = self.tokens[self.i]; self.i += 1
            right = self._parse_split_expr()
            # explicitly forbid chaining: a < b < c
            if self._peek().kind == TK_OP and self._peek().value in COMPARISON_OPS:
                bad = self._peek()
                raise ParseError(
                    bad.line,
                    "comparison operators do not chain "
                    "(write `a < b && b < c` instead of `a < b < c`)",
                    got=bad,
                )
            left = BinOp(op=op_tok.value, left=left, right=right, line=op_tok.line)
        return left

    def _parse_split_expr(self):
        # `split` sits between comparison and additive in our precedence chain;
        # it is left-associative and chainable.
        left = self._parse_add_expr()
        while self._check(TK_KW, "split"):
            op_tok = self.tokens[self.i]; self.i += 1
            right = self._parse_add_expr()
            left = SplitExpr(left=left, right=right, line=op_tok.line)
        return left

    def _parse_add_expr(self):
        left = self._parse_mul_expr()
        while self._peek().kind == TK_OP and self._peek().value in ("+", "-"):
            op_tok = self.tokens[self.i]; self.i += 1
            right = self._parse_mul_expr()
            left = BinOp(op=op_tok.value, left=left, right=right, line=op_tok.line)
        return left

    def _parse_mul_expr(self):
        left = self._parse_unary()
        while self._peek().kind == TK_OP and self._peek().value in ("*", "/"):
            op_tok = self.tokens[self.i]; self.i += 1
            right = self._parse_unary()
            left = BinOp(op=op_tok.value, left=left, right=right, line=op_tok.line)
        return left

    def _parse_unary(self):
        t = self._peek()
        if t.kind == TK_OP and t.value in ("-", "!"):
            self.i += 1
            operand = self._parse_unary()
            return UnaryOp(op=t.value, operand=operand, line=t.line)
        return self._parse_primary()

    def _parse_primary(self):
        """Parse a primary expression followed by any number of `.field`
        suffixes.  Field access binds tighter than every binary operator
        (it lives at the primary level), so `a.b + c` is `(a.b) + c`
        and `a + b.c` is `a + (b.c)`.
        """
        node = self._parse_primary_core()
        while self._check(TK_SEP, "."):
            dot = self.tokens[self.i]; self.i += 1
            name_tok = self._expect(
                TK_IDENT, None, "field name after `.`"
            )
            node = FieldAccess(
                target=node, field_name=name_tok.value, line=dot.line,
            )
        return node

    def _parse_primary_core(self):
        t = self._peek()

        # Parenthesised expression
        if t.kind == TK_SEP and t.value == "(":
            self.i += 1
            inner = self._parse_expr()
            self._expect(TK_SEP, ")", "`)` to close parenthesised expression")
            return inner

        # Numeric literals: may glue onto a currency or duration unit
        if t.kind == TK_INT:
            self.i += 1
            # duration?  `7 days`
            nxt = self._peek()
            if nxt.kind == TK_KW and nxt.value in DURATION_UNIT_KEYWORDS:
                self.i += 1
                return DurationLit(
                    amount=int(t.value),
                    unit=_canonical_unit(nxt.value),
                    line=t.line,
                )
            # money with integer amount?  `199 USD`
            if nxt.kind == TK_KW and nxt.value in CURRENCY_KEYWORDS:
                self.i += 1
                return MoneyLit(amount=t.value, currency=nxt.value, line=t.line)
            return IntLit(value=int(t.value), line=t.line)

        if t.kind == TK_DEC:
            self.i += 1
            nxt = self._peek()
            if nxt.kind == TK_KW and nxt.value in CURRENCY_KEYWORDS:
                self.i += 1
                return MoneyLit(amount=t.value, currency=nxt.value, line=t.line)
            # decimals don't combine with duration units (`7.5 days` is rejected)
            return DecLit(value=t.value, line=t.line)

        if t.kind == TK_PCT:
            self.i += 1
            return PercentLit(value=t.value, line=t.line)

        if t.kind == TK_STR:
            self.i += 1
            return StringLit(value=t.value, line=t.line)

        if t.kind == TK_KW and t.value in ("true", "false"):
            self.i += 1
            return BoolLit(value=(t.value == "true"), line=t.line)

        # Identifier, possibly a call
        if t.kind == TK_IDENT:
            self.i += 1
            if self._check(TK_SEP, "("):
                self.i += 1
                args = []
                if not self._check(TK_SEP, ")"):
                    args.append(self._parse_expr())
                    while self._accept(TK_SEP, ","):
                        args.append(self._parse_expr())
                self._expect(TK_SEP, ")", "`)` to close argument list")
                return Call(callee=t.value, args=args, line=t.line)
            return Ident(name=t.value, line=t.line)

        raise ParseError(
            t.line,
            "expected an expression (literal, identifier, or `(` ... `)`)",
            got=t,
        )


# ---------------------------------------------------------------------------
# Convenience: parse a source string end-to-end
# ---------------------------------------------------------------------------

def parse(source: str) -> Program:
    tokens = tokenize(source)
    return Parser(tokens).parse_program()
