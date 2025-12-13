import inspect
import time
from . import leds

SIZE = leds.SIZE
current_leds = [(0, 0, 0, 0)] * SIZE 

def getLEDCount():
    return SIZE
    
def setLEDs(new_leds):
    global current_leds
    if len(new_leds) != SIZE:
        raise ValueError("LED list size does not match Tree size")
    
    current_leds = new_leds
    payload = bytearray()
    for led in current_leds:
        payload.extend(led)
    leds.set_framebuf(bytes(payload))
    return True

def clearLEDs():
    setLEDs([(0, 0, 0, 0)] * SIZE)

def sleep(seconds):
    if seconds > 10:
        raise ValueError("sleep max 10s")
    time.sleep(seconds)

def get_exposed_functions():
    current_module = inspect.getmembers(inspect.getmodule(inspect.currentframe()))
    exposed = {}
    
    for name, obj in current_module:
        if callable(obj) and not name.startswith('_') and name != 'get_exposed_functions':
            exposed[name] = obj
    
    return exposed