#!/usr/bin/env python3
"""Build docs/assets/protocolith/demo.gif from a real run of the ledger commands.

The script copies examples/quickstart to a temporary directory, runs the real commands
(init, freeze, record, verify-ledger, summary, issue, atlas), then edits one word of the ledger
and verifies again to show that tampering is detected. The terminal output in the frames is
the captured output of those commands; only long hexadecimal strings (40 characters or more)
are shortened to their first 12 characters followed by "..." so that lines fit the frame.

Pillow is needed only here, not by Protocolith:

    uv run --no-project --with pillow python scripts/build_demo_gif.py [--out FILE]

Standard output shows the progress in percent. The frames contain the current date (it is part of the card ids).
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
WIDTH, HEIGHT = 820, 500
PAD, TOP = 18, 44
FONT_SIZE = 15
LINE_H = 20
BG, BAR, TEXT = (14, 20, 27), (24, 33, 44), (238, 242, 246)
PROMPT, OK, BAD, DIM = (232, 176, 74), (110, 200, 140), (240, 110, 110), (140, 156, 176)
FONT_CANDIDATES = (
    "/System/Library/Fonts/Menlo.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    "C:/Windows/Fonts/consola.ttf",
)
HEX = re.compile(r"[0-9a-f]{40,}")
VERSION = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]
RUNNER = "import sys; from protocolith.cli import main; sys.exit(main())"


def short(text: str) -> str:
    return HEX.sub(lambda m: m.group(0)[:12] + "...", text)


def run(argv: list[str], cwd: Path) -> tuple[list[str], int]:
    env = dict(os.environ, PYTHONPATH=str(ROOT / "src"), PYTHONIOENCODING="utf-8")
    proc = subprocess.run(
        [sys.executable, "-c", RUNNER, *argv], cwd=cwd, env=env, capture_output=True, text=True, check=False
    )
    lines = (proc.stdout + proc.stderr).rstrip("\n").splitlines()
    return [short(line) for line in lines], proc.returncode


def script(work: Path) -> list[tuple[str, list[str], int]]:
    """Run every step for real and return (shown command, output lines, exit code)."""
    steps: list[tuple[str, list[str], int]] = []

    def step(shown: str, argv: list[str]) -> None:
        out, code = run(argv, work)
        steps.append((shown, out, code))

    step("protocolith --version", ["--version"])
    step("protocolith init", ["init"])
    step("protocolith freeze protocol.json", ["freeze", "protocol.json"])
    step("protocolith record record.json", ["record", "record.json"])
    step("protocolith verify-ledger", ["verify-ledger"])
    step("protocolith summary", ["summary"])
    step("protocolith issue 1", ["issue", "1"])
    step("protocolith atlas --store .protocolith --out atlas.html", ["atlas", "--store", ".protocolith", "--out", "atlas.html"])
    ledger = work / ".protocolith" / "ledger.jsonl"
    ledger.write_text(ledger.read_text(encoding="utf-8").replace("PASSED_UNDER_PROTOCOL", "FAILED_UNDER_PROTOCOL", 1), encoding="utf-8")
    steps.append(("sed -i 's/PASSED/FAILED/' .protocolith/ledger.jsonl   # tamper", [], 0))
    step("protocolith verify-ledger", ["verify-ledger"])
    return steps


def load_font() -> ImageFont.FreeTypeFont:
    for path in FONT_CANDIDATES:
        if Path(path).exists():
            return ImageFont.truetype(path, FONT_SIZE)
    raise SystemExit("no monospace font found; pass a path with --font")


def colour(line: str, code: int) -> tuple[int, int, int]:
    if line.startswith("$"):
        return TEXT
    if code != 0:
        return BAD
    if line.startswith(("OK", "wrote", "frozen", "recorded", "issued", "ledger OK")):
        return OK
    return TEXT


def frame(font: ImageFont.FreeTypeFont, rows: list[tuple[str, tuple[int, int, int]]], cursor: bool) -> Image.Image:
    img = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(img)
    draw.rectangle((0, 0, WIDTH, 30), fill=BAR)
    for i, colr in enumerate(((240, 110, 110), (232, 176, 74), (110, 200, 140))):
        draw.ellipse((14 + i * 20, 9, 26 + i * 20, 21), fill=colr)
    draw.text((WIDTH // 2 - 60, 7), f"protocolith {VERSION}", font=font, fill=DIM)
    visible = (HEIGHT - TOP - PAD) // LINE_H
    y = TOP
    for text, colr in rows[-visible:]:
        if text.startswith("$ "):
            draw.text((PAD, y), "$", font=font, fill=PROMPT)
            draw.text((PAD + 20, y), text[2:], font=font, fill=TEXT)
        else:
            draw.text((PAD, y), text, font=font, fill=colr)
        y += LINE_H
    if cursor:
        last = rows[-1][0] if rows else ""
        x = PAD + 20 + int(font.getlength(last[2:])) if last.startswith("$ ") else PAD
        draw.rectangle((x, y - LINE_H + 2, x + 9, y - 4), fill=TEXT)
    return img


def build(steps: list[tuple[str, list[str], int]], font: ImageFont.FreeTypeFont) -> tuple[list[Image.Image], list[int]]:
    frames: list[Image.Image] = []
    delays: list[int] = []
    rows: list[tuple[str, tuple[int, int, int]]] = []

    def add(delay: int, cursor: bool = False) -> None:
        img = frame(font, rows, cursor)
        if frames and list(img.getdata()) == list(frames[-1].getdata()):
            delays[-1] += delay
            return
        frames.append(img)
        delays.append(delay)

    for index, (shown, out, code) in enumerate(steps):
        for n in range(0, len(shown) + 1, 4):
            rows.append((("$ " + shown[:n]), TEXT))
            add(40, cursor=True)
            rows.pop()
        rows.append(("$ " + shown, TEXT))
        add(350)
        for line in out:
            rows.append((line if len(line) <= 90 else line[:87] + "...", colour(line, code)))
            add(70)
        if code != 0:
            rows.append((f"exit code {code}", BAD))
        add(1100 if index < len(steps) - 1 else 3200)
        print(f"progress {int(100 * (index + 1) / len(steps))}%", flush=True)
    return frames, delays


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--out", default=str(ROOT / "docs" / "assets" / "protocolith" / "demo.gif"))
    parser.add_argument("--font", default=None, help="path to a monospace font")
    args = parser.parse_args()
    if args.font:
        FONT_CANDIDATES_LOCAL = (args.font,)
        font = ImageFont.truetype(FONT_CANDIDATES_LOCAL[0], FONT_SIZE)
    else:
        font = load_font()
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        for name in ("protocol.json", "record.json", "results.txt"):
            shutil.copy(ROOT / "examples" / "quickstart" / name, work / name)
        steps = script(work)
    frames, delays = build(steps, font)
    palette = frames[0].quantize(colors=48, method=Image.Quantize.MEDIANCUT)
    quantized = [f.quantize(palette=palette, dither=Image.Dither.NONE) for f in frames]
    out = Path(args.out)
    quantized[0].save(out, save_all=True, append_images=quantized[1:], duration=delays, loop=0, optimize=True, disposal=1)
    print(f"wrote {out} frames={len(frames)} bytes={out.stat().st_size}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
