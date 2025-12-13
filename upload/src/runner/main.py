import sys
from .color import Color
from RestrictedPython import compile_restricted
from RestrictedPython.Guards import safe_builtins, safer_getattr, guarded_iter_unpack_sequence, guarded_unpack_sequence
from RestrictedPython.Eval import default_guarded_getiter
from RestrictedPython.PrintCollector import PrintCollector
import math
import random
from .exposed import get_exposed_functions

def _inplacevar_(op, var, expr):
    ops = {"+=": lambda: var + expr, "-=": lambda: var - expr, "*=": lambda: var * expr,
           "/=": lambda: var / expr, "%=": lambda: var % expr, "**=": lambda: var ** expr,
           "<<": lambda: var << expr, ">>=": lambda: var >> expr, "|=": lambda: var | expr,
           "^=": lambda: var ^ expr, "&=": lambda: var & expr, "//=": lambda: var // expr}
    return ops.get(op, lambda: var)()

def execute_code(code):
    byte_code = compile_restricted(code, "<user_code>", "exec")
    allowed_builtins = {**safe_builtins, "enumerate": enumerate, "zip": zip, "map": map,
                        "filter": filter, "sorted": sorted, "reversed": reversed, "sum": sum,
                        "min": min, "max": max, "abs": abs, "round": round, "pow": pow,
                        "divmod": divmod, "all": all, "any": any, "isinstance": isinstance,
                        "chr": chr, "ord": ord, "hex": hex, "oct": oct, "bin": bin,
                        "range": range}
    restricted_globals = {
        "__builtins__": allowed_builtins,
        "_getitem_": lambda obj, index: obj[index],
        "_inplacevar_": _inplacevar_,
        "_print_": PrintCollector,
        "_getattr_": safer_getattr,
        "_getiter_": default_guarded_getiter,
        "_iter_unpack_sequence_": guarded_iter_unpack_sequence,
        "_unpack_sequence_": guarded_unpack_sequence,
        "__name__": "restricted_module",
        "__metaclass__": type,
        "RED": Color.RED, "GREEN": Color.GREEN, "BLUE": Color.BLUE,
        "YELLOW": Color.YELLOW, "CYAN": Color.CYAN, "MAGENTA": Color.MAGENTA,
        "WHITE": Color.WHITE, "ORANGE": Color.ORANGE, "PURPLE": Color.PURPLE,
        "PINK": Color.PINK, "OFF": Color.OFF,
        "math": math, "random": random
    }
    restricted_globals.update(get_exposed_functions())
    
    try:
        exec(byte_code, restricted_globals)
        result = restricted_globals.get("_print", lambda: "")()
        return result if result.strip() else "No prints invoked, but ur program executed ok (we hope)"
    except Exception as e:
        return f"Error: {e}"

def __debug_cli():
    with open(sys.argv[1], "r") as f:
        print(execute_code(f.read()))

if __name__ == "__main__":
    __debug_cli()