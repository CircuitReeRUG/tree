import sys
import logging
from .color import Color

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

from RestrictedPython import compile_restricted
from RestrictedPython.Guards import (
    safe_builtins,
    safe_globals,
    safer_getattr,
    full_write_guard,
    guarded_iter_unpack_sequence,
    guarded_unpack_sequence,
)
from RestrictedPython.Eval import default_guarded_getiter
from RestrictedPython.PrintCollector import PrintCollector

import math
import random

from .exposed import get_exposed_functions



def execute_code(code: str) -> str:
    byte_code = compile_restricted(code, '<user_code>', 'exec')
    
    # Merge safe_builtins with limited_builtins to get more functionality
    allowed_builtins = { **safe_builtins}
    
    # Allow more builtins for full Python syntax support
    allowed_builtins.update({
        'enumerate': enumerate,
        'zip': zip,
        'map': map,
        'filter': filter,
        'sorted': sorted,
        'reversed': reversed,
        'sum': sum,
        'min': min,
        'max': max,
        'abs': abs,
        'round': round,
        'pow': pow,
        'divmod': divmod,
        'all': all,
        'any': any,
        'isinstance': isinstance,
        'issubclass': issubclass,
        'callable': callable,
        'chr': chr,
        'ord': ord,
        'hex': hex,
        'oct': oct,
        'bin': bin,
        'hash': hash,
        'id': id,
        'type': type,
        'bytes': bytes,
        'bytearray': bytearray,
        'complex': complex,
        'frozenset': frozenset,
        'range': range
    })
    
    restricted_globals = {
        '__builtins__': allowed_builtins,
        '__name__': 'user_code',
        '__metaclass__': type,
        '_getitem_': lambda obj, index: obj[index],
        '_inplacevar_': lambda op, x, y: op(x, y), 
        '_print_': PrintCollector,
        '_getattr_': safer_getattr, 
        '_write_': full_write_guard,
        '_getiter_': default_guarded_getiter,
        '_iter_unpack_sequence_': guarded_iter_unpack_sequence,
        '_unpack_sequence_': guarded_unpack_sequence,
        # ----- Colors ------
        'RED': Color.RED,
        'GREEN': Color.GREEN,
        'BLUE': Color.BLUE,
        'YELLOW': Color.YELLOW,
        'CYAN': Color.CYAN,
        'MAGENTA': Color.MAGENTA,
        'WHITE': Color.WHITE,
        'ORANGE': Color.ORANGE,
        'PURPLE': Color.PURPLE,
        'PINK': Color.PINK,
        'OFF': Color.OFF,
        'math': math,
        'random': random
    }
    
    # add exposed functions
    restricted_globals.update(get_exposed_functions())
    
    try:
        exec(byte_code, restricted_globals)
        if '_print' in restricted_globals:
            result = restricted_globals['_print']() # pyright: ignore[reportCallIssue]
        else:
            result = ""
        
        if not result.strip():
            result = "No prints invoked, but ur program executed ok (we hope)"
        
        return result #pyright: ignore[reportReturnType]
    except Exception as e:
        return f"Error: {e}"

# DEBUG
def __debug_cli():
    file_path = sys.argv[1]
    language = "python"
    with open(file_path, 'r') as f:
        code = f.read()
    
    output = execute_code(code)
    print(output)

if __name__ == "__main__":
    __debug_cli()