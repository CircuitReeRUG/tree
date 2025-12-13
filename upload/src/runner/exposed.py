import inspect
import time
from . import leds

SIZE: int = leds.SIZE
current_leds = [(0, 0, 0, 0)] * SIZE 

def getLEDCount() -> int:
    return SIZE
    
def setLEDs(new_leds: list[tuple[int, int, int, int]]) -> bool:
    global current_leds
    if len(new_leds) != SIZE:
        raise ValueError("LED list size does not match Tree size")
    
    # make sure to type check
    for led in new_leds:
        if not isinstance(led, tuple) or len(led) != 4:
            raise ValueError("Each LED must be a tuple of four integers (R,G,B,L)")
        r, g, b, brightness = led
        if not all(isinstance(c, int) for c in led):
            raise TypeError("All LED values must be integers")
        if not (0 <= r <= 255 and 0 <= g <= 255 and 0 <= b <= 255):
            raise ValueError("RGB values must be between 0 and 255")
        if not (0 <= brightness <= 100):
            raise ValueError("Brightness (L) must be between 0 and 100")
    
    current_leds = new_leds
    
    payload = bytearray()
    for led in current_leds:
        payload.extend(led)
    leds.set_framebuf(bytes(payload))
    return True

def clearLEDs() -> None:
    global current_leds
    setLEDs([(0, 0, 0, 0)] * SIZE)

def sleep(seconds: float) -> None:
    """Sleep for the given number of seconds."""
    if not isinstance(seconds, (int, float)):
        raise TypeError("sleep() argument must be a number")
    if seconds < 0:
        raise ValueError("sleep() argument must be non-negative")
    if seconds > 10:
        raise ValueError("sleep() argument must be at most 10 seconds")
    time.sleep(seconds)

def get_exposed_functions() -> dict: #pyright: ignore[reportMissingTypeArgument]
    current_module = inspect.getmembers(inspect.getmodule(inspect.currentframe()))
    exposed = {}
    
    for name, obj in current_module:
        if callable(obj) and not name.startswith('_') and name != 'get_exposed_functions':
            exposed[name] = obj
    
    return exposed