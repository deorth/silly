#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║   D U C K . E X E  ::  the rubber duck debugger                              ║
║                                                                              ║
║   You explain your problem to a duck. The duck floats. The duck blinks.      ║
║   The duck says "go on." Ninety seconds later you have fixed your bug and    ║
║   the duck has said nothing of substance. This is the correct outcome.       ║
║                                                                              ║
║   keys:  [enter] speak  [ctrl+f] bread  [ctrl+t] pet  [ctrl+g] just tell me  ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

from __future__ import annotations

import math
import random
import re
import time

from rich.segment import Segment
from rich.style import Style
from rich.text import Text

from textual.app import App, ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.strip import Strip
from textual.widget import Widget
from textual.widgets import Input, RichLog, Static

try:
    from pyfiglet import Figlet
except Exception:  # pragma: no cover
    Figlet = None


# ───────────────────────────── palette ──────────────────────────────────────
DUCK = "#ffd23f"
DUCK_SHADE = "#d99e12"
BILL = "#ff8c1a"
BILL_SHADE = "#c85f00"
EYE = "#140d04"
GLINT = "#ffffff"

WATER_TOP = "#1a6f8f"
WATER_DEEP = "#04202c"
FOAM = "#a8ecff"
BREAD_C = "#d9a566"
BREAD_SHADE = "#a87440"

AMBER = "#ffc857"
GHOST = "#e8f4ff"
DIM = "#4a7a8c"
POND_INK = "#0a2c3a"
REED = "#2f7d5a"


# ───────────────────────────── color helpers ────────────────────────────────
def _rgb(c: str) -> tuple[int, int, int]:
    return int(c[1:3], 16), int(c[3:5], 16), int(c[5:7], 16)


_BLEND_CACHE: dict[tuple[str, str, int], str] = {}


def blend(a: str, b: str, f: float) -> str:
    """Mix hex color a toward b by fraction f (cached, 1/64 steps)."""
    key = (a, b, int(f * 64))
    hit = _BLEND_CACHE.get(key)
    if hit is not None:
        return hit
    f = max(0.0, min(1.0, f))
    ar, ag, ab = _rgb(a)
    br, bg, bb = _rgb(b)
    out = "#%02x%02x%02x" % (
        int(ar + (br - ar) * f),
        int(ag + (bg - ag) * f),
        int(ab + (bb - ab) * f),
    )
    _BLEND_CACHE[key] = out
    return out


WATER_GRAD = [blend(WATER_TOP, WATER_DEEP, i / 23) for i in range(24)]
SKY_GRAD = [blend("#04141c", "#0e3f52", i / 23) for i in range(24)]


# ───────────────────────────── the duck sprite ──────────────────────────────
# The duck is drawn as pixel art at 2x vertical resolution: each terminal row
# holds two pixel rows, printed as "▀" with a foreground and a background.
# Sprites are cached per (scale, blink, tilt, beak) because there are only a
# dozen of them and we redraw twenty times a second.
_SPRITE_CACHE: dict[tuple, tuple[dict[tuple[int, int], str], int, int]] = {}


def _ellipse(px, cx, cy, rx, ry, color) -> None:
    if rx < 0.5 or ry < 0.5:
        return
    for y in range(int(cy - ry), int(cy + ry) + 1):
        dy = (y - cy) / ry
        if abs(dy) > 1.0:
            continue
        half = rx * math.sqrt(max(0.0, 1.0 - dy * dy))
        for x in range(int(cx - half), int(cx + half) + 1):
            px[(x, y)] = color


def _triangle(px, pts, color) -> None:
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    (x1, y1), (x2, y2), (x3, y3) = pts

    def side(ax, ay, bx, by, cx, cy):
        return (ax - cx) * (by - cy) - (bx - cx) * (ay - cy)

    for y in range(int(min(ys)), int(max(ys)) + 1):
        for x in range(int(min(xs)), int(max(xs)) + 1):
            d1 = side(x, y, x1, y1, x2, y2)
            d2 = side(x, y, x2, y2, x3, y3)
            d3 = side(x, y, x3, y3, x1, y1)
            neg = d1 < 0 or d2 < 0 or d3 < 0
            pos = d1 > 0 or d2 > 0 or d3 > 0
            if not (neg and pos):
                px[(x, y)] = color


def duck_sprite(scale: float, blink: bool, tilt: int, beak: bool):
    """Build (pixels, width, height) for one duck pose."""
    key = (round(scale, 2), blink, tilt, beak)
    hit = _SPRITE_CACHE.get(key)
    if hit is not None:
        return hit

    s = scale
    px: dict[tuple[int, int], str] = {}

    # tail: an upswept wedge off the back of the body
    _triangle(px, [(6.5 * s, 11.0 * s), (19 * s, 16 * s), (12 * s, 21.5 * s)], DUCK_SHADE)
    _triangle(px, [(7.5 * s, 12.2 * s), (18.5 * s, 16.2 * s), (12.5 * s, 20.5 * s)], DUCK)

    # body: shade pass, then the lit body nudged up-left for a rim of shadow
    _ellipse(px, 21 * s, 18 * s, 13 * s, 5.6 * s, DUCK_SHADE)
    _ellipse(px, 20.4 * s, 17.4 * s, 12.4 * s, 5.0 * s, DUCK)

    # neck
    _ellipse(px, 26 * s, 13 * s, 5 * s, 5 * s, DUCK)

    # head (leans with the tilt)
    hx = 28 * s + tilt * 1.6 * s
    hy = 8 * s - abs(tilt) * 0.4 * s
    _ellipse(px, hx, hy, 6.2 * s, 6.0 * s, DUCK_SHADE)
    _ellipse(px, hx - 0.4 * s, hy - 0.5 * s, 5.8 * s, 5.5 * s, DUCK)

    # bill: upper and lower mandible, parted when the duck is quacking
    gap = 1.6 * s if beak else 0.0
    bx = hx + 8 * s
    by = hy + 1.5 * s
    _ellipse(px, bx, by - gap * 0.6, 4.8 * s, 1.9 * s, BILL)
    _triangle(
        px,
        [(hx + 3.6 * s, by - 2.4 * s - gap * 0.6), (bx + 2 * s, by - 2.0 * s - gap * 0.6), (bx, by + 0.6 * s - gap * 0.6)],
        BILL,
    )
    if beak:
        _ellipse(px, bx - 0.6 * s, by + gap * 1.1, 4.0 * s, 1.3 * s, BILL_SHADE)
    else:
        _ellipse(px, bx - 0.4 * s, by + 1.5 * s, 4.2 * s, 0.9 * s, BILL_SHADE)

    # eye
    ex, ey = hx + 2.2 * s, hy - 2.0 * s
    if blink:
        for dx in range(int(-2.0 * s), int(2.0 * s) + 1):
            px[(int(ex + dx), int(ey))] = EYE
    else:
        _ellipse(px, ex, ey, max(1.0, 1.3 * s), max(1.0, 1.3 * s), EYE)
        if s >= 0.8:
            px[(int(ex - 0.6 * s), int(ey - 0.3 * s))] = GLINT

    if not px:
        return ({}, 1, 1)
    w = max(p[0] for p in px) + 1
    h = max(p[1] for p in px) + 1
    out = (px, w, h)
    _SPRITE_CACHE[key] = out
    return out


# ───────────────────────────── the pond ─────────────────────────────────────
class Pond(Widget):
    """A duck. On water. Bobbing. This is the whole feature."""

    DEFAULT_CSS = "Pond { background: #071e28; }"

    def __init__(self) -> None:
        super().__init__()
        self.t = 0.0
        self.blink_until = 0.0
        self.beak_until = 0.0
        self.tilt = 0
        self.tilt_until = 0.0
        self.delight = 0.0
        self.asleep = False
        self.ripples: list[list[float]] = []  # [x, radius, life]
        self.bread: list[float] | None = None  # [x, y_wobble_phase]
        self.reeds = [(0.03, 10), (0.08, 6), (0.93, 9), (0.98, 5)]
        self.buf: list[list[str | None]] = []
        self.surf: list[float] = []
        self._styles: dict[tuple[str | None, str | None], Style] = {}

    def on_mount(self) -> None:
        self.set_interval(1 / 20, self._tick)

    # ---- things the duck can be made to do ----
    def quack(self) -> None:
        self.beak_until = self.t + 0.45
        w = max(1, self.size.width)
        self.ripples.append([w * 0.5, 1.0, 1.0])

    def blink(self) -> None:
        self.blink_until = self.t + 0.16

    def head_tilt(self) -> None:
        self.tilt = random.choice((-1, 1))
        self.tilt_until = self.t + random.uniform(1.4, 3.0)

    def throw_bread(self) -> None:
        w = max(8, self.size.width)
        self.bread = [random.choice((2.0, w - 3.0)), random.random() * 6.28]

    def be_delighted(self) -> None:
        self.delight = 3.0

    # ---- the frame ----
    def _tick(self) -> None:
        self.t += 1 / 20
        if self.t > self.tilt_until:
            self.tilt = 0
        if self.delight > 0:
            self.delight = max(0.0, self.delight - 1 / 20)
        if random.random() < 0.012 and self.t > self.blink_until:
            self.blink()

        w, h = self.size.width, self.size.height
        if w <= 0 or h <= 0:
            return

        # bread drifts toward the duck and is eventually eaten
        if self.bread is not None:
            target = w * 0.5
            self.bread[0] += (1 if target > self.bread[0] else -1) * 0.35
            if abs(self.bread[0] - target) < 2.5:
                self.bread = None
                self.beak_until = self.t + 0.5
                self.be_delighted()
                self.ripples.append([w * 0.5, 1.0, 1.0])

        for r in self.ripples:
            r[1] += 0.8
            r[2] -= 0.035
        self.ripples = [r for r in self.ripples if r[2] > 0][-14:]
        if random.random() < 0.03:
            self.ripples.append([random.uniform(0, w), 1.0, 0.55])

        self._build(w, h)
        self.refresh()

    def _build(self, w: int, h: int) -> None:
        ph = h * 2
        buf: list[list[str | None]] = [[None] * w for _ in range(ph)]
        t = self.t
        waterline = ph * 0.68

        # the surface: two sine waves, gently out of phase
        surf = [
            waterline
            + 1.3 * math.sin(x * 0.17 + t * 1.6)
            + 0.9 * math.sin(x * 0.06 - t * 1.05)
            for x in range(w)
        ]
        self.surf = surf

        # night sky, lightening toward the horizon
        for y in range(ph):
            shade = SKY_GRAD[min(23, int((y / max(1.0, waterline)) * 23))]
            row = buf[y]
            for x in range(w):
                row[x] = shade

        for x in range(w):
            sy = int(surf[x])
            for y in range(max(0, sy), ph):
                d = (y - sy) / max(1.0, ph - sy)
                buf[y][x] = WATER_GRAD[min(23, int(d * 23))]
            if 0 <= sy < ph:
                buf[sy][x] = blend(WATER_TOP, FOAM, 0.35)

        # a few reeds at the banks, swaying out of time with each other
        for frac, tall in self.reeds:
            rx = int(frac * (w - 1))
            for k in range(tall):
                sway = math.sin(t * 0.8 + frac * 17) * 1.8 * (k / max(1, tall))
                x = int(rx + sway)
                y = int(surf[min(w - 1, max(0, rx))]) - k
                if 0 <= x < w and 0 <= y < ph:
                    buf[y][x] = REED if k % 3 else blend(REED, "#0b2f24", 0.45)

        # duck placement: bobbing, submerged to about four fifths
        scale = max(0.34, min(1.25, min(w / 46.0, ph / 30.0)))
        blink = t < self.blink_until or self.asleep
        beak = t < self.beak_until
        pixels, dw, dh = duck_sprite(scale, blink, self.tilt, beak)
        bob = math.sin(t * 1.5) * 1.1
        if self.delight > 0:
            bob += abs(math.sin(t * 7.0)) * 2.2
        left = (w - dw) // 2
        top = max(0.0, waterline - dh * 0.80 + bob)

        # reflection first, so the duck itself always wins the pixel
        for (sx, sy), color in pixels.items():
            x = left + sx
            if not (0 <= x < w):
                continue
            cy = top + sy
            ry = int(2 * surf[x] - cy + 1)
            wob = int(math.sin(cy * 0.55 + t * 2.4) * 1.6)
            rx = x + wob
            if 0 <= ry < ph and 0 <= rx < w and ry > surf[rx]:
                below = ry - surf[rx]
                if below > 7 and (rx + ry) % 2:
                    continue
                depth = below / max(1.0, ph - surf[rx])
                base = WATER_GRAD[min(23, int(depth * 23))]
                buf[ry][rx] = blend(color, base, min(0.92, 0.70 + below * 0.02))

        # ripple rings riding the surface
        for cx, r, life in self.ripples:
            for sign in (-1, 1):
                x = int(cx + sign * r)
                if 0 <= x < w:
                    y = int(surf[x])
                    if 0 <= y < ph:
                        buf[y][x] = blend(WATER_TOP, FOAM, min(1.0, life))

        # bread, floating
        if self.bread is not None:
            bx = int(self.bread[0])
            for x in (bx, bx + 1):
                if 0 <= x < w:
                    y = int(surf[x] - 1)
                    if 0 <= y < ph:
                        buf[y][x] = BREAD_C
                    if 0 <= y + 1 < ph:
                        buf[y + 1][x] = BREAD_SHADE

        # and finally the duck
        for (sx, sy), color in pixels.items():
            x, y = left + sx, int(top + sy)
            if 0 <= x < w and 0 <= y < ph:
                buf[y][x] = color

        self.buf = buf

    def _style(self, top: str | None, bottom: str | None) -> Style:
        key = (top, bottom)
        st = self._styles.get(key)
        if st is None:
            st = Style(color=top or POND_INK, bgcolor=bottom or POND_INK)
            self._styles[key] = st
        return st

    def render_line(self, y: int) -> Strip:
        w = self.size.width
        # a resize can land between _build() and render_line(); the next tick
        # rebuilds at the new size, so draw nothing rather than index off the end
        if not self.buf or y * 2 + 1 >= len(self.buf) or len(self.buf[0]) != w:
            return Strip.blank(w)
        top_row = self.buf[y * 2]
        bot_row = self.buf[y * 2 + 1]
        segments = [
            Segment("▀", self._style(top_row[x], bot_row[x])) for x in range(w)
        ]
        return Strip(segments, w)


# ───────────────────────────── telemetry ────────────────────────────────────
class Telemetry(Widget):
    """Gauges for a creature made of rubber."""

    DEFAULT_CSS = "Telemetry { height: 6; }"

    def __init__(self) -> None:
        super().__init__()
        self.patience = 100.0
        self.quack_pressure = 0.0
        self.bread = 0
        self.comprehension_flicker = 0.0

    def on_mount(self) -> None:
        self.set_interval(0.1, self.refresh)

    def _bar(self, t: Text, label: str, value: float, color: str, note: str) -> None:
        w = max(20, self.size.width)
        label_s = f"{label:<15}"
        bar_w = max(4, w - len(label_s) - len(note) - 3)
        filled = int(bar_w * max(0.0, min(100.0, value)) / 100)
        t.append(label_s, Style(color=color, bold=True))
        t.append("▐", Style(color=DIM))
        t.append("█" * filled, Style(color=color))
        t.append("░" * (bar_w - filled), Style(color="#123540"))
        t.append("▌", Style(color=DIM))
        t.append(note + "\n", Style(color=GHOST))

    def render(self) -> Text:
        t = Text()
        # comprehension flickers to 1% now and then, then thinks better of it
        comp = self.comprehension_flicker
        self._bar(t, "COMPREHENSION", comp, "#ff6b6b", f"{int(comp):>3}%")
        self._bar(t, "PATIENCE", self.patience, AMBER, f"{int(self.patience):>3}%")
        self._bar(t, "QUACK PRESSURE", self.quack_pressure, "#ffa94d", f"{int(self.quack_pressure):>3}%")
        self._bar(t, "EMPATHY*", 100, "#8ce99a", "100%")
        self._bar(t, "BUOYANCY", 100, "#74c0fc", "100%")
        t.append(f"{'BREAD':<15}", Style(color=BREAD_C, bold=True))
        t.append("🍞 " * min(8, self.bread) or "—", Style(color=BREAD_C))
        t.append(f"  ({self.bread} fed)", Style(color=DIM))
        return t


# ───────────────────────────── the duck's brain ─────────────────────────────
# Note the ratio: mostly noise, occasionally a question, never an answer.
ACKS = [
    "*blinks*",
    "*tilts head*",
    "go on.",
    "*nods, slowly*",
    "mm.",
    "*maintains eye contact*",
    "and then?",
    "*stares at a point slightly behind you*",
    "quack.",
    "*ruffles feathers noncommittally*",
    "sure. sure.",
    "*floats*",
    "keep going.",
    "*paddles thoughtfully*",
    "hm.",
    "*does not blink*",
    "right, right.",
    "*waits*",
    "*preens one wing, still listening*",
    "uh huh.",
]

PROMPTS = [
    "what did you *expect* to happen?",
    "when did it last work?",
    "have you read the error message. out loud. all of it.",
    "which part have you seen, and which part are you assuming?",
    "does it do that every time, or only when you're watching?",
    "what changed?",
    "did you save the file.",
    "what's the smallest version of this that still breaks?",
    "have you run it anywhere that isn't your laptop?",
    "so what's it doing instead?",
    "say that again, but slower.",
    "why should that work?",
    "who else writes to it?",
    "are you sure that's the code that's running?",
    "is it that line, or the line before it?",
    "what would you check first if it were someone else's bug?",
]

WISDOM = [
    "*it is a rubber duck. it does not know what a mutex is. it is right anyway.*",
    "*the duck has no opinion on your architecture. the duck has an opinion on your assumptions.*",
    "*the duck would like the stack trace, not the summary of the stack trace.*",
]

DRIFT = [
    "*has drifted slightly downstream*",
    "you lost me at \"basically\".",
    "*was following, right up until the second \"and also\"*",
    "*that was four sentences ago. we're still in it.*",
    "*gently paddles back into earshot*",
]

IDLE = [
    "*quack*",
    "*bobs*",
    "*looks at you*",
    "*waits, patiently, as is its nature*",
    "still here.",
    "*a single ripple*",
]

# keyword → the duck has been through this before
KEYWORDS: list[tuple[str, list[str]]] = [
    (r"\bdns\b", ["*it's always DNS.*", "it's DNS. it's always DNS. quack."]),
    (r"\bcach(e|ing|ed)\b", ["there are only two hard things. this is one of them.",
                             "invalidation, naming, or off-by-one. pick your fighter."]),
    (r"\b(race|async|await|thread|concurren\w*|deadlock|mutex)\b",
     ["*quacks in nondeterministic order*", "*two quacks arrive. their order is not guaranteed.*"]),
    (r"\bregex|regular expression\b", ["now you have two problems. *quack*"]),
    (r"\b(timezone|utc|dst|daylight)\b", ["*shudders*", "*visibly ages*"]),
    (r"\bcors\b", ["*sympathetic quack*", "*has also been blocked by a preflight*"]),
    (r"works on my machine", ["*writes that down. does not have a pen. does not have hands.*"]),
    (r"\b(unicode|utf-?8|encoding|mojibake)\b", ["*makes a noise like â€œ*"]),
    (r"\b(float|rounding|decimal)\b", ["0.1 + 0.2. *stares*"]),
    (r"off[- ]by[- ]one", ["off by two, then."]),
    (r"\b(memory )?leak\w*\b", ["*checks own buoyancy. fine. yours?*"]),
    (r"\b(prod|production)\b", ["*eyes widen very slightly*"]),
    (r"\b(friday|deploy|ship it)\b", ["*swims away*", "*begins slowly paddling toward the reeds*"]),
    (r"\b(git|rebase|merge conflict|force[- ]push)\b",
     ["*has never rebased. has never needed to.*", "*quack. (reflog.)*"]),
    (r"\byaml\b", ["*hisses. ducks cannot hiss. it managed.*", "norway. it's norway again, isn't it."]),
    (r"\b(kubernetes|k8s|helm|cluster)\b", ["*capsizes*"]),
    (r"\b(javascript|npm|node_modules|typescript)\b", ["*quack. (this means NaN.)*"]),
    (r"\bdocker\b", ["have you tried it in a slightly larger box?"]),
    (r"\b(ssl|tls|cert\w*)\b", ["expired. *quack*. check the date."]),
    (r"\b(test|tests|spec)\b", ["would a test have caught it?", "and the test passes?"]),
    (r"\bwork(s|ed|ing)? (fine|locally)\b", ["*tilts head, unconvinced*"]),
    (r"\b(ai|llm|claude|gpt|copilot|model)\b", ["*looks directly at you*", "*the duck predates this and will outlast it*"]),
    (r"\b(i think|i guess|probably|maybe)\b", ["you think, or you know?"]),
    (r"\bshould\b", ["\"should\".", "*\"should\" is doing a lot of work in that sentence*"]),
    (r"\bobviously\b", ["*blinks*"]),
    (r"\bjust\b", ["\"just\".", "*there is no \"just\"*"]),
    (r"\b(weird|strange|impossible|can't be|cannot be)\b", ["it is happening, so it is possible. *quack*"]),
    (r"\b(fuck|shit|damn|bloody|christ)\b", ["*sympathetic quack*", "*floats supportively*"]),
    (r"\bhelp\b", ["*is helping*"]),
    (r"\b(hello|hi|hey|good morning)\b", ["*quack*", "*bobs once, formally*"]),
    (r"\b(thank|thanks|cheers)\b", ["*accepts this as its due*"]),
    (r"\bduck\b", ["*that's me*"]),
]

EUREKA = re.compile(
    r"\b(oh+|ohh+|aha+|wait|hang on|hold on|nevermind|never mind|i see|of course|"
    r"found it|got it|that'?s it|there it is|duh|god damn it|goddammit|omg|it was)\b",
    re.I,
)

JUST_TELL_ME = [
    "quack.",
    "*quack*",
    "quack. (this is the whole feature.)",
    "*shakes head*  quack.",
    "no. *quack*",
]


def duck_reply(text: str) -> tuple[str, str]:
    """Return (line, mood) for whatever the human just said."""
    low = text.lower()
    words = low.split()

    for pattern, replies in KEYWORDS:
        if re.search(pattern, low):
            if random.random() < 0.8:
                return random.choice(replies), "knowing"

    if len(words) > 45:
        return random.choice(DRIFT), "drifting"
    if len(words) <= 3:
        return random.choice(["go on.", "*waits*", "and?", "*tilts head*"]), "attentive"
    if text.rstrip().endswith("?"):
        return random.choice([
            "*stares*",
            "what do you think?",
            "*that was a question. the duck notes this.*",
            "you're asking the duck?",
            "mm. what would that mean if it were true?",
        ]), "skeptical"
    if random.random() < 0.05:
        return random.choice(WISDOM), "knowing"
    if random.random() < 0.34:
        return random.choice(PROMPTS), "attentive"
    return random.choice(ACKS), "listening"


# ───────────────────────────── celebration overlay ──────────────────────────
class Flash(Static):
    """BUG SOLVED. The duck accepts no credit and will be given all of it."""

    def on_mount(self) -> None:
        self.display = False

    def fire(self, headline: str, sub: str, color: str) -> None:
        body = headline
        if Figlet is not None:
            for font in ("ansi_shadow", "big", "standard"):
                try:
                    body = Figlet(font=font, width=200).renderText(headline).rstrip("\n")
                    break
                except Exception:
                    continue
        t = Text(body + "\n", style=Style(color=color, bold=True), justify="center")
        t.append(sub, Style(color=GHOST, italic=True))
        self.update(t)
        self.display = True
        self.set_timer(2.0, self._hide)

    def _hide(self) -> None:
        self.display = False


# ───────────────────────────── the app ──────────────────────────────────────
class DuckDebugger(App):
    TITLE = "duck.exe :: rubber duck debugger"

    CSS = """
    Screen {
        layers: base overlay;
        background: #04141c;
        color: #ffc857;
    }

    #banner {
        height: auto;
        content-align: center middle;
        text-align: center;
        padding: 0 1;
    }

    #main { height: 1fr; }

    #left { width: 1fr; min-width: 30; }

    #pond-pane {
        height: 1fr;
        border: round #1a6f8f;
        border-title-color: #ffd23f;
        border-title-align: center;
    }
    Pond { height: 1fr; }

    #tele-pane {
        height: auto;
        border: round #1a6f8f;
        border-title-color: #ffd23f;
        border-title-align: center;
        padding: 0 1;
    }

    #right { width: 1fr; }

    #transcript {
        height: 1fr;
        border: round #1a6f8f;
        border-title-color: #ffd23f;
        border-title-align: center;
        background: #051a24;
        scrollbar-color: #1a6f8f;
        scrollbar-background: #051a24;
    }

    #say {
        height: 3;
        border: round #2f7d5a;
        border-title-color: #8ce99a;
        border-title-align: left;
        background: #051a24;
        color: #e8f4ff;
    }
    #say:focus { border: round #8ce99a; }

    #status {
        dock: bottom;
        height: 1;
        background: #062430;
        color: #ffc857;
        padding: 0 1;
    }

    #flash {
        layer: overlay;
        width: 100%;
        height: 100%;
        background: #04141c 88%;
        content-align: center middle;
        text-align: center;
    }
    """

    BINDINGS = [
        ("ctrl+q", "quit", "leave the duck"),
        ("ctrl+f,ctrl+b", "bread", "bread"),
        ("ctrl+t", "pet", "pet the duck"),
        ("ctrl+g", "just_tell_me", "just tell me"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.started = time.time()
        self.your_words = 0
        self.duck_words = 0
        self.quacks = 0
        self.bugs_solved = 0
        self.advice_given = 0  # this never moves. that is the joke. it is also true.
        self.last_spoke = time.time()

    # ----- layout -----
    def compose(self) -> ComposeResult:
        yield Static(self._banner(), id="banner")
        with Horizontal(id="main"):
            with Vertical(id="left"):
                with Container(id="pond-pane") as pp:
                    pp.border_title = "// THE DUCK"
                    yield Pond()
                with Container(id="tele-pane") as tp:
                    tp.border_title = "// DUCK TELEMETRY  (* simulated)"
                    yield Telemetry()
            with Vertical(id="right"):
                log = RichLog(highlight=False, markup=True, wrap=True,
                              min_width=12, max_lines=2000, auto_scroll=True,
                              id="transcript")
                log.border_title = "// ~/rubber-duck :: session transcript"
                yield log
                inp = Input(placeholder="explain your problem to the duck…  (/help)",
                            id="say")
                inp.border_title = "you"
                yield inp
        yield Static("", id="status")
        yield Flash(id="flash")

    def on_mount(self) -> None:
        self.log_view = self.query_one("#transcript", RichLog)
        self.pond = self.query_one(Pond)
        self.tele = self.query_one(Telemetry)
        self.say(f"[{DIM}]" + "─" * 52 + "[/]")
        self.say(f"[b {DUCK}]duck.exe[/] [{DIM}]— a rubber duck is listening. it will not "
                 f"interrupt, advise, or judge.[/]")
        self.say(f"[{DIM}]it may, however, blink.[/]")
        self.say(f"[{DIM}]" + "─" * 52 + "[/]")
        self.duck_says("*quack*", "listening")
        self.query_one("#say", Input).focus()
        self.set_interval(0.5, self._status)
        self.set_interval(0.25, self._idle)

    def _banner(self) -> Text:
        block = "RUBBER DUCK"
        if Figlet is not None:
            for font in ("standard", "slant", "small"):
                try:
                    block = Figlet(font=font, width=200).renderText("rubber duck").rstrip("\n")
                    break
                except Exception:
                    continue
        grad = [DUCK, "#ffca28", BILL, "#ffca28", DUCK]
        t = Text(justify="center")
        for i, line in enumerate(block.split("\n")):
            t.append(line + "\n", Style(color=grad[i % len(grad)], bold=True))
        t.append("[ ", Style(color=DIM))
        t.append("it does not know either", Style(color=GHOST, italic=True))
        t.append(" · ", Style(color=DIM))
        t.append("that has never stopped it", Style(color=REED, italic=True))
        t.append(" ]", Style(color=DIM))
        return t

    # ----- transcript helpers -----
    def say(self, markup: str) -> None:
        self.log_view.write(markup)

    def duck_says(self, line: str, mood: str = "listening") -> None:
        self.duck_words += len(line.split())
        color = {
            "listening": DUCK,
            "attentive": AMBER,
            "skeptical": BILL,
            "knowing": "#8ce99a",
            "drifting": DIM,
            "delighted": "#ffe066",
        }.get(mood, DUCK)
        style = "i " if line.startswith("*") else "b "
        self.say(f"[{DIM}]🦆 >[/] [{style}{color}]{line}[/]")
        if "quack" in line.lower():
            self.quacks += 1
        self.pond.quack()
        if mood == "skeptical":
            self.pond.head_tilt()
        if mood == "drifting":
            self.pond.blink()
        self.tele.quack_pressure = 0.0

    # ----- input -----
    def on_input_submitted(self, event: Input.Submitted) -> None:
        text = event.value.strip()
        event.input.value = ""
        if not text:
            self.pond.blink()
            return

        if text.startswith("/"):
            self._command(text.split()[0].lower())
            return

        self.your_words += len(text.split())
        self.last_spoke = time.time()
        self.say(f"[{DIM}]you >[/] [{GHOST}]{text}[/]")

        # rambling costs patience; brevity earns it back
        n = len(text.split())
        self.tele.patience = max(0.0, min(100.0, self.tele.patience - max(0, n - 12) * 0.8 + 4))
        if random.random() < 0.25:
            self.tele.comprehension_flicker = 1.0
            self.set_timer(0.8, lambda: setattr(self.tele, "comprehension_flicker", 0.0))

        if EUREKA.search(text):
            self._eureka()
            return

        line, mood = duck_reply(text)
        self.set_timer(random.uniform(0.35, 1.1), lambda: self.duck_says(line, mood))

    def _command(self, cmd: str) -> None:
        commands = {
            "/bread": self.action_bread,
            "/feed": self.action_bread,
            "/pet": self.action_pet,
            "/tell": self.action_just_tell_me,
            "/tellme": self.action_just_tell_me,
            "/help": self._help,
            "/keys": self._help,
        }
        run = commands.get(cmd)
        if run is None:
            self.say(f"[{DIM}]the duck does not know {cmd}. it knows "
                     f"/bread /pet /tell /help[/]")
            self.pond.blink()
            return
        run()

    def _help(self) -> None:
        self.say(f"[b {DUCK}]the duck responds to:[/]")
        for keys, what in (
            ("enter", "say it out loud"),
            ("ctrl+f  /bread", "throw bread"),
            ("ctrl+t  /pet", "pet the duck"),
            ("ctrl+g  /tell", "demand a straight answer"),
            ("ctrl+q", "leave the duck"),
        ):
            self.say(f"  [{AMBER}]{keys:<16}[/][{GHOST}]{what}[/]")

    def _eureka(self) -> None:
        self.bugs_solved += 1
        self.pond.be_delighted()
        self.duck_says(random.choice([
            "quack.",
            "*quack* (it was never going to be the compiler.)",
            "*the duck said nothing. the duck takes full credit.*",
            "*nods once, deeply*",
        ]), "delighted")
        self.query_one("#flash", Flash).fire(
            "BUG SOLVED",
            f"advice given: {self.advice_given}   ·   bugs solved: {self.bugs_solved}",
            DUCK,
        )
        self.say(f"[b {DUCK}]── BUG SOLVED ── [/][{DIM}]advice given: "
                 f"{self.advice_given} · you did that yourself[/]")

    # ----- ambient duck -----
    def _idle(self) -> None:
        quiet = time.time() - self.last_spoke
        self.tele.quack_pressure = min(100.0, self.tele.quack_pressure + 0.45)
        self.tele.patience = min(100.0, self.tele.patience + 0.12)
        self.pond.asleep = quiet > 180
        if self.tele.quack_pressure >= 100 and quiet > 22:
            self.duck_says(random.choice(IDLE), "listening")

    # ----- actions -----
    def action_bread(self) -> None:
        self.tele.bread += 1
        self.pond.throw_bread()
        self.say(f"[{DIM}]you >[/] [{BREAD_C}]*throws bread*[/]")
        self.set_timer(1.4, lambda: self.duck_says(random.choice([
            "*eats bread. this does not help. it does help.*",
            "*delighted*",
            "*bread accepted. problem unchanged. morale improved.*",
            "*quack!*",
        ]), "delighted"))

    def action_just_tell_me(self) -> None:
        self.say(f"[{DIM}]you >[/] [{GHOST}]just tell me what's wrong with it[/]")
        self.duck_says(random.choice(JUST_TELL_ME), "skeptical")

    def action_pet(self) -> None:
        self.say(f"[{DIM}]you >[/] [{GHOST}]*pets the duck*[/]")
        self.pond.be_delighted()
        self.duck_says(random.choice([
            "*squeaks*",
            "*is rubber. squeaks accordingly.*",
            "*leans into it*",
        ]), "delighted")

    # ----- status bar -----
    def _status(self) -> None:
        el = int(time.time() - self.started)
        t = Text()
        t.append(f" {el // 60:02d}:{el % 60:02d} ", Style(color=DUCK, bold=True))
        t.append("│ you ", Style(color=DIM))
        t.append(f"{self.your_words}w", Style(color=GHOST))
        t.append(" · duck ", Style(color=DIM))
        t.append(f"{self.duck_words}w", Style(color=GHOST))
        t.append(" · quacks ", Style(color=DIM))
        t.append(f"{self.quacks}", Style(color=BILL, bold=True))
        t.append(" │ advice given: ", Style(color=DIM))
        t.append(f"{self.advice_given}", Style(color="#ff6b6b", bold=True))
        t.append(" · bugs solved: ", Style(color=DIM))
        t.append(f"{self.bugs_solved}", Style(color="#8ce99a", bold=True))
        t.append(" │ ^f bread ^t pet ^g tell-me ^q leave ", Style(color=DIM))
        self.query_one("#status", Static).update(t)


if __name__ == "__main__":
    DuckDebugger().run()
