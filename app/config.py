"""Aplikačná konfigurácia — cesty, konštanty, default hodnoty.

DB sa neukladá do inštalačného priečinka (kvôli právam na zápis), ale do
používateľského dátového priečinka (``%APPDATA%\\AIPromptManager`` na Windows).
Cesta k DB je uložená v malom ``config.json`` (bootstrap config), aby ju bolo
možné zmeniť v Nastaveniach bez chicken-egg problému (cesta k DB nemôže byť
uložená v samotnej DB).
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# --------------------------------------------------------------------------- #
# Metadáta aplikácie
# --------------------------------------------------------------------------- #
APP_NAME = "AI Prompt Manager"
APP_TITLE = "🧠 AI Prompt Manager"
APP_VERSION = "1.0.0"
GITHUB_URL = "https://github.com/Apoliak7777/AI-Promt-Manager"

# Changelog — renderuje sa v Nastaveniach (settings_view)
CHANGELOG: dict[str, list[str]] = {
    "1.0.0": [
        "Prvé vydanie — prompty, projekty, vlastné AI platformy, Markdown editor, zálohovanie (.zip), dark/light režim, klávesové skratky."
    ]
}

# --------------------------------------------------------------------------- #
# Cesty
# --------------------------------------------------------------------------- #
def _base_config_dir() -> Path:
    """Priečinok pre používateľské dáta aplikácie."""
    if sys.platform == "win32":
        root = os.environ.get("APPDATA") or str(Path.home())
        return Path(root) / "AIPromptManager"
    # Fallback pre iné OS (dev/test)
    xdg = os.environ.get("XDG_DATA_HOME")
    if xdg:
        return Path(xdg) / "AIPromptManager"
    return Path.home() / ".aipromptmanager"


CONFIG_DIR: Path = _base_config_dir()
CONFIG_FILE: Path = CONFIG_DIR / "config.json"
DEFAULT_DB_PATH: Path = CONFIG_DIR / "prompts.db"


def _ensure_config_dir() -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def _load_bootstrap() -> dict:
    try:
        if CONFIG_FILE.exists():
            data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
    except (OSError, ValueError):
        pass
    return {}


def _save_bootstrap(data: dict) -> None:
    _ensure_config_dir()
    # Atomický zápis — najprv do temp súboru, potom os.replace (žiadny polovičný config.json)
    tmp = CONFIG_FILE.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, CONFIG_FILE)


def get_db_path() -> Path:
    """Aktuálna cesta k SQLite databáze."""
    data = _load_bootstrap()
    raw = data.get("db_path")
    if raw:
        return Path(raw)
    return DEFAULT_DB_PATH


def set_db_path(path: str | os.PathLike) -> None:
    """Nastaví novú cestu k databáze (uloží do bootstrap configu)."""
    data = _load_bootstrap()
    data["db_path"] = str(Path(path))
    _save_bootstrap(data)


def resource_path(relative: str) -> Path:
    """Cesta k priloženému zdroju — funguje v dev aj v PyInstaller (_MEIPASS) exe."""
    base = getattr(sys, "_MEIPASS", None)
    if base:
        return Path(base) / relative
    return Path(__file__).resolve().parent.parent / relative


# --------------------------------------------------------------------------- #
# Default AI platformy  (name, color, icon)
# --------------------------------------------------------------------------- #
DEFAULT_PLATFORMS: list[tuple[str, str, str]] = [
    ("ChatGPT", "#10A37F", "🟢"),
    ("Claude", "#D97757", "🟠"),
    ("Gemini", "#4285F4", "🔵"),
    ("Grok", "#1A1A1A", "⚫"),
    ("Perplexity", "#20808D", "🩵"),
    ("GitHub Copilot", "#8957E5", "🟣"),
    ("Mistral", "#FF7000", "🔴"),
    ("Llama / Ollama", "#8B5E3C", "🟤"),
]

# Rýchly odkaz na oficiálnu web appku daného AI (AI Quick-Launch)
AI_LAUNCH_URLS: dict[str, str] = {
    "ChatGPT": "https://chat.openai.com",
    "Claude": "https://claude.ai",
    "Gemini": "https://gemini.google.com",
    "Grok": "https://grok.com",
    "Perplexity": "https://www.perplexity.ai",
    "GitHub Copilot": "https://github.com/copilot",
    "Mistral": "https://chat.mistral.ai",
    "Llama / Ollama": "https://ollama.com",
}

# --------------------------------------------------------------------------- #
# Číselníky
# --------------------------------------------------------------------------- #
DEFAULT_TAGS: list[str] = ["copywriting", "kód", "analýza", "obrázky", "iné"]

PROJECT_STATUSES: list[str] = ["Nápad", "V procese", "Hotovo"]

STATUS_COLORS: dict[str, str] = {
    "Nápad": "#8A8A9E",      # šedá
    "V procese": "#E0A800",  # žltá
    "Hotovo": "#2FB86B",     # zelená
}

SORT_OPTIONS: list[str] = ["Najnovšie", "Najstaršie", "Obľúbené prvé", "Abecedne"]

# Emoji ponuka pre custom AI (jednoduchý picker)
EMOJI_CHOICES: list[str] = [
    "🤖", "🧠", "✨", "💡", "🚀", "⚡", "🔮", "🎯",
    "🟢", "🟠", "🔵", "🟣", "🔴", "🟡", "⚫", "⚪",
    "🐝", "🦉", "🦾", "💬", "📎", "🔧", "🎨", "📚",
]

DEFAULT_ACCENT = "#7C5CFC"
