import socket
import os
import inspect
import time

SIZE:int = int(os.environ.get("TREE_LEDS", "1"))
leds = [(0,0,0,0)] * SIZE 
SERVER_ADDRESS = os.environ.get('LED_SOCKET_PATH', '/tmp/led_socket')

def _send_message(message: str) -> str:
    time.sleep(0.1)  # Rate limiting
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
            client.connect(SERVER_ADDRESS)
            client.sendall(message.encode('utf-8'))
            response = client.recv(4096).decode('utf-8')
        return response
    except (FileNotFoundError, ConnectionRefusedError, OSError) as e:
        return "OK (LED server not connected)"

def getLEDCount() -> int:
    return SIZE
    
def setLEDs(new_leds: list[tuple[int,int,int,int]]) -> bool:
    global leds
    time.sleep(0.05)  # Small delay for LED updates
    if len(new_leds) != SIZE:
        raise ValueError("LED list size does not match Tree size")
    # make sure to type check
    for led in new_leds:
        if (not isinstance(led, tuple) or len(led) != 4 or
            not all(isinstance(c, int) and 0 <= c <= 255 for c in led)):
            raise ValueError("Each LED must be a tuple of four integers (R,G,B,L) between 0 and 255")
    
    leds = new_leds
    # just send the list as text
    _send_message(str(leds))
    return True

def clearLEDs() -> None:
    global leds
    time.sleep(0.05)
    setLEDs( [(0,0,0,0)] * SIZE )

def get_exposed_functions() -> dict: #pyright: ignore[reportMissingTypeArgument]
    current_module = inspect.getmembers(inspect.getmodule(inspect.currentframe()))
    exposed = {}
    
    for name, obj in current_module:
        if callable(obj) and not name.startswith('_') and name != 'get_exposed_functions':
            exposed[name] = obj
    
    return exposed