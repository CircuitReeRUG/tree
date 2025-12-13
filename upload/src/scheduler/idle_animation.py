import time
import math
import threading
import sys, os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from runner.exposed import setLEDs, getLEDCount

idle_running = False
idle_thread = None

def idle_animation():
    global idle_running
    led_count = getLEDCount()
    frame = 0
    
    while idle_running:
        try:
            fade = min(1.0, frame / 100)
            states = []
            
            for i in range(led_count):
                wave = math.sin((i / led_count * 4 * math.pi) + (frame / 20))
                brightness = int((wave * 0.5 + 0.5) * 100 * fade)
                r, g, b = int(80 * fade), int(50 * fade), int(200 * fade)
                states.append((r, g, b, brightness))
            
            setLEDs(states)
            frame += 1
            time.sleep(0.05)
        except:
            break

def start_idle_animation():
    global idle_running, idle_thread
    if not idle_running:
        idle_running = True
        idle_thread = threading.Thread(target=idle_animation, daemon=True)
        idle_thread.start()

def stop_idle_animation():
    global idle_running
    if idle_running:
        idle_running = False
        if idle_thread:
            idle_thread.join(timeout=1)
