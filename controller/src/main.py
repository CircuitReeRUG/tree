import socket
import neopixel
import board
import os
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def __find_pin(pin:int):
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

# named unix socket
SERVER_ADDRESS = os.environ.get('LED_SOCKET_PATH', '/tmp/led_socket')
SIZE = int(os.environ.get('TREE_LEDS', 16))
GPIO_PIN = __find_pin(int(os.environ.get('LED_GPIO_PIN', 18)))
pixels = neopixel.NeoPixel(GPIO_PIN, SIZE) #pyright: ignore[reportArgumentType]

def change_led(led_num, r, g, b, l) -> bool:
    if led_num < 0 or led_num >= SIZE:
        return False
    pixels[led_num] = brightness_hack(l, r, g, b)
    pixels.show()
    return True

def brightness_hack(l: float, r: int, g: int, b: int) -> tuple[int, int, int]:
    if l == 100:
        return (r, g, b)
    
    factor = l / 100.0
    r = int(r * factor)
    g = int(g * factor)
    b = int(b * factor)
    return (r, g, b)

def set_framebuf(payload: bytes) -> bool:
    # led count * 4 bytes (r,g,b,l)
    if len(payload) != SIZE * 4:
        return False
    
    for i in range(SIZE):
        r = payload[i * 4]
        g = payload[i * 4 + 1]
        b = payload[i * 4 + 2]
        l = payload[i * 4 + 3]
        if not change_led(i, r, g, b, l):
            return False
    
    return True

def main():
    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

    try:
        os.unlink(SERVER_ADDRESS)
    except OSError:
        if os.path.exists(SERVER_ADDRESS):
            raise

    server.bind(SERVER_ADDRESS)
    server.listen(1)

    logger.info('LED server is listening...')

    while True:
        connection, client_address = server.accept()
        try:
            logger.debug('Connection from %s', client_address)

            while True:
                data = connection.recv(12000) 
                if data:
                    if not set_framebuf(data):
                        logger.warning('Invalid data received')
                else:
                    break

        finally:
            connection.close()

if __name__ == '__main__':
    main()