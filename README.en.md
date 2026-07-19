<div align="center">

[![Slovencina](https://img.shields.io/badge/SK-Sloven%C4%8Dina-30363d?style=for-the-badge)](README.md) [![English](https://img.shields.io/badge/EN-English-2ea043?style=for-the-badge)](README.en.md)

</div>

<div align="center">

# 🧠 AI Prompt Manager

**A local Windows app for organizing AI prompts and projects — no cloud, no account, everything stays with you.**

![version](https://img.shields.io/badge/version-1.0.0-7C5CFC?style=flat-square)
![python](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=flat-square&logo=python&logoColor=white)
![ui](https://img.shields.io/badge/UI-CustomTkinter%205.2-1f6feb?style=flat-square)
![db](https://img.shields.io/badge/DB-SQLite-003B57?style=flat-square&logo=sqlite&logoColor=white)
![build](https://img.shields.io/badge/build-PyInstaller-FFD43B?style=flat-square)
![license](https://img.shields.io/badge/license-GPL--3.0-2ea043?style=flat-square)

[📥 Download the .exe (Releases)](https://github.com/Apoliak7777/AI-Promt-Manager/releases)

</div>

---

## 📑 Contents

- [🔍 Overview](#-overview)
- [✨ Features](#-features)
- [⚡ Installation and launch](#-installation-and-launch)
- [📦 Building the .exe](#-building-the-exe)
- [🧱 Project structure](#-project-structure)
- [🗂️ Where the data is stored](#️-where-the-data-is-stored)
- [⌨️ Keyboard shortcuts](#️-keyboard-shortcuts)
- [🤖 Default AI platforms](#-default-ai-platforms)
- [🛠️ Tech stack](#️-tech-stack)
- [⚠️ Notes and limitations](#️-notes-and-limitations)
- [📄 License](#-license)

---

## 🔍 Overview

AI Prompt Manager is a desktop application written in Python (CustomTkinter + SQLite) that keeps your **prompts** and **projects** sorted by individual AI platform. The left sidebar is the list of AIs, the main area switches between the `Prompty` (Prompts) and `Projekty` (Projects) tabs.

The application runs **completely offline** — the only thing that reaches the internet is opening an AI in your web browser via the context menu. Your data lives in a single SQLite file in your user folder, nowhere else.

> [!NOTE]
> The application interface itself is **in Slovak**. Throughout this document, on-screen labels are quoted exactly as they appear in the app, with an English gloss in parentheses.

| Property | Value |
|---|---|
| Type | Desktop GUI application |
| Target platform | Windows (a dev fallback exists for macOS/Linux) |
| Network communication | None (apart from opening a link in the browser) |
| Storage | Local SQLite database `prompts.db` |
| Distribution | A single `.exe`, no Python installation needed |

---

## ✨ Features

- 🤖 **AI platforms in the sidebar** — 8 defaults (ChatGPT, Claude, Gemini, Grok, Perplexity, GitHub Copilot, Mistral, Llama/Ollama) plus unlimited custom ones with their own name, color and emoji icon.
- 📝 **Prompts** — add, edit, duplicate, delete and copy the content to the clipboard with a single click; every prompt can have tags, a short note and a ⭐ favorite flag.
- 📁 **Projects** — a Markdown editor in **split-view** with a live preview (220 ms debounce), a `Nápad` / `V procese` / `Hotovo` (Idea / In progress / Done) status, an optional link to a specific prompt, and export of the content to a `.md` file.
- 🔍 **Global search** — across all AIs at once; prompts are searched by name, content and tags, projects by name and Markdown content.
- 🏷️ **Filtering and sorting** — filter by tag and four sorting modes: `Najnovšie` (Newest), `Najstaršie` (Oldest), `Obľúbené prvé` (Favorites first), `Abecedne` (Alphabetical) — alphabetical sorting handles Slovak diacritics too, because sorting happens in Python via `casefold()`.
- 🎨 **Dark / Light / System mode** — plus an accent color from 8 presets or any custom one via the color picker.
- 💾 **Backups** — export the whole database to a `.zip` (`manifest.json` + `data.json`) and import it back. Import **deletes nothing, it only adds**. Automatic backup daily or weekly, keeping the last 10 files.
- 📊 **Statistics** — a summary of the number of prompts, projects, favorites and AI platforms plus a bar breakdown per individual AI.
- 🚀 **Quick AI launch** — right-clicking an AI in the sidebar opens its official web app in the browser.
- 📂 **Movable database** — under `Nastavenia → Dáta` (Settings → Data) you can change the location of `prompts.db` (e.g. to a cloud drive); the existing database is copied over via `sqlite3.backup()`.
- ⌨️ **Keyboard shortcuts** — new prompt, new project, search, save, duplicate, delete, toggle theme.

---

## ⚡ Installation and launch

> [!NOTE]
> If you only want to use the app, you don't need to install anything — download the ready-made `.exe` from the [Releases section](https://github.com/Apoliak7777/AI-Promt-Manager/releases).

For development or running from source you need **Python 3.11+**:

```bash
git clone https://github.com/Apoliak7777/AI-Promt-Manager.git
cd AI-Promt-Manager
pip install -r requirements.txt
python main.py
```

Optionally in a virtual environment:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

On the first launch the database is created automatically, the 8 default AI platforms are seeded, along with the basic settings.

---

## 📦 Building the `.exe`

```bash
pip install pyinstaller
python build_exe.py
```

The `build_exe.py` script first checks whether `assets/icon.ico` exists — if not, it generates it via `assets/make_icon.py` (requires Pillow) — and then runs PyInstaller.

If you want to call PyInstaller directly:

```bash
pyinstaller build.spec --noconfirm --clean
```

The result in both cases: **`dist/AIPromptManager.exe`** — a single windowed file without a console that runs without Python installed.

| Build parameter | Value (from `build.spec`) |
|---|---|
| Output name | `AIPromptManager` |
| Mode | one-file, `console=False` |
| Icon | `assets/icon.ico` |
| UPX compression | enabled |
| Bundled data | CustomTkinter data files + `assets/icon.ico` |
| Excluded modules | `pytest`, `PyInstaller` |

---

## 🧱 Project structure

```text
AI-Promt-Manager/
├── main.py                  # entry point: init DB, auto-backup, error.log, mainloop
├── app/
│   ├── config.py            # app metadata, paths, default AIs, enumerations, changelog
│   ├── db/
│   │   ├── database.py      # SQLite connection, schema, seeding of platforms and settings
│   │   └── models.py        # DAL — CRUD, search, statistics, data export/import
│   ├── ui/
│   │   ├── theme.py         # color tokens, dark/light, accent, fonts
│   │   ├── components.py    # Card, Badge, TagChip, Tooltip, toast, ModalDialog
│   │   ├── app_window.py    # main window, routing between views, keyboard shortcuts
│   │   ├── sidebar.py       # AI list, global search, context menu
│   │   ├── prompt_view.py   # prompt cards, toolbar, tag filter, sorting
│   │   ├── project_view.py  # project cards, statuses, .md export
│   │   ├── dialogs.py       # PromptDialog, ProjectEditor (split-view), PlatformDialog
│   │   ├── search_view.py   # global search results across AIs
│   │   ├── settings_view.py # appearance, data, backups, AI management, about
│   │   └── stats_view.py    # summaries and per-AI breakdown
│   └── utils/
│       ├── clipboard.py     # pyperclip with a tkinter fallback
│       ├── markdown.py      # mistune AST → styled tk.Text (live preview)
│       └── backup.py        # .zip export/import, auto-backup, pruning of old backups
├── assets/
│   ├── icon.ico             # application icon
│   └── make_icon.py         # icon generator (PIL, purely geometric)
├── requirements.txt
├── build.spec               # PyInstaller spec
├── build_exe.py             # convenience build script
└── LICENSE
```

---

## 🗂️ Where the data is stored

The database is deliberately **not stored in the installation folder** (because of write permissions), but in the user data folder:

```text
%APPDATA%\AIPromptManager\
├── prompts.db          # SQLite — prompts, projects, AI platforms, settings
├── config.json         # bootstrap config: path to the database
├── error.log           # captured errors (the windowed .exe has no console)
└── backups\            # automatic backups auto_backup_*.zip (max 10)
```

On macOS/Linux, `$XDG_DATA_HOME/AIPromptManager` or `~/.aipromptmanager` is used.

You can change the database path under **Nastavenia → Dáta → Zmeniť umiestnenie** (Settings → Data → Change location). If at startup it turns out the custom location is unavailable (e.g. a disconnected network drive), the app shows a warning and automatically falls back to the default path.

### Database schema

| Table | Content |
|---|---|
| `ai_platforms` | AI platforms — name, color, emoji icon, `is_custom` flag, order |
| `prompts` | prompts — name, content, tags (JSON array), note, `favorite`, timestamps |
| `projects` | projects — name, `content_md`, status, `linked_prompt_id`, timestamps |
| `settings` | key-value settings (appearance mode, accent, sorting, auto-backup, last AI) |

Foreign keys are enabled (`PRAGMA foreign_keys = ON`), writes run in WAL mode.

---

## ⌨️ Keyboard shortcuts

| Shortcut | Action |
|---|---|
| `Ctrl+N` | New prompt in the current AI |
| `Ctrl+Shift+N` | New project in the current AI |
| `Ctrl+F` | Focus the global search |
| `Ctrl+Enter` | Save the form / Markdown editor |
| `Esc` | Close a modal window or clear the search |
| `Ctrl+D` | Duplicate the selected card |
| `Delete` | Delete the selected card (with confirmation) |
| `Ctrl+B` | Toggle dark / light mode |

> [!TIP]
> You "select" a card by clicking it — it gets highlighted with an accent border. Only then do `Ctrl+D` and `Delete` work. The shortcuts are deliberately inactive while your cursor is in a text field, so that `Delete` doesn't wipe out cards while you type.

---

## 🤖 Default AI platforms

Eight platforms that get seeded on the first launch. Right-clicking an item in the sidebar opens its web app.

| AI | Color | Quick-launch link |
|---|---|---|
| ChatGPT | `#10A37F` | https://chat.openai.com |
| Claude | `#D97757` | https://claude.ai |
| Gemini | `#4285F4` | https://gemini.google.com |
| Grok | `#1A1A1A` | https://grok.com |
| Perplexity | `#20808D` | https://www.perplexity.ai |
| GitHub Copilot | `#8957E5` | https://github.com/copilot |
| Mistral | `#FF7000` | https://chat.mistral.ai |
| Llama / Ollama | `#8B5E3C` | https://ollama.com |

You add a custom AI via `➕ Pridať AI` (Add AI) in the sidebar or under `Nastavenia → AI platformy` (Settings → AI platforms). A custom AI has no quick-launch link assigned.

---

## 🛠️ Tech stack

| Layer | Technology | Note |
|---|---|---|
| UI | CustomTkinter `>=5.2.0` | a modern dark/light look on top of tkinter |
| Language | Python 3.11+ | no framework, pure standard library + 3 packages |
| Database | SQLite (`sqlite3`) | a local file, WAL, foreign keys |
| Markdown | mistune `>=3.0.0` | AST parser + a custom renderer into `tk.Text` |
| Clipboard | pyperclip `>=1.8.2` | with a fallback to the tkinter clipboard |
| Icon | Pillow `>=10.0.0` | only when generating `icon.ico`, not at runtime |
| Build | PyInstaller | single-file windowed `.exe` |

The Markdown preview is not rendered through HTML — mistune returns an AST and a custom renderer draws it straight into `tk.Text` using tags. Thanks to that, the app has full control over the colors in both dark and light mode. Supported are H1–H4 headings, bold, italic, inline and block code, lists including nested and numbered ones, blockquotes, clickable links, strikethrough text, horizontal rules and tables.

---

## ⚠️ Notes and limitations

> [!WARNING]
> The database is **not encrypted**. It is a plain SQLite file — don't put API keys, passwords or other sensitive data into your prompts unless your disk is secured.

- 🪟 **Windows first.** The build produces an `.exe`, the data folder is `%APPDATA%`. The code has fallbacks for macOS and Linux (paths, opening the folder), but those are meant more for development and testing.
- ♻️ **Importing a backup always adds.** Through the UI, the import runs in `merge` mode — existing data is not deleted. At the same time, however, prompts and projects are **not deduplicated**, so importing the same backup twice creates duplicate records. Platforms are matched by name, so those won't be duplicated.
- 🗑️ **Deleting a custom AI deletes its content too.** Foreign keys use `ON DELETE CASCADE`, so its prompts and projects disappear along with the platform. Before deleting, the app shows how many records this affects.
- 🔒 **The 8 default AIs cannot be deleted.** They have `is_custom = 0`; only custom platforms can be edited or removed.
- ✏️ **A duplicate name offers an overwrite.** If you save a prompt or project with a name that already exists within that AI, the app asks whether you want to overwrite the original record.
- 🕐 **Auto-backup runs at startup and then every hour.** It is actually created only when the configured interval (a day or a week) has elapsed since the last one. Anything older than the last 10 is deleted.
- 📄 **Exporting a project writes out the Markdown only.** Neither the status nor the linked prompt is saved into the `.md` file — for a complete transfer use the `.zip` backup.

---

## 📄 License

The project is licensed under the **GNU General Public License v3.0** — you'll find the full text in the [LICENSE](LICENSE) file.

---

<div align="center">

Built by **Alex Poliak** - [GitHub](https://github.com/Apoliak7777) - [alexpoliak21@gmail.com](mailto:alexpoliak21@gmail.com)

</div>
