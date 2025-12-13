import time
import threading

class DelayedCallback:
    def __init__(self, delay, callback):
        self.delay = delay
        self.callback = callback
        self.timer = None
        self.last_poke = time.time()
    
    def poke(self):
        self.last_poke = time.time()
        if self.timer and self.timer.is_alive():
            return
        self.timer = threading.Thread(target=self._wait, daemon=True)
        self.timer.start()
    
    def _wait(self):
        time.sleep(self.delay)
        if time.time() - self.last_poke >= self.delay:
            self.callback()
    
    def cancel(self):
        self.last_poke = time.time() + self.delay * 2
