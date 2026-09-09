#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║   S O R T I N G   G R A N D   P R I X                                        ║
║                                                                              ║
║   Seven sorting algorithms. One shuffled array each. No handicaps: every     ║
║   racer gets the same number of operations per tick, so the finishing order  ║
║   is the real complexity class, live, in front of a paying crowd.            ║
║                                                                              ║
║   Bogosort has never won. Bogosort will never win. Bogosort believes.        ║
║                                                                              ║
║   keys:  [space] pause   [r] restart   [q] leave the paddock                 ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

from __future__ import annotations

import random
import time
from itertools import count

from rich.style import Style
from rich.text import Text

from textual.app import App, ComposeResult
from textual.containers import Container, Vertical
from textual.widget import Widget
from textual.widgets import RichLog, Static

try:
    from pyfiglet import Figlet
except Exception:  # pragma: no cover
    Figlet = None


# ───────────────────────────── palette ──────────────────────────────────────
TRACK = "#0d1b2a"
ASPHALT = "#16324a"
LINE = "#2d5f7f"
GOLD = "#ffd60a"
SILVER = "#c9d6df"
BRONZE = "#cd7f32"
GHOST = "#e8f1f8"
DIM = "#5a7f96"
GREEN = "#5ee07f"
RED = "#ff5c72"
WHITE = "#ffffff"

BARS = "▁▂▃▄▅▆▇█"
N = 40                  # elements on the grid
OPS_PER_TICK = 2        # every racer gets exactly this many, every tick
TICK = 1 / 20


# ───────────────────────────── the racers ───────────────────────────────────
# Each is a generator over a list it mutates in place, yielding once per
# operation. Nothing is faked: the bars you see are the actual array.
def gen_quick(a: list[int]):
    stack = [(0, len(a) - 1)]
    while stack:
        lo, hi = stack.pop()
        if lo >= hi:
            continue
        pivot = a[hi]
        i = lo
        for j in range(lo, hi):
            if a[j] <= pivot:
                a[i], a[j] = a[j], a[i]
                i += 1
            yield
        a[i], a[hi] = a[hi], a[i]
        yield
        stack.append((lo, i - 1))
        stack.append((i + 1, hi))


def gen_insertion(a: list[int]):
    for i in range(1, len(a)):
        j = i
        while j > 0 and a[j - 1] > a[j]:
            a[j - 1], a[j] = a[j], a[j - 1]
            j -= 1
            yield
        yield


def gen_bubble(a: list[int]):
    n = len(a)
    for i in range(n):
        swapped = False
        for j in range(n - 1 - i):
            if a[j] > a[j + 1]:
                a[j], a[j + 1] = a[j + 1], a[j]
                swapped = True
            yield
        if not swapped:
            return


def gen_stalin(a: list[int]):
    """Any element out of order is removed. Permanently. O(n), no appeals."""
    i = 1
    while i < len(a):
        if a[i] < a[i - 1]:
            del a[i]
        else:
            i += 1
        yield


def gen_sleep(a: list[int]):
    """Every element sleeps for a while proportional to itself, then reports."""
    vals = list(a)
    order = sorted(range(len(vals)), key=lambda i: vals[i])
    woken: list[int] = []
    taken: set[int] = set()
    for idx in order:
        for _ in range(max(1, int(vals[idx] * 0.85))):
            yield
        woken.append(vals[idx])
        taken.add(idx)
        a[:] = woken + [vals[i] for i in range(len(vals)) if i not in taken]


def gen_bogo(a: list[int]):
    """Shuffle. Check. Repeat. The purest expression of hope in computing."""
    while any(a[i] > a[i + 1] for i in range(len(a) - 1)):
        random.shuffle(a)
        yield


def gen_miracle(a: list[int]):
    """Checks whether the array has sorted itself. That is the entire algorithm."""
    while any(a[i] > a[i + 1] for i in range(len(a) - 1)):
        yield


FIELD = [
    # name, colour, generator, quoted odds, complexity as the form guide
    ("QUICKSORT", "#4cc9f0", gen_quick, 1.2, "O(n log n)"),
    ("INSERTION SORT", "#b5179e", gen_insertion, 6.5, "O(n²)"),
    ("BUBBLE SORT", "#f72585", gen_bubble, 9.0, "O(n²)"),
    ("STALIN SORT", "#ff9e00", gen_stalin, 2.8, "O(n)"),
    ("SLEEP SORT", "#7209b7", gen_sleep, 12.0, "O(zzz)"),
    ("BOGOSORT", "#ffd60a", gen_bogo, 4.0e8, "O(n·n!)"),
    ("MIRACLE SORT", "#90e0ef", gen_miracle, float("inf"), "O(faith)"),
]


class Racer:
    def __init__(self, name, colour, genfn, odds, form, data):
        self.name = name
        self.colour = colour
        self.odds = odds
        self.form = form
        self.data = list(data)
        self.start_len = len(data)
        self.gen = genfn(self.data)
        self.ops = 0
        self.done = False
        self.finished_at: float | None = None
        self.place: int | None = None

    @property
    def removed(self) -> int:
        return self.start_len - len(self.data)

    @property
    def progress(self) -> float:
        """Sortedness: the fraction of adjacent pairs that are in order."""
        d = self.data
        if len(d) < 2:
            return 1.0
        ok = sum(1 for i in range(len(d) - 1) if d[i] <= d[i + 1])
        return ok / (len(d) - 1)

    def step(self, ops: int) -> None:
        if self.done:
            return
        for _ in range(ops):
            try:
                next(self.gen)
                self.ops += 1
            except StopIteration:
                self.done = True
                self.finished_at = time.time()
                return


# ───────────────────────────── the track ────────────────────────────────────
class Track(Widget):
    """One lane per racer. The bars are the live array, not a progress bar."""

    def __init__(self, app_ref) -> None:
        super().__init__()
        self.app_ref = app_ref

    def render(self) -> Text:
        t = Text()
        racers = self.app_ref.racers
        ranked = self.app_ref.standings()
        width = max(40, self.size.width)
        for pos, r in enumerate(ranked, start=1):
            medal = {1: GOLD, 2: SILVER, 3: BRONZE}.get(pos, DIM)
            t.append(f"{pos:>2} ", Style(color=medal, bold=pos <= 3))
            t.append("▸ ", Style(color=r.colour))
            t.append(f"{r.name:<15}", Style(color=r.colour, bold=True))

            # the array itself, drawn as bar glyphs; settled elements go green
            lane = Text()
            top = max(self.app_ref.values) if self.app_ref.values else 1
            target = sorted(r.data)
            for i, v in enumerate(r.data):
                glyph = BARS[min(len(BARS) - 1, int(v / top * (len(BARS) - 1)))]
                settled = v == target[i]
                lane.append(glyph, Style(color=GREEN if settled else r.colour))
            pad = r.start_len - len(r.data)
            if pad:
                lane.append("·" * pad, Style(color="#3a2a1a"))
            t.append_text(lane)

            pct = r.progress * 100
            t.append(f" {pct:>5.1f}%", Style(color=GHOST if not r.done else GREEN,
                                             bold=r.done))
            t.append(f" {self.app_ref.live_odds(r):>9}", Style(color=DIM))
            if r.done:
                note = "FINISHED" if r.removed == 0 else f"FINISHED −{r.removed}"
                t.append(f"  {note}", Style(color=GREEN, bold=True))
            t.append("\n")
        return t


# ───────────────────────────── commentary ───────────────────────────────────
CHIP, DEL = "CHIP", "DEL"

OPENERS = [
    (CHIP, "and they're away! forty elements, seven algorithms, one shuffle."),
    (DEL, "the crowd is here for bogosort. the crowd is always here for bogosort."),
]

BOGO_LINES = [
    "BOGOSORT SHUFFLES AGAIN, FOLKS—",
    "—it was almost sorted. it shuffled anyway.",
    "bogosort has now tried {ops} arrangements of forty elements.",
    "there are 8×10⁴⁷ arrangements. bogosort has seen {ops} of them.",
    "bogosort is not losing. bogosort is exploring.",
    "somewhere in the permutation space, there is a sorted array. bogosort believes.",
]

MIRACLE_LINES = [
    "miracle sort is doing nothing. that is the algorithm working correctly.",
    "miracle sort awaits a cosmic ray. it has been {ops} checks.",
    "no divine intervention in lane seven. we go again.",
    "miracle sort remains in the hands of physics.",
]

STALIN_LINES = [
    "STALIN SORT has removed {removed} elements. the array is now sorted.",
    "stalin sort finishes early — it always does. the field is {removed} shorter.",
    "the stewards are reviewing the {removed} missing elements.",
    "stalin sort's array is perfectly sorted and missing most of its data.",
]

CHATTER = [
    "quicksort pivots again. clinical.",
    "bubble sort is doing its best and that is genuinely all it can do.",
    "insertion sort is walking each element home, one at a time.",
    "sleep sort has not moved. sleep sort is not asleep at the wheel, it IS the wheel.",
    "the pit wall says O(n log n) and the pit wall is never wrong.",
    "you have to feel for bubble sort. n² is not a strategy, it's a diagnosis.",
    "sleep sort's smallest element is stirring.",
]


class Commentary:
    """Two men who have called this race many times and are still surprised."""

    def __init__(self, write) -> None:
        self.write = write
        self.last = 0.0
        self.spoken: set[str] = set()

    def say(self, who: str, line: str) -> None:
        colour = "#ffd60a" if who is CHIP else "#4cc9f0"
        self.write(f"[{DIM}]🎙 [/][b {colour}]{who}[/][{DIM}]:[/] [{GHOST}]{line}[/]")

    def once(self, key: str, who: str, line: str) -> None:
        if key not in self.spoken:
            self.spoken.add(key)
            self.say(who, line)


# ───────────────────────────── winner overlay ───────────────────────────────
class Flash(Static):
    def on_mount(self) -> None:
        self.display = False

    def fire(self, headline: str, sub: str, colour: str) -> None:
        body = headline
        if Figlet is not None:
            for font in ("ansi_shadow", "big", "standard"):
                try:
                    body = Figlet(font=font, width=220).renderText(headline).rstrip("\n")
                    break
                except Exception:
                    continue
        t = Text(body + "\n", style=Style(color=colour, bold=True), justify="center")
        t.append(sub, Style(color=GHOST, italic=True))
        self.update(t)
        self.display = True
        self.set_timer(2.6, self._hide)

    def _hide(self) -> None:
        self.display = False


# ───────────────────────────── the app ──────────────────────────────────────
class GrandPrix(App):
    TITLE = "sorting grand prix :: bogosort believes"

    CSS = """
    Screen { layers: base overlay; background: #0d1b2a; color: #e8f1f8; }

    #banner { height: auto; content-align: center middle; text-align: center; }

    #track-pane {
        height: auto;
        border: round #2d5f7f;
        border-title-color: #ffd60a;
        border-title-align: center;
        padding: 0 1;
    }
    Track { height: auto; }

    #booth {
        height: 1fr;
        border: round #2d5f7f;
        border-title-color: #ffd60a;
        border-title-align: center;
        background: #0a1622;
        scrollbar-color: #2d5f7f;
        scrollbar-background: #0a1622;
    }

    #status { dock: bottom; height: 1; background: #16324a; color: #ffd60a; padding: 0 1; }

    #flash {
        layer: overlay; width: 100%; height: 100%;
        background: #0d1b2a 88%;
        content-align: center middle; text-align: center;
    }
    """

    BINDINGS = [
        ("q", "quit", "leave"),
        ("space", "pause", "pause"),
        ("r", "restart", "restart"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.paused = False
        self.race_no = 0
        self._reset()

    def _reset(self) -> None:
        self.race_no += 1
        self.values = list(range(1, N + 1))
        random.shuffle(self.values)
        self.racers = [Racer(n, c, g, o, f, self.values)
                       for n, c, g, o, f in FIELD]
        self.started = time.time()
        self.finish_order: list[Racer] = []
        self.last_order: list[str] = []
        self.chatter_at = 0.0

    def compose(self) -> ComposeResult:
        yield Static(self._banner(), id="banner")
        with Container(id="track-pane") as tp:
            tp.border_title = "// THE GRID  ·  bars are the live array  ·  green is home"
            yield Track(self)
        booth = RichLog(highlight=False, markup=True, wrap=True, min_width=12,
                        max_lines=500, auto_scroll=True, id="booth")
        booth.border_title = "// THE COMMENTARY BOX"
        yield booth
        yield Static("", id="status")
        yield Flash(id="flash")

    def on_mount(self) -> None:
        self.booth = self.query_one("#booth", RichLog)
        self.track = self.query_one(Track)
        self.comms = Commentary(self.booth.write)
        self._grid_walk()
        self.set_interval(TICK, self._tick)
        self.set_interval(0.5, self._status)

    def _banner(self) -> Text:
        block = "GRAND PRIX"
        if Figlet is not None:
            for font in ("standard", "small"):
                try:
                    block = Figlet(font=font, width=200).renderText("grand prix").rstrip("\n")
                    break
                except Exception:
                    continue
        grad = [GOLD, "#ffe566", "#4cc9f0", "#ffe566", GOLD]
        t = Text(justify="center")
        for i, line in enumerate(block.split("\n")):
            t.append(line + "\n", Style(color=grad[i % len(grad)], bold=True))
        t.append("[ ", Style(color=DIM))
        t.append("sorting", Style(color=GHOST, bold=True))
        t.append(" · ", Style(color=DIM))
        t.append("no handicaps", Style(color=GREEN, italic=True))
        t.append(" · ", Style(color=DIM))
        t.append("bogosort believes", Style(color=GOLD, italic=True))
        t.append(" ]", Style(color=DIM))
        return t

    # ----- race control -----
    def _grid_walk(self) -> None:
        self.booth.write(f"[{DIM}]{'─' * 58}[/]")
        self.booth.write(f"[b {GOLD}]RACE {self.race_no}[/] [{DIM}]· {N} elements · "
                         f"{OPS_PER_TICK} operations per racer per tick · no handicaps[/]")
        for r in self.racers:
            self.booth.write(f"  [{r.colour}]{r.name:<15}[/][{DIM}]{r.form:>12}   "
                             f"{self.quoted(r.odds)}[/]")
        self.booth.write(f"[{DIM}]{'─' * 58}[/]")
        for who, line in OPENERS:
            self.comms.say(who, line)

    def standings(self) -> list[Racer]:
        return sorted(
            self.racers,
            key=lambda r: (r.place if r.place is not None else 99, -r.progress),
        )

    @staticmethod
    def quoted(odds: float) -> str:
        if odds == float("inf"):
            return "∞"
        if odds >= 1e6:
            return f"{odds/1e6:.0f}M"
        return f"{odds:.1f}"

    def live_odds(self, r: Racer) -> str:
        """Shortening as they close on the line, drifting as they fall away."""
        if r.done:
            return "—"
        if r.odds == float("inf") or r.odds >= 1e6:
            return self.quoted(r.odds)
        gap = max(0.02, 1.0 - r.progress)
        return f"{max(1.01, r.odds * gap * 2.2):.2f}"

    def _tick(self) -> None:
        if self.paused:
            return
        for r in self.racers:
            was_done = r.done
            r.step(OPS_PER_TICK)
            if r.done and not was_done:
                r.place = len(self.finish_order) + 1
                self.finish_order.append(r)
                self._on_finish(r)
        self.track.refresh()
        self._colour_commentary()

    def _on_finish(self, r: Racer) -> None:
        secs = r.finished_at - self.started
        if r.name == "STALIN SORT":
            self.comms.say(DEL, random.choice(STALIN_LINES).format(removed=r.removed))
            self.booth.write(f"[b {r.colour}]  P{r.place}  {r.name}[/] "
                             f"[{DIM}]{secs:5.1f}s · {r.ops} ops · "
                             f"{r.removed} elements did not make it[/]")
        else:
            self.comms.say(CHIP, f"{r.name.lower()} takes P{r.place}, "
                                 f"{secs:.1f} seconds, {r.ops} operations.")
            self.booth.write(f"[b {r.colour}]  P{r.place}  {r.name}[/] "
                             f"[{DIM}]{secs:5.1f}s · {r.ops} ops[/]")
        if r.place == 1:
            self.query_one("#flash", Flash).fire(
                r.name.split()[0], f"wins race {self.race_no} in {secs:.1f}s "
                                   f"· {r.ops} operations", r.colour)

    def _colour_commentary(self) -> None:
        now = time.time()
        if now - self.chatter_at < 3.4:
            return
        self.chatter_at = now
        bogo = next((r for r in self.racers if r.name == "BOGOSORT"), None)
        miracle = next((r for r in self.racers if r.name == "MIRACLE SORT"), None)
        roll = random.random()
        if bogo and not bogo.done and roll < 0.42:
            self.comms.say(DEL, random.choice(BOGO_LINES).format(ops=bogo.ops))
        elif miracle and not miracle.done and roll < 0.62:
            self.comms.say(CHIP, random.choice(MIRACLE_LINES).format(ops=miracle.ops))
        else:
            self.comms.say(random.choice((CHIP, DEL)), random.choice(CHATTER))

        # someone has been overtaken, and the booth has noticed
        order = [r.name for r in self.standings() if not r.done]
        if self.last_order and order[:3] != self.last_order[:3] and len(order) > 1:
            leader = order[0]
            if leader != self.last_order[0]:
                self.comms.say(CHIP, f"{leader.lower()} takes the lead!")
        self.last_order = order

    # ----- actions -----
    def action_pause(self) -> None:
        self.paused = not self.paused
        self.comms.say(DEL, "red flag. everyone hold." if self.paused
                       else "and we go green again.")

    def action_restart(self) -> None:
        self._reset()
        self.comms.spoken.clear()
        self._grid_walk()
        self.track.refresh()

    # ----- status -----
    def _status(self) -> None:
        el = time.time() - self.started
        running = [r for r in self.racers if not r.done]
        total = sum(r.ops for r in self.racers)
        leader = self.standings()[0]
        t = Text()
        t.append(f" {el:6.1f}s ", Style(color=GOLD, bold=True))
        t.append("│ leader ", Style(color=DIM))
        t.append(f"{leader.name}", Style(color=leader.colour, bold=True))
        t.append(" │ still running ", Style(color=DIM))
        t.append(f"{len(running)}", Style(color=GHOST, bold=True))
        t.append(" │ total ops ", Style(color=DIM))
        t.append(f"{total:,}", Style(color=GHOST))
        if self.paused:
            t.append("  RED FLAG", Style(color=RED, bold=True))
        t.append("  │ [space] pause  [r] restart  [q] leave ", Style(color=DIM))
        self.query_one("#status", Static).update(t)


if __name__ == "__main__":
    GrandPrix().run()
