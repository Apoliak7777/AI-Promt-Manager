"""Zobrazenie projektov vybraného AI — karty so statusom, editor, export .md."""
from __future__ import annotations

import re
from tkinter import filedialog

import customtkinter as ctk

from app import config
from app.db import models
from app.ui import theme
from app.ui.components import Badge, Card, EmptyState, IconButton, Tooltip
from app.ui.dialogs import ProjectEditor

_MD_STRIP = re.compile(r"[#>*_`~\-]{1,}")
_PREVIEW_LIMIT = 200


def _plain_preview(md: str, limit: int = _PREVIEW_LIMIT) -> str:
    lines = [ln for ln in md.splitlines() if ln.strip()]
    text = " ".join(lines)
    text = _MD_STRIP.sub("", text)
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    return text[:limit].rstrip() + "…"


class ProjectCard(Card):
    def __init__(self, parent, project: models.Project, view: "ProjectView"):
        super().__init__(parent, on_select=view.on_card_selected)
        self.project = project
        self.view = view
        self.grid_columnconfigure(0, weight=1)

        head = ctk.CTkFrame(self, fg_color="transparent")
        head.grid(row=0, column=0, sticky="ew", padx=14, pady=(12, 4))
        head.grid_columnconfigure(0, weight=1)

        name = ctk.CTkLabel(head, text=project.name, font=theme.font(15, "bold"),
                            text_color=theme.TEXT, anchor="w")
        name.grid(row=0, column=0, sticky="ew")

        status_color = config.STATUS_COLORS.get(project.status, theme.resolve(theme.TEXT_MUTED))
        Badge(head, project.status, status_color).grid(row=0, column=1, padx=(8, 8))

        actions = ctk.CTkFrame(head, fg_color="transparent")
        actions.grid(row=0, column=2, sticky="e")
        IconButton(actions, "👁️", command=lambda: self.view.open_project(self.project),
                   tooltip="Otvoriť / náhľad").pack(side="left", padx=1)
        IconButton(actions, "💾", command=lambda: self.view.export_project(self.project),
                   tooltip="Exportovať ako .md").pack(side="left", padx=1)
        IconButton(actions, "📄", command=lambda: self.view.duplicate_project(self.project),
                   tooltip="Duplikovať").pack(side="left", padx=1)
        IconButton(actions, "🗑️", command=lambda: self.view.delete_project(self.project),
                   tooltip="Zmazať", hover_color=theme.DANGER).pack(side="left", padx=1)

        preview_text = _plain_preview(project.content_md) or "— prázdny projekt —"
        self.preview = ctk.CTkLabel(
            self, text=preview_text, font=theme.font(13), text_color=theme.TEXT_MUTED,
            anchor="w", justify="left", wraplength=620,
        )
        self.preview.grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 2))

        # Prepojený prompt
        if project.linked_prompt_id:
            linked = models.get_prompt(project.linked_prompt_id)
            if linked:
                ctk.CTkLabel(
                    self, text=f"🔗 Prepojený prompt: {linked.name}",
                    font=theme.font(11), text_color=theme.get_accent(), anchor="w",
                ).grid(row=2, column=0, sticky="w", padx=14, pady=(2, 0))

        ctk.CTkFrame(self, fg_color="transparent", height=8).grid(row=3, column=0)

        self.bind("<Configure>", self._on_resize)
        for w in (name, self.preview):
            w.bind("<Double-Button-1>", lambda e: self.view.open_project(self.project))
        self.activate()

    def _on_resize(self, event) -> None:
        self.preview.configure(wraplength=max(200, event.width - 40))


class ProjectView(ctk.CTkFrame):
    def __init__(self, parent, controller, ai_id: int):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        self.ai_id = ai_id
        self.cards: list[ProjectCard] = []
        self.selected_card: ProjectCard | None = None
        self._empty = None

        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.pack(fill="x", padx=20, pady=(14, 6))
        toolbar.grid_columnconfigure(1, weight=1)
        ctk.CTkButton(
            toolbar, text="➕  Nový projekt", command=self.new_project,
            height=38, fg_color=theme.get_accent(), hover_color=theme.get_accent_hover(),
            text_color="#FFFFFF", font=theme.font(13, "bold"), corner_radius=theme.RADIUS,
        ).grid(row=0, column=0, sticky="w")

        self.sort_menu = ctk.CTkOptionMenu(
            toolbar, values=config.SORT_OPTIONS, command=self._on_sort_change,
            height=34, font=theme.font(12), corner_radius=theme.RADIUS,
            fg_color=theme.INPUT_BG, button_color=theme.get_accent(),
            button_hover_color=theme.get_accent_hover(), dropdown_font=theme.font(12),
            width=150,
        )
        self.sort_menu.grid(row=0, column=2, sticky="e")
        self.sort_menu.set(models.get_setting("sort_order", "Najnovšie"))

        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=14, pady=(0, 10))

        self.refresh()

    def _on_sort_change(self, value: str) -> None:
        models.set_setting("sort_order", value)
        self.refresh()

    def refresh(self) -> None:
        for card in self.cards:
            card.destroy()
        self.cards = []
        self.selected_card = None
        if self._empty is not None:
            self._empty.destroy()
            self._empty = None

        projects = models.list_projects(self.ai_id, sort=self.sort_menu.get())
        if not projects:
            self._empty = EmptyState(
                self.scroll, "📁", "Zatiaľ nemáš žiadne projekty",
                "Projekty sú .md poznámky, nápady a plány pre toto AI.",
                action_text="➕  Nový projekt", action_command=self.new_project,
            )
            self._empty.pack(fill="both", expand=True, pady=40)
            return
        for p in projects:
            card = ProjectCard(self.scroll, p, self)
            card.pack(fill="x", pady=5, padx=4)
            self.cards.append(card)

    def on_card_selected(self, card: ProjectCard) -> None:
        if self.selected_card and self.selected_card is not card:
            self.selected_card.set_selected(False)
        card.set_selected(True)
        self.selected_card = card

    def selected_project(self) -> models.Project | None:
        return self.selected_card.project if self.selected_card else None

    # ------------------------------------------------------------------ #
    def new_project(self) -> None:
        result = ProjectEditor(self.winfo_toplevel(), self.ai_id).show()
        if result:
            self.refresh()
            self.controller.refresh_sidebar_counts()
            self.controller.toast("Projekt uložený ✓", "success")

    def open_project(self, project: models.Project) -> None:
        fresh = models.get_project(project.id)
        if not fresh:
            return
        result = ProjectEditor(self.winfo_toplevel(), self.ai_id, project=fresh).show()
        if result:
            self.refresh()
            self.controller.toast("Zmeny uložené ✓", "success")

    def export_project(self, project: models.Project) -> None:
        safe = re.sub(r"[^\w\-. ]", "_", project.name).strip() or "projekt"
        path = filedialog.asksaveasfilename(
            parent=self.winfo_toplevel(), defaultextension=".md",
            initialfile=f"{safe}.md", title="Exportovať projekt ako .md",
            filetypes=[("Markdown", "*.md"), ("Všetky súbory", "*.*")],
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(project.content_md or "")
            self.controller.toast("Projekt exportovaný ✓", "success")
        except OSError as exc:
            self.controller.toast(f"Export zlyhal: {exc}", "error")

    def duplicate_project(self, project: models.Project) -> None:
        models.duplicate_project(project.id)
        self.refresh()
        self.controller.refresh_sidebar_counts()
        self.controller.toast("Projekt duplikovaný ✓", "success")

    def delete_project(self, project: models.Project) -> None:
        from app.ui.components import confirm
        if confirm(self.winfo_toplevel(), "Zmazať projekt?",
                   f"Naozaj chceš zmazať projekt „{project.name}“?",
                   ok_text="Zmazať", cancel_text="Zrušiť", danger=True):
            models.delete_project(project.id)
            self.refresh()
            self.controller.refresh_sidebar_counts()
            self.controller.toast("Projekt zmazaný", "info")

    def duplicate_selected(self) -> None:
        p = self.selected_project()
        if not p:
            self.controller.toast("Najprv klikni na kartu", "info")
            return
        self.duplicate_project(p)

    def delete_selected(self) -> None:
        p = self.selected_project()
        if p:
            self.delete_project(p)
