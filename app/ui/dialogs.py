"""Modálne dialógy — prompt formulár, project markdown editor, custom AI.

Každý dialóg si sám rieši validáciu aj uloženie do DB a cez :meth:`show` vráti id
uloženého záznamu (alebo ``None`` pri zrušení). Views ho len otvoria a po
neprázdnom výsledku refreshnú zoznam.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import colorchooser

import customtkinter as ctk

from app import config
from app.db import models
from app.ui import theme
from app.ui.components import (
    Badge, FieldLabel, ModalDialog, Tooltip, confirm, show_toast,
)
from app.utils.markdown import render_markdown


# --------------------------------------------------------------------------- #
# Prompt dialóg
# --------------------------------------------------------------------------- #
class PromptDialog(ModalDialog):
    def __init__(self, parent, ai_id: int, prompt: models.Prompt | None = None):
        title = "Upraviť prompt" if prompt else "Nový prompt"
        super().__init__(parent, title, width=560, height=580, resizable=True)
        self.ai_id = ai_id
        self.prompt = prompt

        root = ctk.CTkFrame(self, fg_color="transparent")
        root.pack(fill="both", expand=True, padx=24, pady=20)
        root.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(root, text=title, font=theme.font(18, "bold"),
                     text_color=theme.TEXT, anchor="w").grid(
            row=0, column=0, sticky="ew", pady=(0, 14))

        # Názov
        FieldLabel(root, "Názov", required=True).grid(row=1, column=0, sticky="w")
        self.name_entry = ctk.CTkEntry(
            root, height=38, font=theme.font(13), corner_radius=theme.RADIUS,
            fg_color=theme.INPUT_BG, border_color=theme.INPUT_BORDER,
            placeholder_text="napr. SEO článok SK",
        )
        self.name_entry.grid(row=2, column=0, sticky="ew", pady=(4, 2))
        self.name_error = self._error_label(root, row=3)

        # Tag
        tag_row = ctk.CTkFrame(root, fg_color="transparent")
        tag_row.grid(row=4, column=0, sticky="ew", pady=(6, 0))
        tag_row.grid_columnconfigure(0, weight=1)
        FieldLabel(tag_row, "Kategória / Tag").grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(tag_row, text="(viac oddeľ čiarkou)", font=theme.font(11),
                     text_color=theme.TEXT_FAINT).grid(row=0, column=1, sticky="e")
        existing = models.all_tags(ai_id)
        tag_values = list(dict.fromkeys(config.DEFAULT_TAGS + existing))
        self.tag_box = ctk.CTkComboBox(
            root, values=tag_values, height=36, font=theme.font(13),
            corner_radius=theme.RADIUS, fg_color=theme.INPUT_BG,
            border_color=theme.INPUT_BORDER, button_color=theme.get_accent(),
            button_hover_color=theme.get_accent_hover(),
            dropdown_font=theme.font(12),
        )
        self.tag_box.grid(row=5, column=0, sticky="new", pady=(4, 0))
        self.tag_box.set("")

        # Prompt text
        FieldLabel(root, "Prompt text", required=True).grid(
            row=6, column=0, sticky="w", pady=(10, 0))
        self.text_box = ctk.CTkTextbox(
            root, height=170, font=theme.font(13), corner_radius=theme.RADIUS,
            fg_color=theme.INPUT_BG, border_width=1, border_color=theme.INPUT_BORDER,
            wrap="word",
        )
        self.text_box.grid(row=7, column=0, sticky="nsew", pady=(4, 2))
        root.grid_rowconfigure(7, weight=1)
        self.text_error = self._error_label(root, row=8)

        # Poznámka
        FieldLabel(root, "Poznámka").grid(row=9, column=0, sticky="w", pady=(8, 0))
        self.note_entry = ctk.CTkEntry(
            root, height=36, font=theme.font(13), corner_radius=theme.RADIUS,
            fg_color=theme.INPUT_BG, border_color=theme.INPUT_BORDER,
            placeholder_text="krátka poznámka (voliteľné)",
        )
        self.note_entry.grid(row=10, column=0, sticky="ew", pady=(4, 0))

        # Obľúbený
        self.fav_var = ctk.BooleanVar(value=False)
        self.fav_check = ctk.CTkCheckBox(
            root, text="  Označiť ako obľúbený", variable=self.fav_var,
            font=theme.font(13), text_color=theme.TEXT,
            fg_color=theme.get_accent(), hover_color=theme.get_accent_hover(),
            checkmark_color="#FFFFFF", corner_radius=6,
        )
        self.fav_check.grid(row=11, column=0, sticky="w", pady=(12, 0))

        # Tlačidlá
        btns = ctk.CTkFrame(root, fg_color="transparent")
        btns.grid(row=12, column=0, sticky="ew", pady=(18, 0))
        ctk.CTkButton(
            btns, text="Zrušiť", command=self._cancel, width=110, height=38,
            fg_color="transparent", border_width=1, border_color=theme.INPUT_BORDER,
            text_color=theme.TEXT, hover_color=theme.CARD_HOVER,
            font=theme.font(13), corner_radius=theme.RADIUS,
        ).pack(side="right", padx=(8, 0))
        ctk.CTkButton(
            btns, text="Uložiť", command=self._save, width=140, height=38,
            fg_color=theme.get_accent(), hover_color=theme.get_accent_hover(),
            text_color="#FFFFFF", font=theme.font(13, "bold"),
            corner_radius=theme.RADIUS,
        ).pack(side="right")

        # Widget-level bind má prednosť pred class bindom Text (<Return> by inak
        # vložil nový riadok pred uložením); "break" zastaví propagáciu.
        self.text_box.bind("<Control-Return>", self._on_ctrl_enter)
        self.bind("<Control-Return>", lambda e: self._save())

        if prompt:
            self._prefill(prompt)
        self.after(60, self.name_entry.focus_set)

    def _error_label(self, parent, row: int) -> ctk.CTkLabel:
        lbl = ctk.CTkLabel(parent, text="", font=theme.font(11),
                           text_color=theme.DANGER, anchor="w")
        lbl.grid(row=row, column=0, sticky="w")
        return lbl

    def _prefill(self, p: models.Prompt) -> None:
        self.name_entry.insert(0, p.name)
        self.tag_box.set(", ".join(p.tags))
        self.text_box.insert("1.0", p.content)
        self.note_entry.insert(0, p.note)
        self.fav_var.set(p.favorite)

    def _clear_errors(self) -> None:
        self.name_error.configure(text="")
        self.text_error.configure(text="")
        self.name_entry.configure(border_color=theme.INPUT_BORDER)
        self.text_box.configure(border_color=theme.INPUT_BORDER)

    def _on_ctrl_enter(self, _event=None) -> str:
        self._save()
        return "break"

    def _save(self) -> None:
        self._clear_errors()
        name = self.name_entry.get().strip()
        content = self.text_box.get("1.0", "end-1c").strip()
        note = self.note_entry.get().strip()[:200]
        tags = [t.strip() for t in self.tag_box.get().split(",") if t.strip()]
        favorite = bool(self.fav_var.get())

        ok = True
        if not name:
            self.name_error.configure(text="Toto pole je povinné")
            self.name_entry.configure(border_color=theme.DANGER)
            ok = False
        elif len(name) > 80:
            self.name_error.configure(text="Názov môže mať max 80 znakov")
            self.name_entry.configure(border_color=theme.DANGER)
            ok = False
        if not content:
            self.text_error.configure(text="Toto pole je povinné")
            self.text_box.configure(border_color=theme.DANGER)
            ok = False
        if not ok:
            return

        exclude = self.prompt.id if self.prompt else None
        existing_id = models.prompt_id_by_name(self.ai_id, name, exclude_id=exclude)
        if existing_id is not None:
            if not confirm(
                self, "Duplicitný názov",
                f"Prompt s názvom „{name}“ už existuje. Chceš ho prepísať?",
                ok_text="Prepísať", cancel_text="Premenovať",
            ):
                self.name_entry.configure(border_color=theme.WARNING)
                self.name_entry.focus_set()
                return

        try:
            if existing_id is not None:
                # Prepíš existujúci záznam s rovnakým názvom
                models.update_prompt(existing_id, name, content, tags, note, favorite)
                if self.prompt and self.prompt.id != existing_id:
                    models.delete_prompt(self.prompt.id)
                self.result = existing_id
            elif self.prompt:
                models.update_prompt(self.prompt.id, name, content, tags, note, favorite)
                self.result = self.prompt.id
            else:
                self.result = models.add_prompt(self.ai_id, name, content, tags,
                                                 note, favorite)
        except Exception:  # pragma: no cover
            show_toast(self, "Nepodarilo sa uložiť zmeny, skús to znova",
                       kind="error", duration=6000,
                       action_text="Skúsiť znova", action_command=self._save)
            return
        self.destroy()


# --------------------------------------------------------------------------- #
# Project editor (split view raw / preview)
# --------------------------------------------------------------------------- #
class ProjectEditor(ModalDialog):
    def __init__(self, parent, ai_id: int, project: models.Project | None = None):
        title = "Upraviť projekt" if project else "Nový projekt"
        super().__init__(parent, title, width=1020, height=680, resizable=True)
        self.ai_id = ai_id
        self.project = project
        self._preview_job = None

        root = ctk.CTkFrame(self, fg_color="transparent")
        root.pack(fill="both", expand=True, padx=18, pady=16)
        root.grid_columnconfigure(0, weight=1)
        root.grid_rowconfigure(2, weight=1)

        # --- Header: názov + status + linked ---
        header = ctk.CTkFrame(root, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        self.name_entry = ctk.CTkEntry(
            header, height=40, font=theme.font(16, "bold"), corner_radius=theme.RADIUS,
            fg_color=theme.INPUT_BG, border_color=theme.INPUT_BORDER,
            placeholder_text="Názov projektu",
        )
        self.name_entry.grid(row=0, column=0, sticky="ew", padx=(0, 12))

        self.status_menu = ctk.CTkSegmentedButton(
            header, values=config.PROJECT_STATUSES, font=theme.font(12, "bold"),
            selected_color=theme.get_accent(),
            selected_hover_color=theme.get_accent_hover(),
            unselected_color=theme.INPUT_BG,
        )
        self.status_menu.grid(row=0, column=1, sticky="e")
        self.status_menu.set("Nápad")

        # --- Sub-header: linked prompt + name error ---
        sub = ctk.CTkFrame(root, fg_color="transparent")
        sub.grid(row=1, column=0, sticky="ew", pady=(8, 8))
        sub.grid_columnconfigure(2, weight=1)
        ctk.CTkLabel(sub, text="Prepojený prompt:", font=theme.font(12),
                     text_color=theme.TEXT_MUTED).grid(row=0, column=0, padx=(0, 8))
        self._prompt_map = {"(žiadny)": None}
        for p in models.list_prompts(ai_id, sort="Abecedne"):
            # Unikátny label — duplicitné mená (aj koliziu so sentinelom) rozlíš id
            label = p.name
            if label in self._prompt_map:
                label = f"{p.name} (#{p.id})"
            self._prompt_map[label] = p.id
        self.link_menu = ctk.CTkOptionMenu(
            sub, values=list(self._prompt_map.keys()), font=theme.font(12),
            corner_radius=theme.RADIUS, fg_color=theme.INPUT_BG,
            button_color=theme.get_accent(), button_hover_color=theme.get_accent_hover(),
            dropdown_font=theme.font(12), width=220,
        )
        self.link_menu.grid(row=0, column=1, sticky="w")
        self.link_menu.set("(žiadny)")
        self.name_error = ctk.CTkLabel(sub, text="", font=theme.font(11),
                                       text_color=theme.DANGER)
        self.name_error.grid(row=0, column=2, sticky="e")

        # --- Split: editor | preview ---
        paned = tk.PanedWindow(
            root, orient="horizontal", sashwidth=8, bd=0,
            bg=theme.resolve(theme.BG), sashrelief="flat",
        )
        paned.grid(row=2, column=0, sticky="nsew")

        left = ctk.CTkFrame(paned, fg_color=theme.BG_ELEVATED, corner_radius=theme.RADIUS)
        right = ctk.CTkFrame(paned, fg_color=theme.BG_ELEVATED, corner_radius=theme.RADIUS)
        paned.add(left, minsize=280, stretch="always")
        paned.add(right, minsize=280, stretch="always")

        ctk.CTkLabel(left, text="✍  Markdown", font=theme.font(12, "bold"),
                     text_color=theme.TEXT_MUTED, anchor="w").pack(
            fill="x", padx=12, pady=(10, 4))
        self.editor = ctk.CTkTextbox(
            left, font=theme.mono_font(13), corner_radius=theme.RADIUS_SM,
            fg_color=theme.INPUT_BG, wrap="word",
        )
        self.editor.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        ctk.CTkLabel(right, text="👁  Náhľad", font=theme.font(12, "bold"),
                     text_color=theme.TEXT_MUTED, anchor="w").pack(
            fill="x", padx=12, pady=(10, 4))
        self.preview = self._build_preview(right)

        # --- Footer ---
        footer = ctk.CTkFrame(root, fg_color="transparent")
        footer.grid(row=3, column=0, sticky="ew", pady=(12, 0))
        ctk.CTkLabel(footer, text="Ctrl+Enter uloží · Esc zavrie",
                     font=theme.font(11), text_color=theme.TEXT_FAINT).pack(side="left")
        ctk.CTkButton(
            footer, text="Zrušiť", command=self._maybe_cancel, width=110, height=38,
            fg_color="transparent", border_width=1, border_color=theme.INPUT_BORDER,
            text_color=theme.TEXT, hover_color=theme.CARD_HOVER,
            font=theme.font(13), corner_radius=theme.RADIUS,
        ).pack(side="right", padx=(8, 0))
        ctk.CTkButton(
            footer, text="💾  Uložiť projekt", command=self._save, width=170, height=38,
            fg_color=theme.get_accent(), hover_color=theme.get_accent_hover(),
            text_color="#FFFFFF", font=theme.font(13, "bold"),
            corner_radius=theme.RADIUS,
        ).pack(side="right")

        self.editor.bind("<KeyRelease>", self._on_edit)
        # Widget-level bind má prednosť pred class bindom Text (<Return> by inak
        # vložil nový riadok pred uložením); "break" zastaví propagáciu.
        self.editor.bind("<Control-Return>", self._on_ctrl_enter)
        self.bind("<Control-Return>", lambda e: self._save())
        self.protocol("WM_DELETE_WINDOW", self._maybe_cancel)
        self.bind("<Escape>", lambda e: self._maybe_cancel())

        if project:
            self._prefill(project)
        self._orig_state = self._current_state()
        self.after(80, lambda: self._update_preview())
        self.after(60, self.name_entry.focus_set)

    def _build_preview(self, parent) -> tk.Text:
        wrap = ctk.CTkFrame(parent, fg_color=theme.INPUT_BG, corner_radius=theme.RADIUS_SM)
        wrap.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        text = tk.Text(
            wrap, wrap="word", borderwidth=0, highlightthickness=0,
            bg=theme.resolve(theme.INPUT_BG), fg=theme.resolve(theme.TEXT),
            padx=14, pady=12, spacing2=3, spacing3=3, cursor="arrow",
            insertwidth=0,
        )
        scroll = ctk.CTkScrollbar(wrap, command=text.yview)
        text.configure(yscrollcommand=scroll.set, state="disabled")
        scroll.pack(side="right", fill="y", pady=4)
        text.pack(side="left", fill="both", expand=True, padx=(4, 0), pady=4)
        return text

    def _prefill(self, p: models.Project) -> None:
        self.name_entry.insert(0, p.name)
        self.editor.insert("1.0", p.content_md)
        self.status_menu.set(p.status if p.status in config.PROJECT_STATUSES else "Nápad")
        if p.linked_prompt_id:
            for name, pid in self._prompt_map.items():
                if pid == p.linked_prompt_id:
                    self.link_menu.set(name)
                    break

    def _current_state(self) -> tuple:
        return (
            self.name_entry.get(),
            self.editor.get("1.0", "end-1c"),
            self.status_menu.get(),
            self.link_menu.get(),
        )

    def _has_changes(self) -> bool:
        return self._current_state() != self._orig_state

    def _on_ctrl_enter(self, _event=None) -> str:
        self._save()
        return "break"

    def _on_edit(self, _event=None) -> None:
        if self._preview_job:
            self.after_cancel(self._preview_job)
        self._preview_job = self.after(220, self._update_preview)

    def _update_preview(self) -> None:
        self._preview_job = None
        md_text = self.editor.get("1.0", "end-1c")
        render_markdown(self.preview, md_text, theme.markdown_colors())

    def _save(self) -> None:
        self.name_error.configure(text="")
        self.name_entry.configure(border_color=theme.INPUT_BORDER)
        name = self.name_entry.get().strip()
        content = self.editor.get("1.0", "end-1c")
        status = self.status_menu.get() or "Nápad"
        linked = self._prompt_map.get(self.link_menu.get())

        if not name:
            self.name_error.configure(text="Názov je povinný")
            self.name_entry.configure(border_color=theme.DANGER)
            self.name_entry.focus_set()
            return
        if len(name) > 100:
            self.name_error.configure(text="Max 100 znakov")
            self.name_entry.configure(border_color=theme.DANGER)
            return
        if not content.strip():
            show_toast(self, "MD obsah je povinný", kind="error")
            self.editor.focus_set()
            return

        exclude = self.project.id if self.project else None
        existing_id = models.project_id_by_name(self.ai_id, name, exclude_id=exclude)
        if existing_id is not None:
            if not confirm(
                self, "Duplicitný názov",
                f"Projekt s názvom „{name}“ už existuje. Chceš ho prepísať?",
                ok_text="Prepísať", cancel_text="Premenovať",
            ):
                self.name_entry.configure(border_color=theme.WARNING)
                self.name_entry.focus_set()
                return

        try:
            if existing_id is not None:
                # Prepíš existujúci záznam s rovnakým názvom
                models.update_project(existing_id, name, content, status, linked)
                if self.project and self.project.id != existing_id:
                    models.delete_project(self.project.id)
                self.result = existing_id
            elif self.project:
                models.update_project(self.project.id, name, content, status, linked)
                self.result = self.project.id
            else:
                self.result = models.add_project(self.ai_id, name, content, status, linked)
        except Exception:  # pragma: no cover
            show_toast(self, "Nepodarilo sa uložiť zmeny, skús to znova",
                       kind="error", duration=6000,
                       action_text="Skúsiť znova", action_command=self._save)
            return
        self.destroy()

    def _maybe_cancel(self) -> None:
        if self._has_changes():
            if not confirm(self, "Zahodiť zmeny?",
                           "Máš neuložené zmeny. Naozaj chceš zavrieť editor?",
                           ok_text="Zahodiť", cancel_text="Späť", danger=True):
                return
        self._cancel()


# --------------------------------------------------------------------------- #
# Platform dialóg (custom AI)
# --------------------------------------------------------------------------- #
class PlatformDialog(ModalDialog):
    def __init__(self, parent, platform: models.Platform | None = None):
        title = "Upraviť AI" if platform else "Pridať vlastné AI"
        super().__init__(parent, title, width=460, height=440)
        self.platform = platform
        self._color = platform.color if platform else theme.get_accent()

        root = ctk.CTkFrame(self, fg_color="transparent")
        root.pack(fill="both", expand=True, padx=24, pady=20)
        root.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(root, text=title, font=theme.font(18, "bold"),
                     text_color=theme.TEXT, anchor="w").grid(
            row=0, column=0, sticky="ew", pady=(0, 14))

        FieldLabel(root, "Názov", required=True).grid(row=1, column=0, sticky="w")
        self.name_entry = ctk.CTkEntry(
            root, height=38, font=theme.font(13), corner_radius=theme.RADIUS,
            fg_color=theme.INPUT_BG, border_color=theme.INPUT_BORDER,
            placeholder_text="napr. DeepSeek",
        )
        self.name_entry.grid(row=2, column=0, sticky="ew", pady=(4, 2))
        self.name_error = ctk.CTkLabel(root, text="", font=theme.font(11),
                                       text_color=theme.DANGER, anchor="w")
        self.name_error.grid(row=3, column=0, sticky="w")

        # Farba
        FieldLabel(root, "Farba").grid(row=4, column=0, sticky="w", pady=(8, 0))
        color_row = ctk.CTkFrame(root, fg_color="transparent")
        color_row.grid(row=5, column=0, sticky="ew", pady=(4, 0))
        self.swatch = ctk.CTkFrame(color_row, width=38, height=38,
                                   corner_radius=theme.RADIUS_SM, fg_color=self._color)
        self.swatch.pack(side="left")
        self.swatch.pack_propagate(False)
        ctk.CTkButton(
            color_row, text="Vybrať farbu…", command=self._pick_color, height=38,
            fg_color=theme.INPUT_BG, hover_color=theme.CARD_HOVER,
            text_color=theme.TEXT, border_width=1, border_color=theme.INPUT_BORDER,
            font=theme.font(13), corner_radius=theme.RADIUS,
        ).pack(side="left", padx=(10, 0))
        self.color_label = ctk.CTkLabel(color_row, text=self._color,
                                        font=theme.mono_font(12),
                                        text_color=theme.TEXT_MUTED)
        self.color_label.pack(side="left", padx=(10, 0))

        # Ikona / emoji
        FieldLabel(root, "Ikona (emoji)").grid(row=6, column=0, sticky="w", pady=(10, 0))
        self.icon_entry = ctk.CTkEntry(
            root, height=38, font=theme.font(16), corner_radius=theme.RADIUS,
            fg_color=theme.INPUT_BG, border_color=theme.INPUT_BORDER, width=70,
        )
        self.icon_entry.grid(row=7, column=0, sticky="w", pady=(4, 4))

        emoji_wrap = ctk.CTkFrame(root, fg_color="transparent")
        emoji_wrap.grid(row=8, column=0, sticky="ew", pady=(2, 0))
        for i, emo in enumerate(config.EMOJI_CHOICES):
            b = ctk.CTkButton(
                emoji_wrap, text=emo, width=32, height=30, font=theme.font(15),
                fg_color=theme.INPUT_BG, hover_color=theme.CARD_HOVER,
                corner_radius=theme.RADIUS_SM,
                command=lambda e=emo: self._set_emoji(e),
            )
            b.grid(row=i // 8, column=i % 8, padx=2, pady=2)

        # Tlačidlá
        btns = ctk.CTkFrame(root, fg_color="transparent")
        btns.grid(row=9, column=0, sticky="ew", pady=(20, 0))
        ctk.CTkButton(
            btns, text="Zrušiť", command=self._cancel, width=110, height=38,
            fg_color="transparent", border_width=1, border_color=theme.INPUT_BORDER,
            text_color=theme.TEXT, hover_color=theme.CARD_HOVER,
            font=theme.font(13), corner_radius=theme.RADIUS,
        ).pack(side="right", padx=(8, 0))
        ctk.CTkButton(
            btns, text="Uložiť", command=self._save, width=130, height=38,
            fg_color=theme.get_accent(), hover_color=theme.get_accent_hover(),
            text_color="#FFFFFF", font=theme.font(13, "bold"),
            corner_radius=theme.RADIUS,
        ).pack(side="right")

        self.bind("<Control-Return>", lambda e: self._save())
        if platform:
            self.name_entry.insert(0, platform.name)
            self.icon_entry.insert(0, platform.icon or "")
        self.after(60, self.name_entry.focus_set)

    def _set_emoji(self, emo: str) -> None:
        self.icon_entry.delete(0, "end")
        self.icon_entry.insert(0, emo)

    def _pick_color(self) -> None:
        result = colorchooser.askcolor(color=self._color, parent=self,
                                       title="Vyber farbu AI")
        if result and result[1]:
            self._color = result[1].upper()
            self.swatch.configure(fg_color=self._color)
            self.color_label.configure(text=self._color)

    def _save(self) -> None:
        self.name_error.configure(text="")
        self.name_entry.configure(border_color=theme.INPUT_BORDER)
        name = self.name_entry.get().strip()
        icon = self.icon_entry.get().strip()
        if not name:
            self.name_error.configure(text="Názov je povinný")
            self.name_entry.configure(border_color=theme.DANGER)
            return
        exclude = self.platform.id if self.platform else None
        if models.platform_name_exists(name, exclude_id=exclude):
            self.name_error.configure(text="AI s týmto názvom už existuje")
            self.name_entry.configure(border_color=theme.DANGER)
            return
        try:
            if self.platform:
                models.update_platform(self.platform.id, name, self._color, icon)
                self.result = self.platform.id
            else:
                self.result = models.add_platform(name, self._color, icon, is_custom=True)
        except Exception:  # pragma: no cover
            show_toast(self, "Nepodarilo sa uložiť zmeny, skús to znova",
                       kind="error", duration=6000,
                       action_text="Skúsiť znova", action_command=self._save)
            return
        self.destroy()
