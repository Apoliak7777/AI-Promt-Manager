"""Ľavý sidebar — globálne vyhľadávanie, zoznam AI platforiem, akcie."""
from __future__ import annotations

import tkinter as tk

import customtkinter as ctk

from app import config
from app.db import models
from app.ui import theme
from app.ui.components import Tooltip, color_dot


class PlatformRow(ctk.CTkFrame):
    def __init__(self, parent, platform: models.Platform, controller):
        super().__init__(parent, fg_color="transparent", corner_radius=theme.RADIUS_SM,
                         height=38)
        self.platform = platform
        self.controller = controller
        self._active = False
        self.grid_columnconfigure(1, weight=1)
        self.grid_propagate(False)

        self.dot = color_dot(self, platform.color, size=12)
        self.dot.grid(row=0, column=0, padx=(12, 8), pady=9)

        self.label = ctk.CTkLabel(
            self, text=platform.name, font=theme.font(13),
            text_color=theme.TEXT, anchor="w",
        )
        self.label.grid(row=0, column=1, sticky="ew", pady=8)

        self.count = ctk.CTkLabel(self, text="", font=theme.font(11),
                                  text_color=theme.TEXT_FAINT)
        self.count.grid(row=0, column=2, padx=(4, 10))

        for w in (self, self.label, self.dot, self.count):
            w.bind("<Button-1>", self._on_click, add="+")
            w.bind("<Button-3>", self._on_context, add="+")
            w.bind("<Enter>", self._on_enter, add="+")
            w.bind("<Leave>", self._on_leave, add="+")

    def update_count(self) -> None:
        n = models.count_prompts(self.platform.id) + models.count_projects(self.platform.id)
        self.count.configure(text=str(n) if n else "")

    def _on_click(self, _e=None):
        self.controller.select_ai(self.platform.id)

    def _on_enter(self, _e=None):
        if not self._active:
            self.configure(fg_color=theme.CARD_HOVER)

    def _on_leave(self, _e=None):
        if not self._active:
            self.configure(fg_color="transparent")

    def set_active(self, value: bool) -> None:
        self._active = value
        if value:
            self.configure(fg_color=theme.get_accent_soft())
            self.label.configure(text_color=theme.get_accent(), font=theme.font(13, "bold"))
        else:
            self.configure(fg_color="transparent")
            self.label.configure(text_color=theme.TEXT, font=theme.font(13))

    def _on_context(self, event):
        menu = tk.Menu(self, tearoff=0)
        launch_url = config.AI_LAUNCH_URLS.get(self.platform.name)
        if launch_url or self.platform.is_custom:
            menu.add_command(label="🚀  Otvoriť v prehliadači",
                             command=lambda: self.controller.launch_ai(self.platform))
            menu.add_separator()
        if self.platform.is_custom:
            menu.add_command(label="✏️  Upraviť AI",
                             command=lambda: self.controller.edit_platform(self.platform))
            menu.add_command(label="🗑️  Zmazať AI",
                             command=lambda: self.controller.delete_platform(self.platform))
        else:
            menu.add_command(label="Predvolené AI sa nedá zmazať", state="disabled")
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()


class Sidebar(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=theme.SIDEBAR_BG, corner_radius=0, width=248)
        self.controller = controller
        self.grid_propagate(False)
        self.rows: list[PlatformRow] = []
        self._search_job = None

        # Logo / title
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=(16, 10))
        ctk.CTkLabel(header, text="🧠", font=theme.font(22)).pack(side="left")
        ctk.CTkLabel(header, text="AI Prompt\nManager", font=theme.font(14, "bold"),
                     text_color=theme.TEXT, justify="left").pack(side="left", padx=(8, 0))

        # Search
        search_wrap = ctk.CTkFrame(self, fg_color="transparent")
        search_wrap.pack(fill="x", padx=12, pady=(0, 8))
        self.search_entry = ctk.CTkEntry(
            search_wrap, height=36, font=theme.font(13), corner_radius=theme.RADIUS,
            fg_color=theme.INPUT_BG, border_color=theme.INPUT_BORDER,
            placeholder_text="🔍  Hľadať naprieč AI…",
        )
        self.search_entry.pack(fill="x")
        self.search_entry.bind("<KeyRelease>", self._on_search_key)
        self.search_entry.bind("<Escape>", lambda e: self.clear_search())

        # Platform list (scrollable)
        self.list_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.list_frame.pack(fill="both", expand=True, padx=6, pady=(2, 4))

        # Bottom actions
        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.pack(fill="x", side="bottom", padx=12, pady=(4, 14))

        ctk.CTkButton(
            bottom, text="➕  Pridať AI", command=self.controller.open_add_platform,
            height=36, fg_color=theme.INPUT_BG, hover_color=theme.CARD_HOVER,
            text_color=theme.TEXT, font=theme.font(13), corner_radius=theme.RADIUS,
            anchor="w",
        ).pack(fill="x", pady=(0, 8))

        ctk.CTkFrame(bottom, height=1, fg_color=theme.DIVIDER).pack(fill="x", pady=(0, 8))

        actions = ctk.CTkFrame(bottom, fg_color="transparent")
        actions.pack(fill="x")
        actions.grid_columnconfigure((0, 1), weight=1)
        ctk.CTkButton(
            actions, text="📊  Štatistiky", command=self.controller.open_stats,
            height=34, fg_color="transparent", hover_color=theme.CARD_HOVER,
            text_color=theme.TEXT_MUTED, font=theme.font(12), corner_radius=theme.RADIUS,
        ).grid(row=0, column=0, sticky="ew", padx=(0, 3))
        ctk.CTkButton(
            actions, text="⚙️  Nastavenia", command=self.controller.open_settings,
            height=34, fg_color="transparent", hover_color=theme.CARD_HOVER,
            text_color=theme.TEXT_MUTED, font=theme.font(12), corner_radius=theme.RADIUS,
        ).grid(row=0, column=1, sticky="ew", padx=(3, 0))

    # ------------------------------------------------------------------ #
    def refresh(self, active_id: int | None = None) -> None:
        for row in self.rows:
            row.destroy()
        self.rows = []
        for plat in models.list_platforms():
            row = PlatformRow(self.list_frame, plat, self.controller)
            row.pack(fill="x", pady=1)
            row.update_count()
            self.rows.append(row)
        if active_id is not None:
            self.set_active(active_id)

    def set_active(self, ai_id: int) -> None:
        for row in self.rows:
            row.set_active(row.platform.id == ai_id)

    def update_counts(self) -> None:
        for row in self.rows:
            row.update_count()

    def focus_search(self) -> None:
        self.search_entry.focus_set()

    def clear_search(self) -> None:
        self.search_entry.delete(0, "end")
        self.controller.global_search("")

    def _on_search_key(self, event=None) -> None:
        if self._search_job:
            self.after_cancel(self._search_job)
        self._search_job = self.after(200, self._fire_search)

    def _fire_search(self) -> None:
        self._search_job = None
        self.controller.global_search(self.search_entry.get().strip())
