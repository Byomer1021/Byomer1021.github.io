"""Bridge between the PayFlow pipeline and the browser playground.

The five modules beside this file are copied verbatim from
github.com/Byomer1021/payflow (src/), so the playground runs the same
lexer, parser, type checker and interpreter the repository ships --
not a JavaScript re-implementation that could drift from it.

`run_source` returns a JSON string rather than a dict: Pyodide maps a
Python dict to a JS Map, and JSON keeps the boundary boring.
"""

import io
import json

from lexer import LexError, tokenize
from parser import ParseError, parse
from type_checker import PayflowTypeError, check as type_check
from interpreter import Interpreter, RuntimeFault


def _token_lines(source, limit=400):
    """Token dump, in the order the lexer produced them."""
    try:
        toks = tokenize(source)
    except LexError as e:
        return str(e)
    rows = []
    for t in toks[:limit]:
        value = "" if t.value is None else str(t.value)
        rows.append("%4d  %-10s %s" % (t.line, t.kind, value))
    if len(toks) > limit:
        rows.append("... %d more tokens" % (len(toks) - limit))
    return "\n".join(rows)


def run_source(source, region="US"):
    """Lex, parse, type-check and execute `source`.

    Mirrors the phase order and the single-line error format of the
    repository's CLI driver (payflow.py), including its exit-code
    meaning: a lex/parse/type/runtime failure stops the pipeline.
    """
    result = {
        "ok": False,
        "phase": "",
        "error": "",
        "output": "",
        "tokens": "",
        "ast": "",
    }

    result["tokens"] = _token_lines(source)

    # ---- phase 1: lex + parse ------------------------------------------
    try:
        program = parse(source)
    except (LexError, ParseError) as e:
        result["phase"] = "parse"
        result["error"] = str(e)
        return json.dumps(result)

    try:
        result["ast"] = program.dump()
    except Exception as e:                      # pragma: no cover
        result["ast"] = "<could not dump AST: %s>" % e

    # ---- phase 2: type check -------------------------------------------
    try:
        type_check(program)
    except PayflowTypeError as e:
        result["phase"] = "type"
        result["error"] = str(e)
        return json.dumps(result)

    # ---- phase 3: interpret --------------------------------------------
    buf = io.StringIO()
    try:
        Interpreter(out=buf).run(program, region=region)
    except RuntimeFault as e:
        result["phase"] = "runtime"
        result["error"] = str(e)
        result["output"] = buf.getvalue()
        return json.dumps(result)

    result["ok"] = True
    result["phase"] = "done"
    result["output"] = buf.getvalue()
    return json.dumps(result)
