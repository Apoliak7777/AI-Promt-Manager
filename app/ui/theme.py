"""Farebné tokeny a téma.

Väčšina CTk widgetov akceptuje tuple ``(light, dark)`` a sama prepína podľa
appearance mode. Pre widgety, ktoré tuple neprijímajú (``tk.Text``, ``Canvas``),
použi :func:`resolve`, ktorý vráti konkrétnu farbu pre aktuálny mód.
"""
from __future__ import annotations

import customtkinter as ctk

# --------------------------------------------------------------------------- #
# Tokeny  (light, dark)
# --------------------------------------------------------------------------- #
BG = ("#F5F5FA", "#1E1E2E")
BG_ELEVATED = ("#FFFFFF", "#252537")
SIDEBAR_BG = ("#ECECF4", "#181825")
TOPBAR_BG = ("#FBFBFE", "#22222F")

CARD = ("#FFFFFF", "#2A2B3D")
CARD_HOVER = ("#F0F0F8", "#33344B")
CARD_BORDER = ("#E4E4EE", "#3A3B52")

TEXT = ("#1B1B2A", "#E7E7F2")
TEXT_MUTED = ("#6A6A80", "#9C9CB4")
TEXT_FAINT = ("#9090A4", "#6E6E86")

INPUT_BG = ("#FFFFFF", "#232333")
INPUT_BORDER = ("#D6D6E4", "#3C3D55")
DIVIDER = ("#E4E4EE", "#33344B")

DANGER = "#E5484D"
DANGER_HOVER = "#C93C40"
SUCCESS = "#2FB86B"
WARNING = "#E0A800"

# Rozmery
RADIUS = 10
RADIUS_SM = 8
RADIUS_LG = 14

FONT_FAMILY = "Segoe UI"
MONO_FAMILY = "Consolas"

# --------------------------------------------------------------------------- #
# Akcentová farba (dynamická, uložená v nastaveniach)
# --------------------------------------------------------------------------- #
_accent = "#7C5CFC"


def set_accent(hex_color: str) -> None:
    global _accent
    if hex_color and hex_color.startswith("#"):
        _accent = hex_color


def get_accent() -> str:
    return _accent


def get_accent_hover() -> str:
    return shade(_accent, -0.14)


def get_accent_soft() -> tuple[str, str]:
    """Jemné akcentové pozadie (light, dark) — pre aktívne/hover stavy."""
    return (tint(_accent, 0.82), shade(_accent, -0.55))


# --------------------------------------------------------------------------- #
# Appearance mode
# --------------------------------------------------------------------------- #
def apply_appearance(mode: str) -> None:
    """mode: 'dark' | 'light' | 'system'."""
    mode = (mode or "dark").lower()
    if mode not in ("dark", "light", "system"):
        mode = "dark"
    ctk.set_appearance_mode(mode)


def current_mode() -> str:
    """Vráti 'Light' alebo 'Dark' (rozlíšené aj pri 'system')."""
    return ctk.get_appearance_mode()


def is_dark() -> bool:
    return current_mode().lower() == "dark"


def resolve(color) -> str:
    """Z tuple (light, dark) vyber farbu pre aktuálny mód; string vráti tak ako je."""
    if isinstance(color, (tuple, list)):
        return color[1] if is_dark() else color[0]
    return color


# --------------------------------------------------------------------------- #
# Fonty
# --------------------------------------------------------------------------- #
def font(size: int = 14, weight: str = "normal") -> ctk.CTkFont:
    return ctk.CTkFont(family=FONT_FAMILY, size=size, weight=weight)


def mono_font(size: int = 13) -> ctk.CTkFont:
    return ctk.CTkFont(family=MONO_FAMILY, size=size)


# --------------------------------------------------------------------------- #
# Farby pre markdown preview (rozlíšené na aktuálny mód)
# --------------------------------------------------------------------------- #
def markdown_colors() -> dict:
    return {
        "text": resolve(TEXT),
        "muted": resolve(TEXT_MUTED),
        "accent": _accent,
        "heading": resolve(TEXT),
        "code_fg": ("#D6336C" if not is_dark() else "#F0A5C0"),
        "code_bg": ("#F0F0F6" if not is_dark() else "#1B1B2A"),
    }


# --------------------------------------------------------------------------- #
# Farebné utility (hex)
# --------------------------------------------------------------------------- #
def _hex_to_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    return "#{:02X}{:02X}{:02X}".format(*(max(0, min(255, int(c))) for c in rgb))


def shade(hex_color: str, amount: float) -> str:
    """amount<0 stmaví, amount>0 zosvetlí (o daný podiel k čiernej/bielej)."""
    r, g, b = _hex_to_rgb(hex_color)
    if amount < 0:
        f = 1 + amount
        return _rgb_to_hex((r * f, g * f, b * f))
    return _rgb_to_hex((r + (255 - r) * amount,
                        g + (255 - g) * amount,
                        b + (255 - b) * amount))


def tint(hex_color: str, amount: float) -> str:
    """Zmieša farbu s bielou (amount 0..1)."""
    r, g, b = _hex_to_rgb(hex_color)
    return _rgb_to_hex((r + (255 - r) * amount,
                        g + (255 - g) * amount,
                        b + (255 - b) * amount))


def readable_on(hex_color: str) -> str:
    """Vráti #000000/#FFFFFF podľa kontrastu voči danej farbe."""
    r, g, b = _hex_to_rgb(hex_color)
    luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
    return "#000000" if luminance > 0.6 else "#FFFFFF"
