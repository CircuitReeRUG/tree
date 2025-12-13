"""Idle animation for LED tree when no jobs are running"""
import time
import math
from runner.leds import set_framebuf, get_led_count
import threading

# Idle animation state
idle_running = False
idle_thread = None

def idle_animation():
    """Waiting animation - scanning pattern to show system is ready"""
    global idle_running
    led_count = get_led_count()
    frame = 0
    
    while idle_running:
        try:
            payload = bytearray()
            
            # Scanner effect - like KITT from Knight Rider
            scanner_pos = frame % (led_count * 2)
            if scanner_pos >= led_count:
                scanner_pos = (led_count * 2 - 1) - scanner_pos
            
            tail_length = min(12, led_count // 3)
            
            for i in range(led_count):
                distance = abs(i - scanner_pos)
                
                if distance < tail_length:
                    # Blue scanner with fade
                    brightness = int(100 * (1 - distance / tail_length))
                    r, g, b = 0, 150, 255  # Cyan/blue color
                else:
                    # Dim background
                    r, g, b = 20, 20, 30
                    brightness = 100
                
                payload.extend([r, g, b, brightness])
            
            set_framebuf(bytes(payload))
            frame += 1
            time.sleep(0.03)  # Faster for more obvious movement
        except Exception as e:
            print(f"Idle animation error: {e}")
            break

def start_idle_animation():
    """Start the idle animation in background"""
    global idle_running, idle_thread
    if not idle_running:
        idle_running = True
        idle_thread = threading.Thread(target=idle_animation, daemon=True)
        idle_thread.start()
        print("Idle animation started")

def stop_idle_animation():
    """Stop the idle animation"""
    global idle_running
    if idle_running:
        idle_running = False
        if idle_thread:
            idle_thread.join(timeout=1)
        print("Idle animation stopped")
