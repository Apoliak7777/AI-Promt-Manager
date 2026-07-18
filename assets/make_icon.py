"""Vygeneruje ``assets/icon.ico`` — fialový motív (bublina + neurónová sieť).

Spusti: ``python assets/make_icon.py``
Nepotrebuje žiadne externé fonty; kreslí čisto geometricky (PIL).
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

ACCENT_TOP = (140, 108, 255)   # #8C6CFF
ACCENT_BOT = (108, 73, 232)    # #6C49E8
WHITE = (255, 255, 255, 255)
NODE = (124, 92, 252, 255)     # #7C5CFC

SIZE = 256


def _gradient(size: int) -> Image.Image:
    img = Image.new("RGB", (size, size), ACCENT_TOP)
    draw = ImageDraw.Draw(img)
    for y in range(size):
        t = y / max(1, size - 1)
        r = int(ACCENT_TOP[0] + (ACCENT_BOT[0] - ACCENT_TOP[0]) * t)
        g = int(ACCENT_TOP[1] + (ACCENT_BOT[1] - ACCENT_TOP[1]) * t)
        b = int(ACCENT_TOP[2] + (ACCENT_BOT[2] - ACCENT_TOP[2]) * t)
        draw.line([(0, y), (size, y)], fill=(r, g, b))
    return img


def _rounded_mask(size: int, radius: int) -> Image.Image:
    mask = Image.new("L", (size, size), 0)
    d = ImageDraw.Draw(mask)
    d.rounded_rectangle([0, 0, size - 1, size - 1], radius=radius, fill=255)
    return mask


def build() -> Path:
    base = _gradient(SIZE).convert("RGBA")
    base.putalpha(_rounded_mask(SIZE, radius=52))

    draw = ImageDraw.Draw(base)

    # Rečová bublina
    bx0, by0, bx1, by1 = 44, 40, 212, 176
    draw.rounded_rectangle([bx0, by0, bx1, by1], radius=34, fill=WHITE)
    # Chvostík bubliny (ľavý dolný)
    draw.polygon([(78, by1 - 4), (78, by1 + 40), (118, by1 - 4)], fill=WHITE)

    # Neurónová sieť (uzly + spoje) vnútri bubliny
    nodes = [
        (86, 78), (150, 66), (186, 104),
        (104, 118), (150, 138), (176, 150),
        (128, 92),
    ]
    edges = [
        (0, 6), (6, 1), (1, 2), (6, 3), (3, 4),
        (4, 5), (6, 4), (2, 5), (0, 3),
    ]
    for a, b in edges:
        draw.line([nodes[a], nodes[b]], fill=(124, 92, 252, 150), width=4)
    for i, (x, y) in enumerate(nodes):
        r = 11 if i == 6 else 8
        draw.ellipse([x - r, y - r, x + r, y + r], fill=NODE,
                     outline=WHITE, width=2)

    out = Path(__file__).resolve().parent / "icon.ico"
    sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    base.save(out, format="ICO", sizes=sizes)
    return out


if __name__ == "__main__":
    path = build()
    print(f"Ikona vytvorená: {path}")
