"""Výsledky globálneho vyhľadávania — prompty aj projekty naprieč všetkými AI."""
from __future__ import annotations

import customtkinter as ctk

from app.db import models
from app.ui import theme
from app.ui.components import Badge, Card, EmptyState, IconButton, color_dot

_SNIPPET = 160


def _snippet(text: str) -> str:
    flat = " ".join(text.split())
    return flat[:_SNIPPET].rstrip() + ("…" if len(flat) > _SNIPPET else "")


class SearchResultsView(ctk.CTkFrame):
    def __init__(self, parent, controller, query: str):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        self.query = query

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(18, 6))
        ctk.CTkLabel(header, text=f"🔍  Výsledky pre „{query}“",
                     font=theme.font(18, "bold"), text_color=theme.TEXT,
                     anchor="w").pack(side="left")

        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=18, pady=(4, 10))

        self._render()

    def _render(self) -> None:
        results = models.search_global(self.query)
        prompts = results["prompts"]
        projects = results["projects"]
        total = len(prompts) + len(projects)

        if total == 0:
            EmptyState(self.scroll, "🕵️", "Nič sa nenašlo",
                       f"Pre „{self.query}“ nemáme žiadne prompty ani projekty.").pack(
                fill="both", expand=True, pady=60)
            return

        summary = ctk.CTkLabel(
            self.scroll, text=f"Nájdených {len(prompts)} promptov a "
            f"{len(projects)} projektov",
            font=theme.font(12), text_color=theme.TEXT_MUTED, anchor="w",
        )
        summary.pack(fill="x", padx=4, pady=(0, 8))

        if prompts:
            self._section("Prompty")
            for prompt, plat in prompts:
                self._prompt_result(prompt, plat)
        if projects:
            self._section("Projekty")
            for project, plat in projects:
                self._project_result(project, plat)

    def _section(self, title: str) -> None:
        ctk.CTkLabel(self.scroll, text=title.upper(), font=theme.font(11, "bold"),
                     text_color=theme.TEXT_FAINT, anchor="w").pack(
            fill="x", padx=6, pady=(12, 4))

    def _meta_row(self, card, plat: models.Platform, name: str) -> ctk.CTkFrame:
        head = ctk.CTkFrame(card, fg_color="transparent")
        head.grid(row=0, column=0, sticky="ew", padx=14, pady=(10, 2))
        head.grid_columnconfigure(2, weight=1)
        color_dot(head, plat.color, 10).grid(row=0, column=0, padx=(0, 6))
        ctk.CTkLabel(head, text=plat.name, font=theme.font(11),
                     text_color=theme.TEXT_MUTED).grid(row=0, column=1, padx=(0, 10))
        ctk.CTkLabel(head, text=name, font=theme.font(14, "bold"),
                     text_color=theme.TEXT, anchor="w").grid(row=0, column=2, sticky="ew")
        return head

    def _prompt_result(self, prompt: models.Prompt, plat: models.Platform) -> None:
        card = Card(self.scroll)
        card.grid_columnconfigure(0, weight=1)
        card.pack(fill="x", pady=4, padx=4)
        head = self._meta_row(card, plat, prompt.name)
        actions = ctk.CTkFrame(head, fg_color="transparent")
        actions.grid(row=0, column=3, sticky="e")
        IconButton(actions, "📋", tooltip="Kopírovať",
                   command=lambda: self._copy(prompt.content)).pack(side="left", padx=1)
        IconButton(actions, "➡️", tooltip="Prejsť na toto AI",
                   command=lambda: self.controller.goto_prompt(plat.id)).pack(
            side="left", padx=1)
        ctk.CTkLabel(card, text=_snippet(prompt.content), font=theme.font(12),
                     text_color=theme.TEXT_MUTED, anchor="w", justify="left",
                     wraplength=700).grid(row=1, column=0, sticky="ew", padx=14,
                                          pady=(0, 12))
        card.activate()

    def _project_result(self, project: models.Project, plat: models.Platform) -> None:
        card = Card(self.scroll)
        card.grid_columnconfigure(0, weight=1)
        card.pack(fill="x", pady=4, padx=4)
        head = self._meta_row(card, plat, project.name)
        status_color = self.controller.status_color(project.status)
        Badge(head, project.status, status_color).grid(row=0, column=3, padx=(6, 6))
        actions = ctk.CTkFrame(head, fg_color="transparent")
        actions.grid(row=0, column=4, sticky="e")
        IconButton(actions, "➡️", tooltip="Prejsť na toto AI",
                   command=lambda: self.controller.goto_project(plat.id)).pack(
            side="left", padx=1)
        ctk.CTkLabel(card, text=_snippet(project.content_md) or "— prázdny —",
                     font=theme.font(12), text_color=theme.TEXT_MUTED, anchor="w",
                     justify="left", wraplength=700).grid(
            row=1, column=0, sticky="ew", padx=14, pady=(0, 12))
        card.activate()

    def _copy(self, text: str) -> None:
        from app.utils.clipboard import copy_to_clipboard
        if copy_to_clipboard(text, widget=self.winfo_toplevel()):
            self.controller.toast("Skopírované ✓", "success")
        else:
            self.controller.toast("Kopírovanie zlyhalo", "error")
