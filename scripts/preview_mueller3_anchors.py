"""Draw crosshairs at every mueller3 anchor pixel onto the bundled template.

Run after editing templates/mueller3_anchors.json to verify the anchor
coordinates land on the correct landmarks of the M&S diagram. Outputs
mueller3_anchors_preview.png in the project root.

Usage: python scripts/preview_mueller3_anchors.py
"""
from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = ROOT / "templates"
OUT_PATH = ROOT / "mueller3_anchors_preview.png"


def main() -> None:
    cfg = json.load(open(TEMPLATES / "mueller3_anchors.json", encoding="utf-8"))
    img = Image.open(TEMPLATES / cfg["image"]).convert("RGB")
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 18)
    except OSError:
        font = ImageFont.load_default()

    palette = {
        "front": (220, 30, 30),
        "back":  (30, 80, 220),
    }
    for section in ("front", "back"):
        color = palette[section]
        roi = cfg[section]["roi_px"]
        draw.rectangle(roi, outline=color, width=3)
        for name, (x, y) in cfg[section]["anchors_px"].items():
            r = 14
            draw.ellipse([x - r, y - r, x + r, y + r], outline=color, width=3)
            draw.line([x - r - 4, y, x + r + 4, y], fill=color, width=2)
            draw.line([x, y - r - 4, x, y + r + 4], fill=color, width=2)
            draw.text((x + r + 6, y - 12), name, fill=color, font=font)

    img.save(OUT_PATH)
    print(f"saved {OUT_PATH}")


if __name__ == "__main__":
    main()
