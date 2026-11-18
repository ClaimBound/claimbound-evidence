#!/usr/bin/env python3
"""Screenshots and a tour GIF of the published atlas in examples/selective_disclosure/public/atlas.html.

Uses a locally installed Chrome (headless) and Pillow, neither of which Protocolith needs:

    uv run --no-project --with pillow python scripts/build_atlas_screens.py [--chrome PATH]

Writes docs/assets/protocolith/atlas-overview.png, atlas-full.png, atlas-summary.png, atlas-hidden.png and atlas-tour.gif.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
PAGE = ROOT / "examples" / "selective_disclosure" / "public" / "atlas.html"
ASSETS = ROOT / "docs" / "assets" / "protocolith"
CHROME = (
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "google-chrome",
    "chromium",
    "chrome",
)


def find_chrome(explicit: str | None) -> str:
    for candidate in ((explicit,) if explicit else CHROME):
        if candidate and (Path(candidate).exists() or shutil.which(candidate)):
            return candidate
    raise SystemExit("no Chrome or Chromium found; pass --chrome PATH")


def row_ids() -> dict[str, str]:
    text = PAGE.read_text(encoding="utf-8")
    start = text.index(">", text.index('id="atlas-data"')) + 1
    rows = json.loads(text[start : text.index("</script>", start)].replace("\\u003c", "<"))["rows"]
    ids = [row[0] for row in rows]
    return {
        "full": next(i for i in ids if i.startswith("PLITH-")),
        "summary": next(i for i in ids if i.startswith("LEDGER-RECORD-")),
        "hidden": next(i for i in ids if i.startswith("HIDDEN-")),
    }


def shoot(chrome: str, fragment: str, out: Path) -> None:
    url = PAGE.as_uri() + (f"#{fragment}" if fragment else "")
    subprocess.run(
        [chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--window-size=1280,900", "--virtual-time-budget=3000", f"--screenshot={out}", url],
        check=True, capture_output=True, timeout=90,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--chrome", default=None)
    args = parser.parse_args()
    chrome = find_chrome(args.chrome)
    ids = row_ids()
    shots = {"overview": "", **ids}
    for name, fragment in shots.items():
        shoot(chrome, fragment, ASSETS / f"atlas-{name}.png")
        print("wrote", ASSETS / f"atlas-{name}.png", flush=True)
    frames = [Image.open(ASSETS / f"atlas-{name}.png").convert("RGB").resize((960, 675), Image.Resampling.LANCZOS) for name in shots]
    palette = frames[0].quantize(colors=128, method=Image.Quantize.MEDIANCUT)
    quantized = [f.quantize(palette=palette, dither=Image.Dither.NONE) for f in frames]
    out = ASSETS / "atlas-tour.gif"
    quantized[0].save(out, save_all=True, append_images=quantized[1:], duration=[3200, 3200, 3200, 3600], loop=0, optimize=True)
    print(f"wrote {out} bytes={out.stat().st_size}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
