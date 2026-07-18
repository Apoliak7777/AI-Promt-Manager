"""Zobrazenie promptov vybraného AI — toolbar (nový/filter/triedenie) + karty."""
from __future__ import annotations

import customtkinter as ctk

from app import config
from app.db import models
from app.ui import theme
from app.ui.components import Card, EmptyState, IconButton, TagChip, Tooltip
from app.ui.dialogs import PromptDialog

_PREVIEW_LIMIT = 220


def _truncate(text: str, limit: int = _PREVIEW_LIMIT) -> str:
    flat = " ".join(text.split())
    if len(flat) <= limit:
        return flat
    return flat[:limit].rstrip() + "…"


class PromptCard(Card):
    def __init__(self, parent, prompt: models.Prompt, view: "PromptView"):
        super().__init__(parent, on_select=view.on_card_selected)
        self.prompt = prompt
        self.view = view
        self.grid_columnconfigure(0, weight=1)

        # --- Header row ---
        head = ctk.CTkFrame(self, fg_color="transparent")
        head.grid(row=0, column=0, sticky="ew", padx=14, pady=(12, 2))
        head.grid_columnconfigure(1, weight=1)

        self.star = ctk.CTkLabel(
            head, text="⭐" if prompt.favorite else "☆",
            font=theme.font(16),
            text_color=theme.WARNING if prompt.favorite else theme.TEXT_FAINT,
            cursor="hand2",
        )
        self.star.grid(row=0, column=0, padx=(0, 8))
        self.star.bind("<Button-1>", self._on_star_click)
        Tooltip(self.star, "Obľúbený")

        self.name = ctk.CTkLabel(
            head, text=prompt.name, font=theme.font(15, "bold"),
            text_color=theme.TEXT, anchor="w",
        )
        self.name.grid(row=0, column=1, sticky="ew")

        actions = ctk.CTkFrame(head, fg_color="transparent")
        actions.grid(row=0, column=2, sticky="e")
        IconButton(actions, "📋", command=lambda: self.view.copy_prompt(self.prompt),
                   tooltip="Kopírovať prompt").pack(side="left", padx=1)
        IconButton(actions, "✏️", command=lambda: self.view.edit_prompt(self.prompt),
                   tooltip="Upraviť").pack(side="left", padx=1)
        IconButton(actions, "🗑️", command=lambda: self.view.delete_prompt(self.prompt),
                   tooltip="Zmazať", hover_color=theme.DANGER,
                   text_color=theme.TEXT_MUTED).pack(side="left", padx=1)

        # --- Tags ---
        if prompt.tags:
            tagbar = ctk.CTkFrame(self, fg_color="transparent")
            tagbar.grid(row=1, column=0, sticky="w", padx=14, pady=(0, 2))
            for t in prompt.tags[:6]:
                TagChip(tagbar, t).pack(side="left", padx=(0, 4))

        # --- Content preview ---
        self._preview_limit = _PREVIEW_LIMIT
        self.preview = ctk.CTkLabel(
            self, text=_truncate(prompt.content), font=theme.font(13),
            text_color=theme.TEXT_MUTED, anchor="w", justify="left",
            wraplength=620,
        )
        self.preview.grid(row=2, column=0, sticky="ew", padx=14, pady=(2, 0))
        if len(" ".join(prompt.content.split())) > _PREVIEW_LIMIT:
            Tooltip(self.preview, prompt.content)

        # --- Note ---
        if prompt.note:
            ctk.CTkLabel(
                self, text=f"📝 {prompt.note}", font=theme.font(11),
                text_color=theme.TEXT_FAINT, anchor="w", justify="left",
                wraplength=620,
            ).grid(row=3, column=0, sticky="ew", padx=14, pady=(4, 0))

        ctk.CTkFrame(self, fg_color="transparent", height=8).grid(row=4, column=0)

        self.bind("<Configure>", self._on_resize)
        self.activate()

    def _on_star_click(self, _event) -> str:
        self.view.toggle_favorite(self.prompt)
        return "break"  # zastaví ďalšie bindingy — karta je po toggli zničená

    def _on_resize(self, event) -> None:
        wrap = max(200, event.width - 40)
        self.preview.configure(wraplength=wrap)
        # náhľad na ~2 riadky: limit znakov odvodený zo šírky (13px font)
        limit = max(80, 2 * (wrap // 7))
        if limit != self._preview_limit:
            self._preview_limit = limit
            self.preview.configure(text=_truncate(self.prompt.content, limit))


class PromptView(ctk.CTkFrame):
    def __init__(self, parent, controller, ai_id: int):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        self.ai_id = ai_id
        self.cards: list[PromptCard] = []
        self.selected_card: PromptCard | None = None
        self._empty = None
        self._tag_filter = "Všetky tagy"

        # --- Toolbar ---
        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.pack(fill="x", padx=20, pady=(14, 6))
        toolbar.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(
            toolbar, text="➕  Nový prompt", command=self.new_prompt,
            height=38, fg_color=theme.get_accent(), hover_color=theme.get_accent_hover(),
            text_color="#FFFFFF", font=theme.font(13, "bold"), corner_radius=theme.RADIUS,
        ).grid(row=0, column=0, sticky="w")

        filters = ctk.CTkFrame(toolbar, fg_color="transparent")
        filters.grid(row=0, column=2, sticky="e")

        self.tag_menu = ctk.CTkOptionMenu(
            filters, values=self._tag_values(), command=self._on_tag_change,
            height=34, font=theme.font(12), corner_radius=theme.RADIUS,
            fg_color=theme.INPUT_BG, button_color=theme.get_accent(),
            button_hover_color=theme.get_accent_hover(), dropdown_font=theme.font(12),
            width=150,
        )
        self.tag_menu.grid(row=0, column=0, padx=(0, 8))
        self.tag_menu.set("Všetky tagy")

        self.sort_menu = ctk.CTkOptionMenu(
            filters, values=config.SORT_OPTIONS, command=self._on_sort_change,
            height=34, font=theme.font(12), corner_radius=theme.RADIUS,
            fg_color=theme.INPUT_BG, button_color=theme.get_accent(),
            button_hover_color=theme.get_accent_hover(), dropdown_font=theme.font(12),
            width=150,
        )
        self.sort_menu.grid(row=0, column=1)
        self.sort_menu.set(models.get_setting("sort_order", "Obľúbené prvé"))

        # --- Scrollable list ---
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=14, pady=(0, 10))

        self.refresh()

    # ------------------------------------------------------------------ #
    def _tag_values(self) -> list[str]:
        return ["Všetky tagy"] + models.all_tags(self.ai_id)

    def _on_tag_change(self, value: str) -> None:
        self._tag_filter = value
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

        # obnov tag hodnoty (mohli pribudnúť)
        current = self.tag_menu.get()
        self.tag_menu.configure(values=self._tag_values())
        if current not in self._tag_values():
            current = "Všetky tagy"
            self._tag_filter = "Všetky tagy"
        self.tag_menu.set(current)

        sort = self.sort_menu.get()
        prompts = models.list_prompts(self.ai_id, sort=sort, tag=self._tag_filter)

        if not prompts:
            self._show_empty()
            return

        for p in prompts:
            card = PromptCard(self.scroll, p, self)
            card.pack(fill="x", pady=5, padx=4)
            self.cards.append(card)

    def _show_empty(self) -> None:
        if self._tag_filter != "Všetky tagy":
            self._empty = EmptyState(
                self.scroll, "🔍", "Žiadne prompty s týmto tagom",
                "Skús zmeniť filter alebo pridaj nový prompt.",
            )
        else:
            self._empty = EmptyState(
                self.scroll, "📝", "Zatiaľ nemáš žiadne prompty",
                "Klikni na ➕ a pridaj svoj prvý prompt pre toto AI!",
                action_text="➕  Nový prompt", action_command=self.new_prompt,
            )
        self._empty.pack(fill="both", expand=True, pady=40)

    # ------------------------------------------------------------------ #
    def on_card_selected(self, card: PromptCard) -> None:
        if self.selected_card and self.selected_card is not card:
            self.selected_card.set_selected(False)
        card.set_selected(True)
        self.selected_card = card

    def selected_prompt(self) -> models.Prompt | None:
        return self.selected_card.prompt if self.selected_card else None

    # ------------------------------------------------------------------ #
    def new_prompt(self) -> None:
        result = PromptDialog(self.winfo_toplevel(), self.ai_id).show()
        if result:
            self.refresh()
            self.controller.refresh_sidebar_counts()
            self.controller.toast("Prompt uložený ✓", "success")

    def edit_prompt(self, prompt: models.Prompt) -> None:
        fresh = models.get_prompt(prompt.id)
        if not fresh:
            return
        result = PromptDialog(self.winfo_toplevel(), self.ai_id, prompt=fresh).show()
        if result:
            self.refresh()
            self.controller.toast("Zmeny uložené ✓", "success")

    def copy_prompt(self, prompt: models.Prompt) -> None:
        from app.utils.clipboard import copy_to_clipboard
        ok = copy_to_clipboard(prompt.content, widget=self.winfo_toplevel())
        if ok:
            self.controller.toast("Skopírované ✓", "success")
        else:
            self.controller.toast("Kopírovanie zlyhalo", "error")

    def toggle_favorite(self, prompt: models.Prompt) -> None:
        models.toggle_favorite(prompt.id)
        self.refresh()

    def delete_prompt(self, prompt: models.Prompt) -> None:
        from app.ui.components import confirm
        if confirm(self.winfo_toplevel(), "Zmazať prompt?",
                   f"Naozaj chceš zmazať prompt „{prompt.name}“?",
                   ok_text="Zmazať", cancel_text="Zrušiť", danger=True):
            models.delete_prompt(prompt.id)
            self.refresh()
            self.controller.refresh_sidebar_counts()
            self.controller.toast("Prompt zmazaný", "info")

    def duplicate_selected(self) -> None:
        p = self.selected_prompt()
        if not p:
            self.controller.toast("Najprv klikni na kartu", "info")
            return
        models.duplicate_prompt(p.id)
        self.refresh()
        self.controller.refresh_sidebar_counts()
        self.controller.toast("Prompt duplikovaný ✓", "success")

    def delete_selected(self) -> None:
        p = self.selected_prompt()
        if p:
            self.delete_prompt(p)
