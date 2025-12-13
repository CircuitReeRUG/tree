"""LED control module - manages NeoPixel LEDs on Raspberry Pi"""
import neopixel
import board
import os

def __find_pin(pin):
    pins = {10: board.D10, 12: board.D12, 18: board.D18, 21: board.D21}
    if pin not in pins:
        raise ValueError(f'Pin {pin} not supported')
    return pins[pin]

SIZE = int(os.environ.get('TREE_LEDS', 16))
GPIO_PIN = __find_pin(int(os.environ.get('LED_GPIO_PIN', 18)))
pixels = neopixel.NeoPixel(GPIO_PIN, SIZE, brightness=0.2, auto_write=False, pixel_order=neopixel.RGB)

def get_led_count():
    return SIZE

def brightness_hack(l, r, g, b):
    if l == 100:
        return (r, g, b)
    factor = l / 100.0
    return (int(r * factor), int(g * factor), int(b * factor))

def set_framebuf(payload):
    if len(payload) != SIZE * 4:
        return False
    
    for i in range(SIZE):
        r, g, b, l = payload[i*4:i*4+4]
        pixels[i] = brightness_hack(l, r, g, b)
    
    pixels.show()
    return True