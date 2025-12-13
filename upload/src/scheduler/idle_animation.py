"""Idle animation for LED tree when no jobs are running"""
import time
import math
import logging
from runner.leds import set_framebuf, get_led_count
import threading

# Setup logger
logger = logging.getLogger(__name__)

# Idle animation state
idle_running = False
idle_thread = None
fade_in_frames = 100  # Number of frames to fade in

def idle_animation():
    """Waiting animation - scanning pattern to show system is ready"""
    global idle_running
    led_count = get_led_count()
    frame = 0
    
    logger.info("Idle animation loop started")
    
    while idle_running:
        try:
            payload = bytearray()
            
            # Fade in effect - gradually increase intensity
            fade_factor = min(1.0, frame / fade_in_frames)
            
            # Scanner effect - like KITT from Knight Rider
            scanner_pos = frame % (led_count * 2)
            if scanner_pos >= led_count:
                scanner_pos = (led_count * 2 - 1) - scanner_pos
            
            tail_length = min(12, led_count // 3)
            
            for i in range(led_count):
                distance = abs(i - scanner_pos)
                
                if distance < tail_length:
                    # Blue scanner with fade
                    brightness = int(100 * (1 - distance / tail_length) * fade_factor)
                    r, g, b = int(0 * fade_factor), int(150 * fade_factor), int(255 * fade_factor)
                else:
                    # Dim background that fades in
                    r, g, b = int(20 * fade_factor), int(20 * fade_factor), int(30 * fade_factor)
                    brightness = int(100 * fade_factor)
                
                payload.extend([r, g, b, brightness])
            
            set_framebuf(bytes(payload))
            frame += 1
            time.sleep(0.03)  # Faster for more obvious movement
        except Exception as e:
            logger.error(f"Idle animation error: {e}", exc_info=True)
            break
    
    logger.info("Idle animation loop ended")

def start_idle_animation():
    """Start the idle animation in background"""
    global idle_running, idle_thread
    if not idle_running:
        idle_running = True
        idle_thread = threading.Thread(target=idle_animation, daemon=True)
        idle_thread.start()
        logger.info("Idle animation started")
    else:
        logger.debug("Idle animation already running")

def stop_idle_animation():
    """Stop the idle animation"""
    global idle_running
    if idle_running:
        idle_running = False
        if idle_thread:
            idle_thread.join(timeout=1)
        logger.info("Idle animation stopped")
    else:
        logger.debug("Idle animation already stopped")
