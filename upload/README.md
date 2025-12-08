This folder houses the code upload/editor + scheduler + runner + queue visualization page.

# The runner

| Function | Parameters | Returns | Description |
|----------|-----------|---------|-------------|
| `getLEDCount()` | None | `int` | Returns the total number of LEDs in the tree |
| `setLEDs(states)` | `list[tuple[int,int,int,int]]` | `bool` | Sets all LED colors/brightness simultaneously |
| `clearLEDs()` | None | `None` | Turns off all LEDs (sets brightness to 0) |
| `sleep(seconds)` | `float` | `None` | Pauses execution for specified duration (max 10s) |
| `print(...)` | `*args` | `None` | Prints output (collected and returned as program output) |

Only access to `math` and `random` are provided until further notice.

You also get a couple of constants:

```py
RED = (255, 0, 0, 100)
GREEN = (0, 255, 0, 100)
BLUE = (0, 0, 255, 100)
YELLOW = (255, 255, 0, 100)
CYAN = (0, 255, 255, 100)
MAGENTA = (255, 0, 255, 100)
WHITE = (255, 255, 255, 100)
ORANGE = (255, 165, 0, 100)
PURPLE = (128, 0, 128, 100)
PINK = (255, 192, 203, 100)
OFF = (0, 0, 0, 0)
```
