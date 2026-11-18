#!/usr/bin/env python3
"""Build docs/assets/protocolith/demo.gif from a real run of the ledger commands.

The script copies examples/quickstart to a temporary directory, runs the real commands
(init, freeze, record, verify-ledger, summary, issue, atlas), then edits one word of the ledger
and verifies again to show that tampering is detected. The terminal output in the frames is
the captured output of those commands; only long hexadecimal strings (40 characters or more)
are shortened to their first 12 characters followed by "..." so that lines fit the frame.

Pillow is needed only here, not by Protocolith:

    uv run --no-project --with pillow python scripts/build_demo_gif.py [--scenario ledger|anchor|disclose|story] [--out FILE]

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


def anchor_script(work: Path) -> list[tuple[str, list[str], int]]:
    """Freeze, record, anchor, then cut the last entry off: plain verification passes, the anchor catches it."""
    steps: list[tuple[str, list[str], int]] = []

    def step(shown: str, argv: list[str]) -> None:
        out, code = run(argv, work)
        steps.append((shown, out, code))

    step("protocolith init", ["init"])
    step("protocolith freeze protocol.json", ["freeze", "protocol.json"])
    step("protocolith record record.json", ["record", "record.json"])
    step("protocolith anchor --write-head head.txt", ["anchor", "--write-head", "head.txt"])
    ledger = work / ".protocolith" / "ledger.jsonl"
    lines = ledger.read_text(encoding="utf-8").splitlines(keepends=True)
    ledger.write_text("".join(lines[:-1]), encoding="utf-8")
    steps.append(("head -n 1 ledger.jsonl > tmp && mv tmp ledger.jsonl   # drop the last entry", [], 0))
    step("protocolith verify-ledger", ["verify-ledger"])
    step("protocolith verify-ledger --anchors", ["verify-ledger", "--anchors"])
    return steps


def disclose_script(work: Path) -> list[tuple[str, list[str], int]]:
    """A private notebook, a policy, the published view, a reveal, and an edit that is caught."""
    import json

    sys.path.insert(0, str(ROOT / "scripts"))
    from build_disclosure_demo import OUT, build_private
    from protocolith.core import Store, entries

    steps: list[tuple[str, list[str], int]] = []

    def step(shown: str, argv: list[str]) -> None:
        out, code = run(argv, work)
        steps.append((shown, out, code))

    build_private(Store(work / ".protocolith"))
    shutil.copy(OUT / "policy.json", work / "policy.json")
    ledger = entries(Store(work / ".protocolith"))
    revealed = next(e for e in ledger if e["type"] == "record" and e["body"]["run_id"] == "run-03" and 13 < e["seq"] < 22)
    (work / "entry.json").write_text(json.dumps(revealed), encoding="utf-8")
    step("protocolith summary | head -n 3", ["summary"])
    steps[-1] = (steps[-1][0], steps[-1][1][:3], 0)
    step("protocolith disclose --policy policy.json --out public.jsonl", ["disclose", "--policy", "policy.json", "--out", "public.jsonl"])
    lines = (work / "public.jsonl").read_text(encoding="utf-8").splitlines()
    steps.append(("head -n 3 public.jsonl", [short(line) for line in lines[:3]], 0))
    step("protocolith verify-disclosure public.jsonl", ["verify-disclosure", "public.jsonl"])
    step("protocolith verify-disclosure public.jsonl --reveal entry.json", ["verify-disclosure", "public.jsonl", "--reveal", "entry.json"])
    (work / "public.jsonl").write_text("\n".join(lines[:16] + lines[17:]) + "\n", encoding="utf-8")
    steps.append(("# someone drops one hidden entry from the published file", [], 0))
    step("protocolith verify-disclosure public.jsonl", ["verify-disclosure", "public.jsonl"])
    return steps


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


def frame(font: ImageFont.FreeTypeFont, rows: list[tuple[str, tuple[int, int, int]]], cursor: bool, caption: str = "") -> Image.Image:
    img = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(img)
    draw.rectangle((0, 0, WIDTH, 30), fill=BAR)
    for i, colr in enumerate(((240, 110, 110), (232, 176, 74), (110, 200, 140))):
        draw.ellipse((14 + i * 20, 9, 26 + i * 20, 21), fill=colr)
    draw.text((WIDTH // 2 - 60, 7), f"protocolith {VERSION}", font=font, fill=DIM)
    top = TOP + (30 if caption else 0)
    if caption:
        draw.rectangle((0, 30, WIDTH, 64), fill=(32, 44, 58))
        draw.text((PAD, 38), caption, font=font, fill=PROMPT)
    visible = (HEIGHT - top - PAD) // LINE_H
    y = top
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


def card(lines: list[tuple[str, int, tuple[int, int, int]]]) -> Image.Image:
    """A title card: centred lines of (text, size, colour)."""
    img = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(img)
    fonts = {}
    total = sum(size + 18 for _, size, _ in lines)
    y = (HEIGHT - total) // 2
    for text, size, colour in lines:
        if size not in fonts:
            fonts[size] = ImageFont.truetype(next(p for p in FONT_CANDIDATES if Path(p).exists()), size)
        w = draw.textlength(text, font=fonts[size])
        draw.text(((WIDTH - w) / 2, y), text, font=fonts[size], fill=colour)
        y += size + 18
    return img


def story_chapters(work: Path, notebook: Path) -> list[tuple[str, list[tuple[str, list[str], int]]]]:
    """Real runs, grouped in chapters with a one-line caption each."""
    import shutil as _sh

    sys.path.insert(0, str(ROOT / "scripts"))
    from build_disclosure_demo import OUT, build_private
    from protocolith.core import Store, entries

    def runs(cwd: Path, items: list[tuple[str, list[str]]]) -> list[tuple[str, list[str], int]]:
        steps = []
        for shown, argv in items:
            out, code = run(argv, cwd)
            steps.append((shown, out, code))
        return steps

    ledger = work / ".protocolith" / "ledger.jsonl"
    chapters: list[tuple[str, list[tuple[str, list[str], int]]]] = []
    chapters.append(("1  Freeze the protocol BEFORE you run anything", runs(work, [("protocolith init", ["init"]), ("protocolith freeze protocol.json", ["freeze", "protocol.json"])])))
    chapters.append(("2  Record the result, failures included", runs(work, [("protocolith record record.json", ["record", "record.json"]), ("protocolith verify-ledger", ["verify-ledger"])])))
    backup = ledger.read_bytes()
    ledger.write_text(ledger.read_text(encoding="utf-8").replace("PASSED_UNDER_PROTOCOL", "FAILED_UNDER_PROTOCOL", 1), encoding="utf-8")
    edited = runs(work, [("protocolith verify-ledger", ["verify-ledger"])])
    ledger.write_bytes(backup)
    chapters.append(("3  The history is a hash chain: edit one word and it breaks", [("sed -i 's/PASSED/FAILED/' .protocolith/ledger.jsonl", [], 0), *edited]))
    anchored = runs(work, [("protocolith anchor --write-head head.txt", ["anchor", "--write-head", "head.txt"])])
    lines = backup.decode("utf-8").splitlines(keepends=True)
    ledger.write_text("".join(lines[:-1]), encoding="utf-8")
    cut = runs(work, [("protocolith verify-ledger", ["verify-ledger"]), ("protocolith verify-ledger --anchors", ["verify-ledger", "--anchors"])])
    ledger.write_bytes(backup)
    chapters.append(("4  Anchor the head outside your disk: cutting entries is caught", [*anchored, ("head -n 1 ledger.jsonl > tmp && mv tmp ledger.jsonl   # drop the last entry", [], 0), *cut]))
    build_private(Store(notebook / ".protocolith"))
    _sh.copy(OUT / "policy.json", notebook / "policy.json")
    revealed = next(e for e in entries(Store(notebook / ".protocolith")) if e["type"] == "record" and e["body"]["run_id"] == "run-03" and 13 < e["seq"] < 22)
    (notebook / "entry.json").write_text(__import__("json").dumps(revealed), encoding="utf-8")
    pub = runs(notebook, [("protocolith disclose --policy policy.json --out public.jsonl", ["disclose", "--policy", "policy.json", "--out", "public.jsonl"]), ("protocolith verify-disclosure public.jsonl", ["verify-disclosure", "public.jsonl"]), ("protocolith verify-disclosure public.jsonl --reveal entry.json", ["verify-disclosure", "public.jsonl", "--reveal", "entry.json"])])
    chapters.append(("5  Publish only what you choose; the chain proves nothing was dropped", pub))
    return chapters


def build_story(chapters: list[tuple[str, list[tuple[str, list[str], int]]]], font: ImageFont.FreeTypeFont) -> tuple[list[Image.Image], list[int]]:
    frames: list[Image.Image] = []
    delays: list[int] = []
    white, amber, grey = TEXT, PROMPT, DIM
    for img, delay in (
        (card([("Protocolith", 48, white), ("Freeze the protocol. Record the result.", 22, amber), ("Verify the history.", 22, amber)]), 2600),
        (card([("A result is easy to believe", 24, white), ("and hard to check when", 24, white), ("the protocol was written after the run,", 20, grey), ("the history was edited,", 20, grey), ("or a failed run quietly disappeared.", 20, grey)]), 4200),
    ):
        frames.append(img)
        delays.append(delay)
    for caption, steps in chapters:
        rows: list[tuple[str, tuple[int, int, int]]] = []

        def add(delay: int, cursor: bool = False) -> None:
            img = frame(font, rows, cursor, caption)
            if frames and list(img.getdata()) == list(frames[-1].getdata()):
                delays[-1] += delay
                return
            frames.append(img)
            delays.append(delay)

        add(900)
        for index, (shown, out, code) in enumerate(steps):
            for n in range(0, len(shown) + 1, 4):
                rows.append(("$ " + shown[:n], TEXT))
                add(35, cursor=True)
                rows.pop()
            rows.append(("$ " + shown, TEXT))
            add(300)
            for line in out:
                rows.append((line if len(line) <= 90 else line[:87] + "...", colour(line, code)))
                add(60)
            if code != 0:
                rows.append((f"exit code {code}", BAD))
            add(1500 if index == len(steps) - 1 else 900)
        add(1200)
    frames.append(card([("pip install protocolith", 30, amber), ("No dependencies. Runs offline. For people and AI agents.", 18, white), ("protocolith.github.io", 22, white), ("github.com/Protocolith/protocolith", 18, grey)]))
    delays.append(5200)
    return frames, delays


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--out", default=None)
    parser.add_argument("--scenario", choices=("ledger", "anchor", "disclose", "story"), default="ledger")
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
        if args.scenario == "story":
            notebook = Path(tmp) / "notebook"
            notebook.mkdir()
            frames, delays = build_story(story_chapters(work, notebook), font)
        else:
            steps = {"anchor": anchor_script, "disclose": disclose_script}.get(args.scenario, script)(work)
            frames, delays = build(steps, font)
    sample = frames[:: max(1, len(frames) // 6)][:6]
    mosaic = Image.new("RGB", (WIDTH, HEIGHT * len(sample)))
    for number, shot in enumerate(sample):
        mosaic.paste(shot, (0, number * HEIGHT))
    palette = mosaic.quantize(colors=64, method=Image.Quantize.MEDIANCUT)
    quantized = [f.quantize(palette=palette, dither=Image.Dither.NONE) for f in frames]
    default_name = {"anchor": "anchor-demo.gif", "disclose": "disclosure-demo.gif", "story": "protocolith-story.gif"}.get(args.scenario, "demo.gif")
    out = Path(args.out) if args.out else ROOT / "docs" / "assets" / "protocolith" / default_name
    quantized[0].save(out, save_all=True, append_images=quantized[1:], duration=delays, loop=0, optimize=True, disposal=1)
    print(f"wrote {out} frames={len(frames)} bytes={out.stat().st_size}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
