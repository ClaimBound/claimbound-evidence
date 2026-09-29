# SPDX-License-Identifier: Apache-2.0
"""Render docs/assets/demo/quickstart.gif from a real run of the installed CLI.

The commands below are executed for real; their output is captured and drawn as a
terminal recording. The only edit is display wrapping and replacing the temporary
working directory with ``.``.

Usage: python make_demo.py --claimbound /path/to/claimbound --card /path/to/card.json
Requires Pillow. Font: Menlo on macOS, DejaVu Sans Mono elsewhere.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import tempfile
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

COMMANDS = (
    "claimbound validate-card card.json",
    "claimbound inspect card card.json --keys evidence_id result_status reproduction_level",
    "claimbound validate-all",
)
FONT_CANDIDATES = (
    "/System/Library/Fonts/Menlo.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
)
WIDTH, HEIGHT, PAD, FONT_SIZE, LINE = 1000, 430, 22, 15, 21
WRAP = 104
BG, BAR, FG, PROMPT, DIM = "#0d1117", "#161b22", "#e6edf3", "#3fb950", "#8b949e"


def run_commands(claimbound: Path, card: Path) -> list[tuple[str, list[str]]]:
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        shutil.copy(card, work / "card.json")
        results = []
        for command in COMMANDS:
            argv = [str(claimbound), *command.split()[1:]]
            proc = subprocess.run(argv, cwd=work, capture_output=True, text=True, check=False)
            text = (proc.stdout + proc.stderr).replace(str(work.resolve()), ".").replace(str(work), ".")
            lines: list[str] = []
            for raw in text.rstrip("\n").splitlines():
                lines.extend(textwrap.wrap(raw, WRAP, subsequent_indent="  ") or [""])
            results.append((command, lines))
        return results


def load_font() -> ImageFont.FreeTypeFont:
    for candidate in FONT_CANDIDATES:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, FONT_SIZE)
    raise SystemExit("no monospace font found")


def draw_frame(font, lines: list[tuple[str, str]], cursor: bool) -> Image.Image:
    img = Image.new("RGB", (WIDTH, HEIGHT), BG)
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, WIDTH, 34), fill=BAR)
    for i, colour in enumerate(("#ff5f56", "#ffbd2e", "#27c93f")):
        d.ellipse((16 + i * 22, 11, 28 + i * 22, 23), fill=colour)
    d.text((WIDTH // 2, 17), "claimbound-evidence", font=font, fill=DIM, anchor="mm")
    visible = lines[-((HEIGHT - 34 - 2 * PAD) // LINE):]
    y = 34 + PAD
    for kind, text in visible:
        if kind == "cmd":
            d.text((PAD, y), "$ ", font=font, fill=PROMPT)
            d.text((PAD + font.getlength("$ "), y), text, font=font, fill=FG)
        else:
            d.text((PAD, y), text, font=font, fill=FG if kind == "out" else DIM)
        y += LINE
    if cursor:
        last_kind, last_text = visible[-1] if visible else ("cmd", "")
        x = PAD + font.getlength(("$ " if last_kind == "cmd" else "") + last_text)
        d.rectangle((x, y - LINE + 2, x + 9, y - 4), fill=FG)
    return img


def build(results, out: Path) -> None:
    font = load_font()
    frames: list[Image.Image] = []
    durations: list[int] = []
    shown: list[tuple[str, str]] = []

    def add(cursor: bool, ms: int) -> None:
        frames.append(draw_frame(font, shown, cursor))
        durations.append(ms)

    for command, output in results:
        shown.append(("cmd", ""))
        add(True, 350)
        for end in range(3, len(command) + 3, 3):
            shown[-1] = ("cmd", command[:end])
            add(True, 70)
        shown[-1] = ("cmd", command)
        add(True, 300)
        for line in output:
            shown.append(("out", line))
        add(False, 1900)
    shown.append(("cmd", ""))
    add(True, 1500)
    first = frames[0].quantize(colors=32, method=Image.Quantize.MEDIANCUT)
    rest = [f.quantize(palette=first) for f in frames[1:]]
    first.save(out, save_all=True, append_images=rest, duration=durations, loop=0, optimize=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--claimbound", type=Path, required=True)
    parser.add_argument("--card", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=Path(__file__).with_name("quickstart.gif"))
    args = parser.parse_args()
    build(run_commands(args.claimbound, args.card), args.out)


if __name__ == "__main__":
    main()
