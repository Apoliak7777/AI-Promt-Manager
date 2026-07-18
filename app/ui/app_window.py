"""Hlavné okno + kontrolér — spája sidebar, obsah, klávesové skratky a routing."""
from __future__ import annotations

import tkinter as tk
import webbrowser

import customtkinter as ctk

from app import config
from app.db import database, models
from app.ui import theme
from app.ui.components import confirm, show_toast
from app.ui.dialogs import PlatformDialog
from app.ui.project_view import ProjectView
from app.ui.prompt_view import PromptView
from app.ui.search_view import SearchResultsView
from app.ui.settings_view import SettingsView
from app.ui.sidebar import Sidebar
from app.ui.stats_view import StatsView


class AppWindow(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Načítaj uložené nastavenia témy PRED stavbou UI
        theme.set_accent(models.get_setting("accent_color", config.DEFAULT_ACCENT))
        theme.apply_appearance(models.get_setting("appearance_mode", "dark"))

        self.title(config.APP_TITLE)
        self.geometry("1140x720")
        self.minsize(820, 560)
        self.configure(fg_color=theme.BG)

        self.mode = "ai"
        self.current_ai_id: int | None = None
        self.current_tab = "prompts"
        self.current_view = None
        self._last_query = ""
        self._seg = None
        self.body_frame = None

        # Layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar = Sidebar(self, controller=self)
        self.sidebar.grid(row=0, column=0, sticky="nswe")

        self.content = ctk.CTkFrame(self, fg_color=theme.BG, corner_radius=0)
        self.content.grid(row=0, column=1, sticky="nswe")
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(1, weight=1)

        self.sidebar.refresh()
        self._bind_shortcuts()
        self._load_initial_ai()

    # ------------------------------------------------------------------ #
    # Inicializácia
    # ------------------------------------------------------------------ #
    def _load_initial_ai(self) -> None:
        platforms = models.list_platforms()
        if not platforms:
            self._clear_content()
            ctk.CTkLabel(self.content, text="Žiadne AI platformy.",
                         font=theme.font(14), text_color=theme.TEXT_MUTED).grid(
                row=0, column=0, pady=40)
            return
        last = models.get_setting("last_ai_id", "")
        target = None
        if last and last.isdigit():
            target = next((p for p in platforms if p.id == int(last)), None)
        self.select_ai((target or platforms[0]).id)

    def _bind_shortcuts(self) -> None:
        self.bind("<Control-n>", lambda e: self._sc_new_prompt())
        self.bind("<Control-N>", lambda e: self._sc_new_prompt())
        self.bind("<Control-Shift-N>", lambda e: self._sc_new_project())
        self.bind("<Control-Shift-n>", lambda e: self._sc_new_project())
        self.bind("<Control-f>", lambda e: self.sidebar.focus_search())
        self.bind("<Control-F>", lambda e: self.sidebar.focus_search())
        self.bind("<Control-b>", lambda e: self._toggle_theme())
        self.bind("<Control-B>", lambda e: self._toggle_theme())
        self.bind("<Control-d>", lambda e: self._sc_duplicate())
        self.bind("<Control-D>", lambda e: self._sc_duplicate())
        self.bind("<Delete>", self._sc_delete)

    def _is_text_focus(self) -> bool:
        w = self.focus_get()
        if w is None:
            return False
        try:
            return w.winfo_class() in ("Entry", "Text", "TEntry", "TCombobox")
        except Exception:
            return False

    # ------------------------------------------------------------------ #
    # Content helpers
    # ------------------------------------------------------------------ #
    def _clear_content(self) -> None:
        for child in self.content.winfo_children():
            child.destroy()
        self.current_view = None
        self._seg = None
        self.body_frame = None

    # ------------------------------------------------------------------ #
    # Routing
    # ------------------------------------------------------------------ #
    def select_ai(self, ai_id: int) -> None:
        self.mode = "ai"
        self.current_ai_id = ai_id
        models.set_setting("last_ai_id", str(ai_id))
        self.sidebar.set_active(ai_id)
        self._render_ai()

    def _render_ai(self) -> None:
        self._clear_content()
        plat = models.get_platform(self.current_ai_id)
        if plat is None:
            self._load_initial_ai()
            return

        # Header
        header = ctk.CTkFrame(self.content, fg_color=theme.TOPBAR_BG, corner_radius=0,
                              height=64)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_propagate(False)
        header.grid_columnconfigure(1, weight=1)

        from app.ui.components import color_dot
        title_wrap = ctk.CTkFrame(header, fg_color="transparent")
        title_wrap.grid(row=0, column=0, sticky="w", padx=20, pady=14)
        color_dot(title_wrap, plat.color, 16).pack(side="left", padx=(0, 10))
        ctk.CTkLabel(title_wrap, text=plat.name, font=theme.font(19, "bold"),
                     text_color=theme.TEXT).pack(side="left")

        self._seg = ctk.CTkSegmentedButton(
            header, values=["Prompty", "Projekty"], font=theme.font(13, "bold"),
            selected_color=theme.get_accent(),
            selected_hover_color=theme.get_accent_hover(),
            unselected_color=theme.INPUT_BG, height=36,
            command=self._on_tab_change,
        )
        self._seg.grid(row=0, column=2, sticky="e", padx=20)
        self._seg.set("Prompty" if self.current_tab == "prompts" else "Projekty")

        ctk.CTkFrame(self.content, height=1, fg_color=theme.DIVIDER).grid(
            row=0, column=0, sticky="sew")

        # Body
        self.body_frame = ctk.CTkFrame(self.content, fg_color="transparent")
        self.body_frame.grid(row=1, column=0, sticky="nswe")
        self.body_frame.grid_columnconfigure(0, weight=1)
        self.body_frame.grid_rowconfigure(0, weight=1)
        self._mount_body()

    def _on_tab_change(self, value: str) -> None:
        self.current_tab = "prompts" if value == "Prompty" else "projects"
        self._mount_body()

    def _mount_body(self) -> None:
        if self.body_frame is None:
            return
        for child in self.body_frame.winfo_children():
            child.destroy()
        if self.current_tab == "prompts":
            self.current_view = PromptView(self.body_frame, self, self.current_ai_id)
        else:
            self.current_view = ProjectView(self.body_frame, self, self.current_ai_id)
        self.current_view.grid(row=0, column=0, sticky="nswe")

    # ------------------------------------------------------------------ #
    def global_search(self, query: str) -> None:
        self._last_query = query
        if not query:
            if self.mode == "search":
                if self.current_ai_id is not None:
                    self.select_ai(self.current_ai_id)
                else:
                    self._load_initial_ai()
            return
        self.mode = "search"
        self._clear_content()
        view = SearchResultsView(self.content, self, query)
        view.grid(row=0, column=0, rowspan=2, sticky="nswe")

    def goto_prompt(self, ai_id: int) -> None:
        self.sidebar.clear_search()
        self.current_tab = "prompts"
        self.select_ai(ai_id)

    def goto_project(self, ai_id: int) -> None:
        self.sidebar.clear_search()
        self.current_tab = "projects"
        self.select_ai(ai_id)

    def open_settings(self) -> None:
        self.mode = "settings"
        self._clear_content()
        view = SettingsView(self.content, self)
        view.grid(row=0, column=0, rowspan=2, sticky="nswe")

    def open_stats(self) -> None:
        self.mode = "stats"
        self._clear_content()
        view = StatsView(self.content, self)
        view.grid(row=0, column=0, rowspan=2, sticky="nswe")

    # ------------------------------------------------------------------ #
    # Platformy
    # ------------------------------------------------------------------ #
    def open_add_platform(self) -> None:
        result = PlatformDialog(self).show()
        if result:
            self.sidebar.refresh(self.current_ai_id if self.mode == "ai" else None)
            self._refresh_current_mode()
            self.toast("AI pridané ✓", "success")

    def edit_platform(self, platform: models.Platform) -> None:
        fresh = models.get_platform(platform.id)
        if not fresh:
            return
        result = PlatformDialog(self, platform=fresh).show()
        if result:
            self.sidebar.refresh(self.current_ai_id if self.mode == "ai" else None)
            self._refresh_current_mode()
            self.toast("AI upravené ✓", "success")

    def delete_platform(self, platform: models.Platform) -> None:
        if not platform.is_custom:
            self.toast("Predvolené AI sa nedá zmazať", "info")
            return
        n = models.count_prompts(platform.id) + models.count_projects(platform.id)
        extra = f"\nZmaže sa aj {n} súvisiacich promptov/projektov." if n else ""
        if not confirm(self, "Zmazať AI?",
                       f"Naozaj chceš zmazať AI „{platform.name}“?{extra}",
                       ok_text="Zmazať", cancel_text="Zrušiť", danger=True):
            return
        models.delete_platform(platform.id)
        if self.current_ai_id == platform.id:
            self.current_ai_id = None
        self.sidebar.refresh(self.current_ai_id if self.mode == "ai" else None)
        if self.current_ai_id is None:
            self._load_initial_ai()
        else:
            self._refresh_current_mode()
        self.toast("AI zmazané", "info")

    def launch_ai(self, platform: models.Platform) -> None:
        url = config.AI_LAUNCH_URLS.get(platform.name)
        if url:
            webbrowser.open(url)
        else:
            self.toast("Toto AI nemá priradený odkaz", "info")

    # ------------------------------------------------------------------ #
    # Téma
    # ------------------------------------------------------------------ #
    def set_appearance(self, mode: str) -> None:
        models.set_setting("appearance_mode", mode)
        theme.apply_appearance(mode)
        self._rebuild_all()

    def set_accent(self, hex_color: str) -> None:
        theme.set_accent(hex_color)
        models.set_setting("accent_color", hex_color)
        self._rebuild_all()

    def _toggle_theme(self) -> None:
        if self._is_text_focus():
            return
        new_mode = "light" if theme.is_dark() else "dark"
        self.set_appearance(new_mode)

    def _rebuild_all(self) -> None:
        self.configure(fg_color=theme.BG)
        self.content.configure(fg_color=theme.BG)
        self._rebuild_sidebar()
        self._refresh_current_mode()

    def _rebuild_sidebar(self) -> None:
        self.sidebar.destroy()
        self.sidebar = Sidebar(self, controller=self)
        self.sidebar.grid(row=0, column=0, sticky="nswe")
        self.sidebar.refresh(self.current_ai_id if self.mode == "ai" else None)

    def _refresh_current_mode(self) -> None:
        if self.mode == "ai" and self.current_ai_id is not None:
            self._render_ai()
        elif self.mode == "settings":
            self.open_settings()
        elif self.mode == "stats":
            self.open_stats()
        elif self.mode == "search":
            self.global_search(self._last_query)
        else:
            self._load_initial_ai()

    def reload_after_db_change(self) -> None:
        database.init_db()
        theme.set_accent(models.get_setting("accent_color", config.DEFAULT_ACCENT))
        self.sidebar.refresh()
        self.current_ai_id = None
        self._load_initial_ai()

    # ------------------------------------------------------------------ #
    # Utility pre views
    # ------------------------------------------------------------------ #
    def toast(self, message: str, kind: str = "info") -> None:
        show_toast(self, message, kind)

    def refresh_sidebar_counts(self) -> None:
        self.sidebar.update_counts()

    def status_color(self, status: str) -> str:
        return config.STATUS_COLORS.get(status, theme.resolve(theme.TEXT_MUTED))

    # ------------------------------------------------------------------ #
    # Skratky
    # ------------------------------------------------------------------ #
    def _ensure_ai_tab(self, tab: str) -> bool:
        if self.current_ai_id is None:
            platforms = models.list_platforms()
            if not platforms:
                return False
            self.current_ai_id = platforms[0].id
        if self.mode != "ai" or self.current_tab != tab:
            self.current_tab = tab
            self.select_ai(self.current_ai_id)
        return True

    def _sc_new_prompt(self) -> None:
        if self._is_text_focus():
            return
        if self._ensure_ai_tab("prompts") and isinstance(self.current_view, PromptView):
            self.current_view.new_prompt()

    def _sc_new_project(self) -> None:
        if self._is_text_focus():
            return
        if self._ensure_ai_tab("projects") and isinstance(self.current_view, ProjectView):
            self.current_view.new_project()

    def _sc_duplicate(self) -> None:
        if self._is_text_focus():
            return
        if self.mode == "ai" and hasattr(self.current_view, "duplicate_selected"):
            self.current_view.duplicate_selected()

    def _sc_delete(self, _event=None) -> None:
        if self._is_text_focus():
            return
        if self.mode == "ai" and hasattr(self.current_view, "delete_selected"):
            self.current_view.delete_selected()

    # ------------------------------------------------------------------ #
    def set_app_icon(self, ico_path) -> None:
        try:
            self.iconbitmap(str(ico_path))
        except Exception:
            pass
