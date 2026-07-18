# 🧠 AI Prompt Manager

Lokálna desktopová Windows aplikácia na organizovanie **AI promptov** a **projektov**
pre všetky hlavné AI platformy (ChatGPT, Claude, Gemini, Grok, Perplexity, Copilot,
Mistral, Llama…). Beží úplne offline — všetky dáta ostávajú u teba v SQLite databáze.
Žiadny cloud, žiadny účet.

![verzia](https://img.shields.io/badge/verzia-1.0.0-7C5CFC) ![python](https://img.shields.io/badge/python-3.11%2B-blue)

---

## ✨ Funkcie

- **Sidebar s AI platformami** — 8 predvolených + neobmedzene vlastných (názov, farba, emoji)
- **Prompty** — pridať / upraviť / duplikovať / zmazať / kopírovať jedným klikom, tagy, poznámky, ⭐ obľúbené
- **Projekty** — plnohodnotný **Markdown editor so split-view live náhľadom**, status (Nápad / V procese / Hotovo), prepojenie s promptom, export do `.md`
- **Globálne vyhľadávanie** naprieč všetkými AI (názov + obsah + tagy)
- **Filtrovanie podľa tagu** a **triedenie** (najnovšie / najstaršie / obľúbené / abecedne)
- **Dark / Light / Systémový** režim + voliteľná **akcentová farba**
- **Zálohovanie** — export/import celej databázy ako `.zip` (import nič nezmaže — pridáva), + automatická záloha (denne/týždenne)
- **Štatistiky** — prehľad počtu promptov/projektov podľa AI
- **Klávesové skratky** pre rýchlu prácu
- **Kontextové menu** na AI (pravý klik) — rýchle otvorenie AI v prehliadači
- Beží ako jeden **`.exe`** bez inštalácie Pythonu

---

## ⌨️ Klávesové skratky

| Skratka          | Akcia                                   |
|------------------|-----------------------------------------|
| `Ctrl+N`         | Nový prompt (v aktuálnom AI)            |
| `Ctrl+Shift+N`   | Nový projekt                            |
| `Ctrl+F`         | Fokus na globálne vyhľadávanie          |
| `Ctrl+Enter`     | Uložiť formulár / editor                |
| `Esc`            | Zavrieť modal / editor                  |
| `Ctrl+D`         | Duplikovať vybranú kartu                |
| `Delete`         | Zmazať vybranú kartu (s potvrdením)     |
| `Ctrl+B`         | Prepnúť dark / light režim              |

> Kartu „vyberieš“ kliknutím (zvýrazní sa akcentovým rámikom) — potom fungujú `Ctrl+D` / `Delete`.

---

## ⚡ Spustenie (dev mód)

```bash
cd AIpromtmanagerapp
pip install -r requirements.txt
python main.py
```

Vyžaduje **Python 3.11+**.

## 📦 Build do `.exe`

```bash
pip install pyinstaller
python build_exe.py
# alebo priamo:
pyinstaller build.spec --noconfirm --clean
```

Výsledok: **`dist/AIPromptManager.exe`** — jeden súbor, spustiteľný bez Pythonu.

---

## 🗂️ Kde sú dáta?

Databáza (`prompts.db`) a nastavenia sa ukladajú do používateľského priečinka:

```
%APPDATA%\AIPromptManager\
├── prompts.db          # SQLite databáza (prompty, projekty, AI, nastavenia)
├── config.json         # cesta k databáze
└── backups\            # automatické zálohy
```

Cestu k databáze vieš zmeniť v **Nastavenia → Dáta**.

---

## 🧱 Štruktúra projektu

```
AIpromtmanagerapp/
├── main.py                  # vstupný bod
├── app/
│   ├── config.py            # cesty, konštanty, default AI, číselníky
│   ├── db/
│   │   ├── database.py      # SQLite pripojenie + schéma + seed
│   │   └── models.py        # dátový prístup (CRUD, search, export/import)
│   ├── ui/
│   │   ├── theme.py         # farebné tokeny, dark/light, akcent
│   │   ├── components.py    # karty, odznaky, toast, tooltip, dialóg base
│   │   ├── app_window.py    # hlavné okno + kontrolér + skratky
│   │   ├── sidebar.py       # zoznam AI + vyhľadávanie
│   │   ├── prompt_view.py   # prompty
│   │   ├── project_view.py  # projekty
│   │   ├── dialogs.py       # prompt/project/AI dialógy
│   │   ├── search_view.py   # výsledky globálneho hľadania
│   │   ├── settings_view.py # nastavenia
│   │   └── stats_view.py    # štatistiky
│   └── utils/
│       ├── clipboard.py     # kopírovanie do schránky
│       ├── markdown.py      # Markdown → štýlovaný Text (live náhľad)
│       └── backup.py        # export/import .zip
├── assets/
│   ├── icon.ico
│   └── make_icon.py         # generátor ikony
├── requirements.txt
├── build.spec               # PyInstaller
├── build_exe.py
└── README.md
```

---

## 🛠️ Tech stack

- **UI:** CustomTkinter 5.2 (moderný dark/light vzhľad)
- **Backend:** Python 3.11+
- **Databáza:** SQLite (lokálny súbor)
- **Markdown:** mistune 3 (vlastný renderer do `tk.Text`)
- **Clipboard:** pyperclip
- **Build:** PyInstaller (single-file `.exe`)

---

## 📥 Stiahnutie

Hotový `.exe` nájdeš v sekcii [Releases](https://github.com/Apoliak7777/AI-Promt-Manager/releases)
— stačí stiahnuť a spustiť, netreba inštalovať Python ani nič iné.

---

## 📄 Licencia

[GNU GPL v3.0](LICENSE)

---

*Vytvorené ako lokálny nástroj na organizáciu AI workflow. Všetko ostáva u teba.*
