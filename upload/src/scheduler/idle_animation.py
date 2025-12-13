"""Idle animation for LED tree when no jobs are running"""
import time
import math
from runner.leds import set_framebuf, get_led_count
import threading

# Idle animation state
idle_running = False
idle_thread = None

def idle_animation():
    """Gentle breathing rainbow effect when idle"""
    global idle_running
    led_count = get_led_count()
    frame = 0
    
    while idle_running:
        try:
            # Breathing effect with slow rainbow
            pulse = (math.sin(frame * 0.05) + 1) / 2  # 0-1
            brightness = int(pulse * 50 + 10)  # 10-60 brightness
            
            payload = bytearray()
            for i in range(led_count):
                hue = (frame * 2 + i * 360 / led_count) % 360
                # Simple HSV to RGB
                sector = int(hue / 60) % 6
                frac = (hue % 60) / 60.0
                
                if sector == 0:
                    r, g, b = 255, int(255 * frac), 0
                elif sector == 1:
                    r, g, b = int(255 * (1 - frac)), 255, 0
                elif sector == 2:
                    r, g, b = 0, 255, int(255 * frac)
                elif sector == 3:
                    r, g, b = 0, int(255 * (1 - frac)), 255
                elif sector == 4:
                    r, g, b = int(255 * frac), 0, 255
                else:
                    r, g, b = 255, 0, int(255 * (1 - frac))
                
                payload.extend([r, g, b, brightness])
            
            set_framebuf(bytes(payload))
            frame += 1
            time.sleep(0.05)
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
