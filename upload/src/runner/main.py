import sys
import logging
from .color import Color

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

from RestrictedPython import compile_restricted, safe_globals, PrintCollector, limited_builtins
from RestrictedPython.Eval import default_guarded_getiter
from RestrictedPython.Guards import guarded_iter_unpack_sequence, safer_getattr
from .exposed import get_exposed_functions

def execute_code(code: str) -> str:
    byte_code = compile_restricted(code, '<user_code>', 'exec')
    
    restricted_globals = {
        '__builtins__': limited_builtins,
        '_iter_unpack_sequence_': guarded_iter_unpack_sequence,
        '_getattr_': safer_getattr,
        '_getiter_': default_guarded_getiter,
        '_print_': PrintCollector,
        '_getitem_': lambda obj, index: obj[index],

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
        'math': __import__('math'),
        'random': __import__('random'),
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
