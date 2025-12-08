#import "@preview/diatypst:0.8.0": *
#show: slides.with(
  title: "Control our Christmas Tree!",
  subtitle: "Via Python!",
  date: datetime.today().display(),
  authors: ("CircuitRee!"),
  title-color: rgb("#F6921D"),
)
#set text(font: "Fira Sans")


= The code stuff

== LED protocol
LED State: 4-tuple of integers
```python
(R, G, B, L)
```
- R, G, B: 0-255 (color)
- L: 0-100 (brightness)

LED Array: List of states
```python
[(255, 0, 0, 100), (0, 255, 0, 50), ...]
```

Array length must match LED count!

#align(center)[
  #text(fill: red, size: 2em, weight: "bold")[
    We have 100 LEDs
  ]
]

== Python Subset

*Allowed Standard Library*
- `math`, `random`

*Blocked*
- `os`, `sys`, `subprocess`, `ctypes`
- All external modules

*Extra Functions*:
- `getLEDCount()` - Returns the number of LEDs (100)
- `setLEDs(states)` - Update all LEDs with the given states
- `sleep(seconds)` - Pause execution for the specified duration

*Example Code*
```python
led_count = getLEDCount()
states = [[0, 0, 255, 100] for _ in range(led_count)]
setLEDs(states)
```

= The Infrastructure
== tree.cartof.io
#align(center + horizon)[
  #text(size:20pt)[
    *Everything happens here:*
  ]
#image("assets/qr.png", width:50%)
]

== Homepage
#image("assets/home.png")

== Submission screen
#image("assets/submission.png")

== Disclaimer
#align(center + horizon)[
  #text(size: 25pt)[
    Issues are *certainly* going to arise...
  ]
  #text(size: 10pt)[
    but do try to figure out as much as you can on your own -- help us help you.
  ]
]
= Questions?

== Outro
#align(center + horizon)[
  #text(size: 50pt)[

  *Let's light up this tree!*
  ]
]