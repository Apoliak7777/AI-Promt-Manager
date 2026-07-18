"""Nastavenia — vzhľad, dáta, zálohovanie, správa AI, o aplikácii."""
from __future__ import annotations

import os
import sqlite3
import subprocess
import sys
import webbrowser
from pathlib import Path
from tkinter import colorchooser, filedialog

import customtkinter as ctk

from app import config
from app.db import models
from app.ui import theme
from app.ui.components import IconButton, color_dot, confirm, show_toast
from app.utils import backup

ACCENT_PRESETS = ["#7C5CFC", "#4C8DFF", "#2FB86B", "#E0A800",
                  "#FF7A59", "#E5484D", "#D053C4", "#20808D"]


class SettingsView(ctk.CTkScrollableFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller

        ctk.CTkLabel(self, text="⚙️  Nastavenia", font=theme.font(20, "bold"),
                     text_color=theme.TEXT, anchor="w").pack(
            fill="x", padx=24, pady=(20, 12))

        self._appearance_section()
        self._data_section()
        self._backup_section()
        self._platforms_section()
        self._about_section()

    # ------------------------------------------------------------------ #
    def _card(self, title: str, subtitle: str = "") -> ctk.CTkFrame:
        card = ctk.CTkFrame(self, fg_color=theme.CARD, corner_radius=theme.RADIUS,
                            border_width=1, border_color=theme.CARD_BORDER)
        card.pack(fill="x", padx=24, pady=8)
        ctk.CTkLabel(card, text=title, font=theme.font(15, "bold"),
                     text_color=theme.TEXT, anchor="w").pack(
            fill="x", padx=18, pady=(14, 0))
        if subtitle:
            ctk.CTkLabel(card, text=subtitle, font=theme.font(12),
                         text_color=theme.TEXT_MUTED, anchor="w").pack(
                fill="x", padx=18, pady=(2, 0))
        return card

    # ------------------------------------------------------------------ #
    def _appearance_section(self) -> None:
        card = self._card("Vzhľad", "Farebný režim a akcentová farba aplikácie.")
        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=18, pady=(12, 6))
        ctk.CTkLabel(row, text="Režim:", font=theme.font(13),
                     text_color=theme.TEXT).pack(side="left", padx=(0, 12))
        mode_map = {"dark": "Tmavý", "light": "Svetlý", "system": "Systémový"}
        inv_map = {v: k for k, v in mode_map.items()}
        seg = ctk.CTkSegmentedButton(
            row, values=list(mode_map.values()), font=theme.font(12, "bold"),
            selected_color=theme.get_accent(),
            selected_hover_color=theme.get_accent_hover(),
            command=lambda v: self.controller.set_appearance(inv_map[v]),
        )
        seg.pack(side="left")
        current = models.get_setting("appearance_mode", "dark")
        seg.set(mode_map.get(current, "Tmavý"))

        # Accent
        acc_label = ctk.CTkFrame(card, fg_color="transparent")
        acc_label.pack(fill="x", padx=18, pady=(8, 4))
        ctk.CTkLabel(acc_label, text="Akcentová farba:", font=theme.font(13),
                     text_color=theme.TEXT).pack(side="left")
        swatches = ctk.CTkFrame(card, fg_color="transparent")
        swatches.pack(fill="x", padx=18, pady=(0, 14))
        for hexc in ACCENT_PRESETS:
            b = ctk.CTkButton(
                swatches, text="", width=30, height=30, corner_radius=15,
                fg_color=hexc, hover_color=theme.shade(hexc, -0.15),
                border_width=2,
                border_color=(theme.TEXT if hexc == theme.get_accent() else hexc),
                command=lambda c=hexc: self.controller.set_accent(c),
            )
            b.pack(side="left", padx=3)
        ctk.CTkButton(
            swatches, text="Vlastná…", width=90, height=30, font=theme.font(12),
            fg_color=theme.INPUT_BG, hover_color=theme.CARD_HOVER,
            text_color=theme.TEXT, corner_radius=theme.RADIUS,
            command=self._pick_accent,
        ).pack(side="left", padx=(10, 0))

    def _pick_accent(self) -> None:
        result = colorchooser.askcolor(color=theme.get_accent(),
                                       parent=self.winfo_toplevel(),
                                       title="Vyber akcentovú farbu")
        if result and result[1]:
            self.controller.set_accent(result[1].upper())

    # ------------------------------------------------------------------ #
    def _data_section(self) -> None:
        card = self._card("Dáta", "Umiestnenie databázy s tvojimi promptami a projektmi.")
        path_row = ctk.CTkFrame(card, fg_color="transparent")
        path_row.pack(fill="x", padx=18, pady=(10, 4))
        ctk.CTkLabel(path_row, text=str(config.get_db_path()), font=theme.mono_font(11),
                     text_color=theme.TEXT_MUTED, anchor="w", wraplength=600,
                     justify="left").pack(fill="x")

        btns = ctk.CTkFrame(card, fg_color="transparent")
        btns.pack(fill="x", padx=18, pady=(6, 14))
        ctk.CTkButton(
            btns, text="📂  Otvoriť priečinok s dátami", command=self._open_data_dir,
            height=34, font=theme.font(12), fg_color=theme.INPUT_BG,
            hover_color=theme.CARD_HOVER, text_color=theme.TEXT,
            corner_radius=theme.RADIUS,
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            btns, text="Zmeniť umiestnenie…", command=self._change_db_dir,
            height=34, font=theme.font(12), fg_color=theme.INPUT_BG,
            hover_color=theme.CARD_HOVER, text_color=theme.TEXT,
            corner_radius=theme.RADIUS,
        ).pack(side="left")

    def _open_data_dir(self) -> None:
        folder = config.get_db_path().parent
        folder.mkdir(parents=True, exist_ok=True)
        _open_folder(folder)

    def _change_db_dir(self) -> None:
        folder = filedialog.askdirectory(
            parent=self.winfo_toplevel(), title="Vyber priečinok pre databázu")
        if not folder:
            return
        old_path = config.get_db_path()
        new_path = Path(folder) / "prompts.db"
        if new_path == old_path:
            return
        if new_path.exists():
            if not confirm(self.winfo_toplevel(), "Použiť existujúcu databázu?",
                           "V priečinku už existuje databáza. Použiť ju?",
                           ok_text="Použiť", cancel_text="Zrušiť"):
                return
        elif old_path.exists():
            try:
                src = sqlite3.connect(str(old_path))
                dst = sqlite3.connect(str(new_path))
                src.backup(dst)
                dst.close()
                src.close()
            except Exception as exc:
                show_toast(self.winfo_toplevel(),
                           f"Presun databázy zlyhal: {exc}", "error")
                return
        config.set_db_path(new_path)
        self.controller.reload_after_db_change()
        show_toast(self.winfo_toplevel(),
                   "Umiestnenie databázy zmenené ✓", "success")

    # ------------------------------------------------------------------ #
    def _backup_section(self) -> None:
        card = self._card("Zálohovanie", "Export a import všetkých dát ako .zip.")
        btns = ctk.CTkFrame(card, fg_color="transparent")
        btns.pack(fill="x", padx=18, pady=(10, 6))
        ctk.CTkButton(
            btns, text="⬇️  Exportovať zálohu (.zip)", command=self._export,
            height=36, font=theme.font(13, "bold"), fg_color=theme.get_accent(),
            hover_color=theme.get_accent_hover(), text_color="#FFFFFF",
            corner_radius=theme.RADIUS,
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            btns, text="⬆️  Importovať zálohu", command=self._import,
            height=36, font=theme.font(13), fg_color=theme.INPUT_BG,
            hover_color=theme.CARD_HOVER, text_color=theme.TEXT,
            corner_radius=theme.RADIUS,
        ).pack(side="left")

        auto_row = ctk.CTkFrame(card, fg_color="transparent")
        auto_row.pack(fill="x", padx=18, pady=(6, 14))
        ctk.CTkLabel(auto_row, text="Automatická záloha:", font=theme.font(13),
                     text_color=theme.TEXT).pack(side="left", padx=(0, 12))
        auto_map = {"off": "Vypnuté", "daily": "Denne", "weekly": "Týždenne"}
        inv = {v: k for k, v in auto_map.items()}
        seg = ctk.CTkSegmentedButton(
            auto_row, values=list(auto_map.values()), font=theme.font(12, "bold"),
            selected_color=theme.get_accent(),
            selected_hover_color=theme.get_accent_hover(),
            command=lambda v: models.set_setting("auto_backup", inv[v]),
        )
        seg.pack(side="left")
        seg.set(auto_map.get(models.get_setting("auto_backup", "off"), "Vypnuté"))

    def _export(self) -> None:
        path = filedialog.asksaveasfilename(
            parent=self.winfo_toplevel(), defaultextension=".zip",
            initialfile="ai_prompt_manager_zaloha.zip",
            title="Uložiť zálohu", filetypes=[("ZIP záloha", "*.zip")])
        if not path:
            return
        try:
            backup.export_backup(path)
            self.controller.toast("Záloha vytvorená ✓", "success")
        except Exception as exc:
            self.controller.toast(f"Export zlyhal: {exc}", "error")

    def _import(self) -> None:
        path = filedialog.askopenfilename(
            parent=self.winfo_toplevel(), title="Vyber zálohu (.zip)",
            filetypes=[("ZIP záloha", "*.zip"), ("Všetky súbory", "*.*")])
        if not path:
            return
        ok, msg, manifest = backup.validate_backup(path)
        if not ok:
            self.controller.toast(msg, "error")
            return
        counts = (manifest or {}).get("counts", {})
        detail = (f"Obsahuje {counts.get('prompts', '?')} promptov a "
                  f"{counts.get('projects', '?')} projektov.\n"
                  "Dáta sa PRIDAJÚ k existujúcim (nič sa nezmaže).")
        if not confirm(self.winfo_toplevel(), "Importovať zálohu?", detail,
                       ok_text="Importovať", cancel_text="Zrušiť"):
            return
        try:
            res = backup.import_backup(path, mode="merge")
            self.controller.reload_after_db_change()
            self.controller.toast(
                f"Naimportované: {res['prompts']} promptov, "
                f"{res['projects']} projektov ✓", "success")
        except Exception as exc:
            self.controller.toast(f"Import zlyhal: {exc}", "error")

    # ------------------------------------------------------------------ #
    def _platforms_section(self) -> None:
        card = self._card("AI platformy", "Správa vlastných AI (predvolené sa nedajú zmazať).")
        holder = ctk.CTkFrame(card, fg_color="transparent")
        holder.pack(fill="x", padx=18, pady=(8, 6))
        customs = [p for p in models.list_platforms() if p.is_custom]
        if not customs:
            ctk.CTkLabel(holder, text="Zatiaľ nemáš žiadne vlastné AI.",
                         font=theme.font(12), text_color=theme.TEXT_FAINT,
                         anchor="w").pack(fill="x")
        for plat in customs:
            row = ctk.CTkFrame(holder, fg_color=theme.INPUT_BG,
                               corner_radius=theme.RADIUS_SM)
            row.pack(fill="x", pady=3)
            color_dot(row, plat.color, 12).pack(side="left", padx=(12, 8), pady=8)
            ctk.CTkLabel(row, text=f"{plat.icon or ''} {plat.name}".strip(),
                         font=theme.font(13), text_color=theme.TEXT).pack(
                side="left", pady=8)
            IconButton(row, "🗑️", tooltip="Zmazať AI", hover_color=theme.DANGER,
                       command=lambda p=plat: self.controller.delete_platform(p)).pack(
                side="right", padx=(0, 8))
            IconButton(row, "✏️", tooltip="Upraviť AI",
                       command=lambda p=plat: self.controller.edit_platform(p)).pack(
                side="right", padx=2)
        ctk.CTkButton(
            card, text="➕  Pridať vlastné AI", command=self.controller.open_add_platform,
            height=34, font=theme.font(12), fg_color=theme.INPUT_BG,
            hover_color=theme.CARD_HOVER, text_color=theme.TEXT,
            corner_radius=theme.RADIUS,
        ).pack(anchor="w", padx=18, pady=(6, 14))

    # ------------------------------------------------------------------ #
    def _about_section(self) -> None:
        card = self._card("O aplikácii")
        ctk.CTkLabel(card, text=f"{config.APP_NAME}  ·  verzia {config.APP_VERSION}",
                     font=theme.font(13), text_color=theme.TEXT, anchor="w").pack(
            fill="x", padx=18, pady=(8, 2))
        ctk.CTkLabel(
            card, text="Lokálna appka na organizovanie AI promptov a projektov. "
            "Všetky dáta ostávajú na tvojom počítači (SQLite).",
            font=theme.font(12), text_color=theme.TEXT_MUTED, anchor="w",
            wraplength=620, justify="left").pack(fill="x", padx=18, pady=(0, 8))
        for ver, items in config.CHANGELOG.items():
            ctk.CTkLabel(card, text=f"Verzia {ver}", font=theme.font(12, "bold"),
                         text_color=theme.TEXT, anchor="w").pack(
                fill="x", padx=18, pady=(4, 0))
            ctk.CTkLabel(card, text="\n".join(f"• {item}" for item in items),
                         font=theme.font(12), text_color=theme.TEXT_MUTED,
                         anchor="w", wraplength=620, justify="left").pack(
                fill="x", padx=18, pady=(0, 4))
        ctk.CTkButton(
            card, text="🔗  GitHub repozitár", command=lambda: webbrowser.open(config.GITHUB_URL),
            height=32, font=theme.font(12), fg_color="transparent",
            hover_color=theme.CARD_HOVER, text_color=theme.get_accent(),
            corner_radius=theme.RADIUS, anchor="w",
        ).pack(anchor="w", padx=14, pady=(0, 14))


def _open_folder(path) -> None:
    try:
        if sys.platform == "win32":
            os.startfile(str(path))  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.run(["open", str(path)], check=False)
        else:
            subprocess.run(["xdg-open", str(path)], check=False)
    except Exception:
        pass
