"""Kopírovanie do systémovej schránky — pyperclip s tkinter fallbackom."""
from __future__ import annotations

try:
    import pyperclip
    _HAS_PYPERCLIP = True
except Exception:  # pragma: no cover
    pyperclip = None
    _HAS_PYPERCLIP = False


def copy_to_clipboard(text: str, widget=None) -> bool:
    """Skopíruje text do schránky. Vráti True pri úspechu.

    Skúsi pyperclip; ak zlyhá (napr. chýbajúci backend na Linuxe), použije
    tkinter clipboard cez odovzdaný widget.
    """
    if _HAS_PYPERCLIP:
        try:
            pyperclip.copy(text)
            return True
        except Exception:
            pass
    if widget is not None:
        try:
            widget.clipboard_clear()
            widget.clipboard_append(text)
            widget.update_idletasks()
            return True
        except Exception:
            pass
    return False
