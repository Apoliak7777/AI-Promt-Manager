"""Štatistiky — súhrny a rozdelenie promptov/projektov podľa AI."""
from __future__ import annotations

import customtkinter as ctk

from app.db import models
from app.ui import theme
from app.ui.components import EmptyState, color_dot


class StatsView(ctk.CTkScrollableFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller

        ctk.CTkLabel(self, text="📊  Štatistiky", font=theme.font(20, "bold"),
                     text_color=theme.TEXT, anchor="w").pack(
            fill="x", padx=24, pady=(20, 12))

        totals = models.totals()
        self._totals_row(totals)

        stats = models.platform_stats()
        if totals["prompts"] == 0 and totals["projects"] == 0:
            EmptyState(self, "📈", "Zatiaľ žiadne dáta",
                       "Pridaj prvé prompty a projekty a uvidíš tu prehľad.").pack(
                fill="both", expand=True, pady=40)
            return

        self._distribution(stats)

    def _totals_row(self, totals: dict) -> None:
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=(0, 10))
        cards = [
            ("📝", "Prompty", totals["prompts"], theme.get_accent()),
            ("📁", "Projekty", totals["projects"], "#4C8DFF"),
            ("⭐", "Obľúbené", totals["favorites"], theme.WARNING),
            ("🤖", "AI platformy", totals["platforms"], theme.SUCCESS),
        ]
        for i in range(len(cards)):
            row.grid_columnconfigure(i, weight=1)
        for i, (icon, label, value, accent) in enumerate(cards):
            c = ctk.CTkFrame(row, fg_color=theme.CARD, corner_radius=theme.RADIUS,
                             border_width=1, border_color=theme.CARD_BORDER)
            c.grid(row=0, column=i, sticky="ew", padx=6, pady=4)
            ctk.CTkLabel(c, text=icon, font=theme.font(22)).pack(pady=(14, 0))
            ctk.CTkLabel(c, text=str(value), font=theme.font(26, "bold"),
                         text_color=accent).pack()
            ctk.CTkLabel(c, text=label, font=theme.font(12),
                         text_color=theme.TEXT_MUTED).pack(pady=(0, 14))

    def _distribution(self, stats: list[dict]) -> None:
        card = ctk.CTkFrame(self, fg_color=theme.CARD, corner_radius=theme.RADIUS,
                            border_width=1, border_color=theme.CARD_BORDER)
        card.pack(fill="x", padx=24, pady=8)
        ctk.CTkLabel(card, text="Rozdelenie podľa AI", font=theme.font(15, "bold"),
                     text_color=theme.TEXT, anchor="w").pack(
            fill="x", padx=18, pady=(14, 8))

        max_total = max((s["prompts"] + s["projects"] for s in stats), default=0) or 1
        for s in stats:
            plat = s["platform"]
            total = s["prompts"] + s["projects"]
            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=18, pady=4)
            row.grid_columnconfigure(1, weight=1)

            label = ctk.CTkFrame(row, fg_color="transparent")
            label.grid(row=0, column=0, sticky="w", padx=(0, 12))
            color_dot(label, plat.color, 11).pack(side="left", padx=(0, 6))
            ctk.CTkLabel(label, text=plat.name, font=theme.font(12),
                         text_color=theme.TEXT, width=130, anchor="w").pack(side="left")

            track = ctk.CTkFrame(row, fg_color=theme.INPUT_BG, height=18,
                                 corner_radius=9)
            track.grid(row=0, column=1, sticky="ew")
            track.grid_propagate(False)
            ratio = total / max_total if max_total else 0
            if ratio > 0:
                fill = ctk.CTkFrame(track, fg_color=plat.color, height=18,
                                    corner_radius=9)
                fill.place(relwidth=max(0.02, ratio), relheight=1.0)

            ctk.CTkLabel(
                row, text=f"{s['prompts']} · {s['projects']}  (⭐{s['favorites']})",
                font=theme.font(11), text_color=theme.TEXT_MUTED, width=120,
            ).grid(row=0, column=2, sticky="e", padx=(12, 0))

        ctk.CTkLabel(card, text="prompty · projekty  (⭐ obľúbené)",
                     font=theme.font(10), text_color=theme.TEXT_FAINT,
                     anchor="e").pack(fill="x", padx=18, pady=(4, 14))
