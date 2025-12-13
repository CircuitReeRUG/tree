"""LED control module - manages NeoPixel LEDs on Raspberry Pi"""
import neopixel
import board
import os
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def __find_pin(pin: int):
    allowed_pins = {
        # https://learn.adafruit.com/neopixels-on-raspberry-pi/python-usage
        10: board.D10,
        12: board.D12,
        18: board.D18,
        21: board.D21,
    }
    if pin not in allowed_pins:
        raise ValueError(f'Pin {pin} is not supported for NeoPixel')
    return allowed_pins[pin]

SIZE = int(os.environ.get('TREE_LEDS', 16))
GPIO_PIN = __find_pin(int(os.environ.get('LED_GPIO_PIN', 18)))
pixels = neopixel.NeoPixel(GPIO_PIN, SIZE, brightness=0.2, auto_write=False)  # pyright: ignore[reportArgumentType]

def get_led_count() -> int:
    return SIZE

def brightness_hack(l: float, r: int, g: int, b: int) -> tuple[int, int, int]:
    if l == 100:
        return (r, g, b)
    
    factor = l / 100.0
    r = int(r * factor)
    g = int(g * factor)
    b = int(b * factor)
    return (g, r, b)

def set_framebuf(payload: bytes) -> bool:
    # led count * 4 bytes (r,g,b,l)
    expected_size = SIZE * 4
    if len(payload) != expected_size:
        logger.error(f'Invalid payload size: received {len(payload)} bytes, expected {expected_size} bytes')
        return False
    
    for i in range(SIZE):
        r = payload[i * 4]
        g = payload[i * 4 + 1]
        b = payload[i * 4 + 2]
        l = payload[i * 4 + 3]
        pixels[i] = brightness_hack(l, r, g, b)
    
    pixels.show()
    return True