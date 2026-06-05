# HACK THE PLANET — a terminal extravaganza

A full-screen [Textual](https://textual.textualize.io) TUI that mashes up the
neon swagger of **Hackers (1995)**, the grounded terminal realism of
**Mr. Robot**, and the green digital rain of **The Matrix**.

![screenshot](hack.png)

## What's on screen

- **Banner** — a `HACK THE PLANET` figlet header in a green→cyan gradient.
- **MATRIX_RAIN** — half-width katakana cascading with bright leading drops,
  rendered through Textual's Line API so it stays smooth.
- **Live shell** — a scrolling exploit console that cycles through scripted
  scenes: `nmap` service scans, `hydra` brute force, a Metasploit/meterpreter
  session + `hashdump`, encrypted exfil, plus Matrix/Hackers easter eggs.
- **TARGET_ACQUISITION** — a kill list of nodes marching
  `SCANNING → PROBING → EXPLOIT → BREACHED → ROOTED`.
- **SYSTEM_BREACH** — self-animating neon gauges (DECRYPT / BRUTE / FIREWALL /
  UPLINK / TRACE) that fill, flash a verdict, and reset.
- **Status bar** — clock, a Tor-style routing hop chain, and a blinking cursor.

## Run it

```sh
source venv/bin/activate      # the virtualenv created in this directory
python hack.py
```

Or from scratch elsewhere:

```sh
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python hack.py
```

## Keys

| key     | action                                   |
|---------|------------------------------------------|
| `q`     | disconnect (quit)                        |
| `space` | full-screen `ACCESS GRANTED` flash       |
| `m`     | mute/unmute the Matrix rain              |

The dramatic flash also fires on its own every ~17 seconds. Best enjoyed
full-screen with the lights off. Hack responsibly — it's all theatre.
