"""Idle animation for LED tree when no jobs are running"""
import time
import math
import logging
from runner.leds import set_framebuf, get_led_count
import threading

logger = logging.getLogger(__name__)

idle_running = False
idle_thread = None
fade_in_frames = 100

def idle_animation():
    global idle_running
    led_count = get_led_count()
    frame = 0
    
    logger.info("Idle animation loop started")
    
    while idle_running:
        try:
            payload = bytearray()
            
            # Fade in effect
            fade_factor = min(1.0, frame / fade_in_frames)
            
            # Pulsing wave effect
            for i in range(led_count):
                # Create a wave that travels down the tree
                wave = math.sin((i / led_count * 4 * math.pi) + (frame / 20))
                brightness = int((wave * 0.5 + 0.5) * 100 * fade_factor)
                
                # Cool blue-purple gradient
                r = int(80 * fade_factor)
                g = int(50 * fade_factor)
                b = int(200 * fade_factor)
                
                payload.extend([r, g, b, brightness])
            
            set_framebuf(bytes(payload))
            frame += 1
            time.sleep(0.05)
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
