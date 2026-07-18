"""Znovupoužiteľné UI komponenty — karty, odznaky, tlačidlá, toast, tooltip,
prázdne stavy a základ pre modálne dialógy. Views z nich skladajú obrazovky, čo
drží vzhľad konzistentný.
"""
from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from app.ui import theme


# --------------------------------------------------------------------------- #
# Farebná bodka (kruh)
# --------------------------------------------------------------------------- #
def color_dot(parent, color: str, size: int = 12) -> ctk.CTkFrame:
    dot = ctk.CTkFrame(parent, width=size, height=size, corner_radius=size // 2,
                       fg_color=color, border_width=0)
    dot.grid_propagate(False)
    dot.pack_propagate(False)
    return dot


# --------------------------------------------------------------------------- #
# Odznaky / chipy
# --------------------------------------------------------------------------- #
class Badge(ctk.CTkLabel):
    def __init__(self, parent, text: str, color: str, text_color: str | None = None):
        super().__init__(
            parent, text=text, fg_color=color, corner_radius=theme.RADIUS_SM,
            text_color=text_color or theme.readable_on(color),
            font=theme.font(11, "bold"), padx=8, pady=2,
        )


class TagChip(ctk.CTkLabel):
    def __init__(self, parent, text: str):
        super().__init__(
            parent, text=text, fg_color=theme.get_accent_soft(),
            corner_radius=theme.RADIUS_SM, text_color=theme.get_accent(),
            font=theme.font(11), padx=8, pady=1,
        )


# --------------------------------------------------------------------------- #
# Ikonové tlačidlo
# --------------------------------------------------------------------------- #
class IconButton(ctk.CTkButton):
    def __init__(self, parent, text: str, command: Callable | None = None,
                 tooltip: str | None = None, size: int = 30,
                 fg_color: str | tuple = "transparent",
                 hover_color: str | tuple | None = None,
                 text_color: str | tuple | None = None, font_size: int = 15):
        super().__init__(
            parent, text=text, command=command, width=size, height=size,
            corner_radius=theme.RADIUS_SM, fg_color=fg_color,
            hover_color=hover_color or theme.CARD_HOVER,
            text_color=text_color or theme.TEXT_MUTED,
            font=theme.font(font_size),
        )
        if tooltip:
            Tooltip(self, tooltip)


# --------------------------------------------------------------------------- #
# Karta
# --------------------------------------------------------------------------- #
class Card(ctk.CTkFrame):
    """Klikateľná karta s hover efektom a stavom 'vybraná'."""

    def __init__(self, parent, on_select: Callable | None = None):
        super().__init__(
            parent, fg_color=theme.CARD, corner_radius=theme.RADIUS,
            border_width=1, border_color=theme.CARD_BORDER,
        )
        self._on_select = on_select
        self._selected = False
        self._hovering = False

    def activate(self) -> None:
        """Zaviaž hover/click eventy na kartu aj jej potomkov. Zavolať po naplnení."""
        self._bind_tree(self)

    def _bind_tree(self, widget) -> None:
        widget.bind("<Enter>", self._on_enter, add="+")
        widget.bind("<Leave>", self._on_leave, add="+")
        # Klik na výber len na ne-tlačidlových prvkoch
        if not isinstance(widget, ctk.CTkButton):
            widget.bind("<Button-1>", self._on_click, add="+")
        for child in widget.winfo_children():
            self._bind_tree(child)

    def _on_enter(self, _event=None) -> None:
        self._hovering = True
        if not self._selected:
            self.configure(fg_color=theme.CARD_HOVER)

    def _on_leave(self, _event=None) -> None:
        self._hovering = False
        if not self._selected:
            self.configure(fg_color=theme.CARD)

    def _on_click(self, _event=None) -> None:
        if self._on_select:
            self._on_select(self)

    def set_selected(self, value: bool) -> None:
        self._selected = value
        if value:
            self.configure(border_color=theme.get_accent(), border_width=2,
                           fg_color=theme.CARD_HOVER)
        else:
            self.configure(border_color=theme.CARD_BORDER, border_width=1,
                           fg_color=theme.CARD_HOVER if self._hovering else theme.CARD)


# --------------------------------------------------------------------------- #
# Tooltip
# --------------------------------------------------------------------------- #
class Tooltip:
    def __init__(self, widget, text: str, delay: int = 450):
        self.widget = widget
        self.text = text
        self.delay = delay
        self._after_id = None
        self._tip = None
        widget.bind("<Enter>", self._schedule, add="+")
        widget.bind("<Leave>", self._hide, add="+")
        widget.bind("<ButtonPress>", self._hide, add="+")

    def _schedule(self, _event=None):
        self._cancel()
        self._after_id = self.widget.after(self.delay, self._show)

    def _cancel(self):
        if self._after_id:
            try:
                self.widget.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None

    def _show(self):
        if self._tip or not self.text:
            return
        try:
            x = self.widget.winfo_rootx() + 20
            y = self.widget.winfo_rooty() + self.widget.winfo_height() + 6
        except Exception:
            return
        # Obmedz dĺžku textu — pri celých promptoch by tooltip zakryl obrazovku
        text = self.text
        if len(text) > 2000:
            text = text[:2000] + "…"
        self._tip = tip = ctk.CTkToplevel(self.widget)
        tip.overrideredirect(True)
        tip.attributes("-topmost", True)
        tip.geometry(f"+{x}+{y}")
        label = ctk.CTkLabel(
            tip, text=text, font=theme.font(11), justify="left",
            fg_color=("#2A2A38", "#0F0F18"), text_color="#FFFFFF",
            corner_radius=theme.RADIUS_SM, padx=8, pady=4, wraplength=480,
        )
        label.pack()

    def _hide(self, _event=None):
        self._cancel()
        if self._tip is not None:
            try:
                self._tip.destroy()
            except Exception:
                pass
            self._tip = None


# --------------------------------------------------------------------------- #
# Toast (dočasná notifikácia)
# --------------------------------------------------------------------------- #
def show_toast(master, message: str, kind: str = "info", duration: int = 1700,
               action_text: str | None = None,
               action_command: Callable | None = None) -> None:
    """Zobrazí dočasnú notifikáciu dole v strede okna ``master``.

    Voliteľne s akčným tlačidlom (``action_text`` + ``action_command``) —
    napr. „Späť" pri vratných operáciách.
    """
    colors = {
        "info": ("#2A2A38", "#33344B"),
        "success": (theme.SUCCESS, theme.SUCCESS),
        "error": (theme.DANGER, theme.DANGER),
    }
    fg = colors.get(kind, colors["info"])
    # Zruš predchádzajúci toast
    prev = getattr(master, "_active_toast", None)
    if prev is not None:
        try:
            prev.destroy()
        except Exception:
            pass

    toast = ctk.CTkFrame(master, fg_color=fg, corner_radius=theme.RADIUS)
    label = ctk.CTkLabel(toast, text=message, font=theme.font(13, "bold"),
                         text_color="#FFFFFF", padx=16, pady=8)
    label.pack(side="left")
    toast.place(relx=0.5, rely=0.96, anchor="s")
    master._active_toast = toast

    def _close():
        if getattr(master, "_active_toast", None) is toast:
            master._active_toast = None
        try:
            toast.destroy()
        except Exception:
            pass

    if action_text:
        def _on_action():
            _close()
            if action_command:
                action_command()

        ctk.CTkButton(
            toast, text=action_text, command=_on_action, width=60, height=26,
            fg_color="transparent", border_width=1, border_color="#FFFFFF",
            text_color="#FFFFFF", hover_color=("#3A3A48", "#44455B"),
            font=theme.font(12, "bold"), corner_radius=theme.RADIUS_SM,
        ).pack(side="left", padx=(0, 12), pady=6)

    master.after(duration, _close)


# --------------------------------------------------------------------------- #
# Prázdny stav
# --------------------------------------------------------------------------- #
class EmptyState(ctk.CTkFrame):
    def __init__(self, parent, icon: str, title: str, subtitle: str = "",
                 action_text: str | None = None,
                 action_command: Callable | None = None):
        super().__init__(parent, fg_color="transparent")
        wrap = ctk.CTkFrame(self, fg_color="transparent")
        wrap.place(relx=0.5, rely=0.42, anchor="center")

        ctk.CTkLabel(wrap, text=icon, font=theme.font(52)).pack(pady=(0, 8))
        ctk.CTkLabel(wrap, text=title, font=theme.font(16, "bold"),
                     text_color=theme.TEXT).pack()
        if subtitle:
            ctk.CTkLabel(wrap, text=subtitle, font=theme.font(13),
                         text_color=theme.TEXT_MUTED, wraplength=420,
                         justify="center").pack(pady=(4, 0))
        if action_text and action_command:
            ctk.CTkButton(
                wrap, text=action_text, command=action_command,
                fg_color=theme.get_accent(), hover_color=theme.get_accent_hover(),
                font=theme.font(13, "bold"), corner_radius=theme.RADIUS, height=38,
            ).pack(pady=(18, 0))


# --------------------------------------------------------------------------- #
# Modálny dialóg (základ)
# --------------------------------------------------------------------------- #
class ModalDialog(ctk.CTkToplevel):
    """Základ pre modálne dialógy — centrovanie, grab, Esc, wait_window.

    Podtriedy naplnia ``self`` obsahom a nastavia ``self.result`` pred zavretím.
    Použi ``dialog.show()`` na blokujúce zobrazenie a získanie výsledku.
    """

    def __init__(self, parent, title: str, width: int = 520, height: int = 420,
                 resizable: bool = False):
        super().__init__(parent)
        self.result = None
        self._parent = parent
        self.title(title)
        self.configure(fg_color=theme.BG)
        self.resizable(resizable, resizable)
        self._width = width
        self._height = height
        self.protocol("WM_DELETE_WINDOW", self._cancel)
        self.bind("<Escape>", lambda e: self._cancel())

    def _center(self) -> None:
        self.update_idletasks()
        w, h = self._width, self._height
        try:
            px = self._parent.winfo_rootx()
            py = self._parent.winfo_rooty()
            pw = self._parent.winfo_width()
            ph = self._parent.winfo_height()
            x = px + (pw - w) // 2
            y = py + (ph - h) // 2
        except Exception:
            x, y = 200, 120
        self.geometry(f"{w}x{h}+{max(0, x)}+{max(0, y)}")

    def show(self):
        # Zapamätaj si predchádzajúci grab (vnorené dialógy), aby sme ho vedeli vrátiť
        try:
            prior_grab = self.grab_current()
        except Exception:
            prior_grab = None
        self._center()
        self.transient(self._parent)
        self.lift()
        self.after(20, self._grab)
        self.wait_window()
        if prior_grab is not None:
            try:
                if prior_grab.winfo_exists():
                    prior_grab.grab_set()
            except Exception:
                pass
        return self.result

    def _grab(self):
        try:
            self.grab_set()
            self.focus_force()
        except Exception:
            pass

    def _cancel(self):
        self.result = None
        self.destroy()


# --------------------------------------------------------------------------- #
# Potvrdzovací dialóg
# --------------------------------------------------------------------------- #
class _ConfirmDialog(ModalDialog):
    def __init__(self, parent, title: str, message: str,
                 ok_text: str, cancel_text: str, danger: bool):
        super().__init__(parent, title, width=440, height=200)
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=24, pady=20)

        ctk.CTkLabel(container, text=title, font=theme.font(16, "bold"),
                     text_color=theme.TEXT, anchor="w").pack(fill="x")
        ctk.CTkLabel(container, text=message, font=theme.font(13),
                     text_color=theme.TEXT_MUTED, wraplength=380,
                     justify="left", anchor="w").pack(fill="x", pady=(8, 0))

        btns = ctk.CTkFrame(container, fg_color="transparent")
        btns.pack(side="bottom", fill="x", pady=(20, 0))
        ctk.CTkButton(
            btns, text=cancel_text, command=self._cancel, width=110, height=36,
            fg_color="transparent", border_width=1, border_color=theme.INPUT_BORDER,
            text_color=theme.TEXT, hover_color=theme.CARD_HOVER,
            font=theme.font(13), corner_radius=theme.RADIUS,
        ).pack(side="right", padx=(8, 0))
        ok_color = theme.DANGER if danger else theme.get_accent()
        ok_hover = theme.DANGER_HOVER if danger else theme.get_accent_hover()
        ok_btn = ctk.CTkButton(
            btns, text=ok_text, command=self._ok, width=110, height=36,
            fg_color=ok_color, hover_color=ok_hover, text_color="#FFFFFF",
            font=theme.font(13, "bold"), corner_radius=theme.RADIUS,
        )
        ok_btn.pack(side="right")
        self.bind("<Return>", lambda e: self._ok())
        ok_btn.focus_set()

    def _ok(self):
        self.result = True
        self.destroy()


def confirm(parent, title: str, message: str, ok_text: str = "Áno",
            cancel_text: str = "Zrušiť", danger: bool = False) -> bool:
    dlg = _ConfirmDialog(parent, title, message, ok_text, cancel_text, danger)
    return bool(dlg.show())


# --------------------------------------------------------------------------- #
# Sekčný nadpis
# --------------------------------------------------------------------------- #
class FieldLabel(ctk.CTkLabel):
    def __init__(self, parent, text: str, required: bool = False):
        display = f"{text} *" if required else text
        super().__init__(parent, text=display, font=theme.font(12, "bold"),
                         text_color=theme.TEXT_MUTED, anchor="w")
