<div align="center">

[![Slovencina](https://img.shields.io/badge/SK-Sloven%C4%8Dina-2ea043?style=for-the-badge)](README.md) [![English](https://img.shields.io/badge/EN-English-30363d?style=for-the-badge)](README.en.md)

</div>

<div align="center">

# 🧠 AI Prompt Manager

**Lokálna Windows appka na organizovanie AI promptov a projektov — bez cloudu, bez účtu, všetko ostáva u teba.**

![verzia](https://img.shields.io/badge/verzia-1.0.0-7C5CFC?style=flat-square)
![python](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=flat-square&logo=python&logoColor=white)
![ui](https://img.shields.io/badge/UI-CustomTkinter%205.2-1f6feb?style=flat-square)
![db](https://img.shields.io/badge/DB-SQLite-003B57?style=flat-square&logo=sqlite&logoColor=white)
![build](https://img.shields.io/badge/build-PyInstaller-FFD43B?style=flat-square)
![licencia](https://img.shields.io/badge/licencia-GPL--3.0-2ea043?style=flat-square)

[📥 Stiahnuť .exe (Releases)](https://github.com/Apoliak7777/AI-Promt-Manager/releases)

</div>

---

## 📑 Obsah

- [🔍 Prehľad](#-prehľad)
- [✨ Funkcie](#-funkcie)
- [⚡ Inštalácia a spustenie](#-inštalácia-a-spustenie)
- [📦 Build do .exe](#-build-do-exe)
- [🧱 Štruktúra projektu](#-štruktúra-projektu)
- [🗂️ Kde sú uložené dáta](#️-kde-sú-uložené-dáta)
- [⌨️ Klávesové skratky](#️-klávesové-skratky)
- [🤖 Predvolené AI platformy](#-predvolené-ai-platformy)
- [🛠️ Tech stack](#️-tech-stack)
- [⚠️ Poznámky a obmedzenia](#️-poznámky-a-obmedzenia)
- [📄 Licencia](#-licencia)

---

## 🔍 Prehľad

AI Prompt Manager je desktopová aplikácia napísaná v Pythone (CustomTkinter + SQLite), ktorá ti drží **prompty** a **projekty** roztriedené podľa jednotlivých AI platforiem. Ľavý sidebar je zoznam AI, hlavná plocha prepína medzi kartami `Prompty` a `Projekty`.

Aplikácia beží **úplne offline** — jediné, čo siaha na internet, je otvorenie AI vo webovom prehliadači cez kontextové menu. Dáta žijú v jednom SQLite súbore v tvojom používateľskom priečinku, nikde inde.

| Vlastnosť | Hodnota |
|---|---|
| Typ | Desktopová GUI aplikácia |
| Cieľová platforma | Windows (na macOS/Linux existuje dev fallback) |
| Sieťová komunikácia | Žiadna (okrem otvorenia odkazu v prehliadači) |
| Úložisko | Lokálna SQLite databáza `prompts.db` |
| Distribúcia | Jeden `.exe` bez inštalácie Pythonu |

---

## ✨ Funkcie

- 🤖 **AI platformy v sidebare** — 8 predvolených (ChatGPT, Claude, Gemini, Grok, Perplexity, GitHub Copilot, Mistral, Llama/Ollama) plus neobmedzene vlastných s vlastným názvom, farbou a emoji ikonou.
- 📝 **Prompty** — pridanie, úprava, duplikovanie, mazanie a kopírovanie obsahu do schránky jedným klikom; ku každému promptu tagy, krátka poznámka a označenie ⭐ obľúbený.
- 📁 **Projekty** — Markdown editor v **split-view** s live náhľadom (debounce 220 ms), status `Nápad` / `V procese` / `Hotovo`, voliteľné prepojenie s konkrétnym promptom a export obsahu do `.md` súboru.
- 🔍 **Globálne vyhľadávanie** — naprieč všetkými AI naraz; prompty sa hľadajú v názve, obsahu aj tagoch, projekty v názve a Markdown obsahu.
- 🏷️ **Filtrovanie a triedenie** — filter podľa tagu a štyri režimy triedenia: `Najnovšie`, `Najstaršie`, `Obľúbené prvé`, `Abecedne` (abeceda rieši aj slovenskú diakritiku, lebo sa triedi v Pythone cez `casefold()`).
- 🎨 **Dark / Light / Systémový režim** — plus akcentová farba z 8 preddefinovaných alebo ľubovoľná vlastná cez color picker.
- 💾 **Zálohovanie** — export celej databázy do `.zip` (`manifest.json` + `data.json`) a import späť. Import **nič nemaže, iba pridáva**. Automatická záloha denne alebo týždenne, drží sa posledných 10 súborov.
- 📊 **Štatistiky** — súhrn počtu promptov, projektov, obľúbených a AI platforiem plus stĺpcové rozdelenie podľa jednotlivých AI.
- 🚀 **Rýchle otvorenie AI** — pravý klik na AI v sidebare otvorí jeho oficiálnu web appku v prehliadači.
- 📂 **Presunuteľná databáza** — v `Nastavenia → Dáta` vieš zmeniť umiestnenie `prompts.db` (napr. na cloudový disk); existujúca databáza sa prekopíruje cez `sqlite3.backup()`.
- ⌨️ **Klávesové skratky** — nový prompt, nový projekt, hľadanie, uloženie, duplikovanie, mazanie, prepnutie témy.

---

## ⚡ Inštalácia a spustenie

> [!NOTE]
> Ak chceš appku len používať, nemusíš inštalovať nič — stiahni si hotový `.exe` zo [sekcie Releases](https://github.com/Apoliak7777/AI-Promt-Manager/releases).

Pre vývoj alebo spustenie zo zdrojákov potrebuješ **Python 3.11+**:

```bash
git clone https://github.com/Apoliak7777/AI-Promt-Manager.git
cd AI-Promt-Manager
pip install -r requirements.txt
python main.py
```

Voliteľne vo virtuálnom prostredí:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

Pri prvom spustení sa automaticky vytvorí databáza, naseeduje sa 8 predvolených AI platforiem a základné nastavenia.

---

## 📦 Build do `.exe`

```bash
pip install pyinstaller
python build_exe.py
```

Skript `build_exe.py` najprv skontroluje, či existuje `assets/icon.ico` — ak nie, vygeneruje ju cez `assets/make_icon.py` (vyžaduje Pillow) — a potom spustí PyInstaller.

Ak chceš PyInstaller zavolať priamo:

```bash
pyinstaller build.spec --noconfirm --clean
```

Výsledok v oboch prípadoch: **`dist/AIPromptManager.exe`** — jeden windowed súbor bez konzoly, ktorý beží bez nainštalovaného Pythonu.

| Parameter buildu | Hodnota (z `build.spec`) |
|---|---|
| Názov výstupu | `AIPromptManager` |
| Režim | one-file, `console=False` |
| Ikona | `assets/icon.ico` |
| UPX kompresia | zapnutá |
| Zabalené dáta | dátové súbory CustomTkinter + `assets/icon.ico` |
| Vylúčené moduly | `pytest`, `PyInstaller` |

---

## 🧱 Štruktúra projektu

```text
AI-Promt-Manager/
├── main.py                  # vstupný bod: init DB, auto-záloha, error.log, mainloop
├── app/
│   ├── config.py            # metadáta appky, cesty, default AI, číselníky, changelog
│   ├── db/
│   │   ├── database.py      # SQLite pripojenie, schéma, seed platforiem a nastavení
│   │   └── models.py        # DAL — CRUD, hľadanie, štatistiky, export/import dát
│   ├── ui/
│   │   ├── theme.py         # farebné tokeny, dark/light, akcent, fonty
│   │   ├── components.py    # Card, Badge, TagChip, Tooltip, toast, ModalDialog
│   │   ├── app_window.py    # hlavné okno, routing medzi views, klávesové skratky
│   │   ├── sidebar.py       # zoznam AI, globálne hľadanie, kontextové menu
│   │   ├── prompt_view.py   # karty promptov, toolbar, filter tagov, triedenie
│   │   ├── project_view.py  # karty projektov, statusy, export .md
│   │   ├── dialogs.py       # PromptDialog, ProjectEditor (split-view), PlatformDialog
│   │   ├── search_view.py   # výsledky globálneho hľadania naprieč AI
│   │   ├── settings_view.py # vzhľad, dáta, zálohovanie, správa AI, o aplikácii
│   │   └── stats_view.py    # súhrny a rozdelenie podľa AI
│   └── utils/
│       ├── clipboard.py     # pyperclip s tkinter fallbackom
│       ├── markdown.py      # mistune AST → štýlovaný tk.Text (live náhľad)
│       └── backup.py        # export/import .zip, auto-záloha, prune starých záloh
├── assets/
│   ├── icon.ico             # ikona aplikácie
│   └── make_icon.py         # generátor ikony (PIL, čisto geometricky)
├── requirements.txt
├── build.spec               # PyInstaller spec
├── build_exe.py             # pohodlný build skript
└── LICENSE
```

---

## 🗂️ Kde sú uložené dáta

Databáza sa zámerne **neukladá do inštalačného priečinka** (kvôli právam na zápis), ale do používateľského dátového priečinka:

```text
%APPDATA%\AIPromptManager\
├── prompts.db          # SQLite — prompty, projekty, AI platformy, nastavenia
├── config.json         # bootstrap config: cesta k databáze
├── error.log           # zachytené chyby (windowed .exe nemá konzolu)
└── backups\            # automatické zálohy auto_backup_*.zip (max 10)
```

Na macOS/Linuxe sa použije `$XDG_DATA_HOME/AIPromptManager` alebo `~/.aipromptmanager`.

Cestu k databáze zmeníš v **Nastavenia → Dáta → Zmeniť umiestnenie**. Ak sa pri štarte ukáže, že vlastné umiestnenie nie je dostupné (napr. odpojený sieťový disk), appka zobrazí upozornenie a automaticky sa vráti na predvolenú cestu.

### Schéma databázy

| Tabuľka | Obsah |
|---|---|
| `ai_platforms` | AI platformy — názov, farba, emoji ikona, príznak `is_custom`, poradie |
| `prompts` | prompty — názov, obsah, tagy (JSON pole), poznámka, `favorite`, časové značky |
| `projects` | projekty — názov, `content_md`, status, `linked_prompt_id`, časové značky |
| `settings` | key-value nastavenia (režim vzhľadu, akcent, triedenie, auto-záloha, posledné AI) |

Cudzie kľúče sú zapnuté (`PRAGMA foreign_keys = ON`), zápis beží v režime WAL.

---

## ⌨️ Klávesové skratky

| Skratka | Akcia |
|---|---|
| `Ctrl+N` | Nový prompt v aktuálnom AI |
| `Ctrl+Shift+N` | Nový projekt v aktuálnom AI |
| `Ctrl+F` | Fokus na globálne vyhľadávanie |
| `Ctrl+Enter` | Uložiť formulár / Markdown editor |
| `Esc` | Zavrieť modálne okno alebo vyčistiť vyhľadávanie |
| `Ctrl+D` | Duplikovať vybranú kartu |
| `Delete` | Zmazať vybranú kartu (s potvrdením) |
| `Ctrl+B` | Prepnúť dark / light režim |

> [!TIP]
> Kartu „vyberieš" kliknutím — zvýrazní sa akcentovým rámikom. Až potom fungujú `Ctrl+D` a `Delete`. Skratky sú zámerne neaktívne, kým máš kurzor v textovom poli, aby ti `Delete` nemazal karty počas písania.

---

## 🤖 Predvolené AI platformy

Osem platforiem, ktoré sa naseedujú pri prvom spustení. Pravý klik na položku v sidebare otvorí jej web appku.

| AI | Farba | Odkaz na quick-launch |
|---|---|---|
| ChatGPT | `#10A37F` | https://chat.openai.com |
| Claude | `#D97757` | https://claude.ai |
| Gemini | `#4285F4` | https://gemini.google.com |
| Grok | `#1A1A1A` | https://grok.com |
| Perplexity | `#20808D` | https://www.perplexity.ai |
| GitHub Copilot | `#8957E5` | https://github.com/copilot |
| Mistral | `#FF7000` | https://chat.mistral.ai |
| Llama / Ollama | `#8B5E3C` | https://ollama.com |

Vlastné AI pridáš cez `➕ Pridať AI` v sidebare alebo v `Nastavenia → AI platformy`. Vlastné AI nemá priradený quick-launch odkaz.

---

## 🛠️ Tech stack

| Vrstva | Technológia | Poznámka |
|---|---|---|
| UI | CustomTkinter `>=5.2.0` | moderný dark/light vzhľad nad tkinter |
| Jazyk | Python 3.11+ | žiadny framework, čistý štandard + 3 knižnice |
| Databáza | SQLite (`sqlite3`) | lokálny súbor, WAL, cudzie kľúče |
| Markdown | mistune `>=3.0.0` | AST parser + vlastný renderer do `tk.Text` |
| Schránka | pyperclip `>=1.8.2` | s fallbackom na tkinter clipboard |
| Ikona | Pillow `>=10.0.0` | len pri generovaní `icon.ico`, nie za behu |
| Build | PyInstaller | single-file windowed `.exe` |

Markdown náhľad sa nerenderuje cez HTML — mistune vracia AST a vlastný renderer ho vykreslí priamo do `tk.Text` cez tagy. Vďaka tomu má appka plnú kontrolu nad farbami v dark aj light režime. Podporované sú nadpisy H1–H4, tučné, kurzíva, inline aj blokový kód, zoznamy vrátane vnorených a číslovaných, citáty, klikateľné odkazy, preškrtnutý text, horizontálne čiary a tabuľky.

---

## ⚠️ Poznámky a obmedzenia

> [!WARNING]
> Databáza **nie je šifrovaná**. Je to obyčajný SQLite súbor — nedávaj do promptov API kľúče, heslá ani iné citlivé údaje, ak nemáš zabezpečený disk.

- 🪟 **Primárne Windows.** Build produkuje `.exe`, dátový priečinok je `%APPDATA%`. Kód má fallbacky pre macOS a Linux (cesty, otváranie priečinka), ale tie sú určené skôr na vývoj a testovanie.
- ♻️ **Import zálohy vždy pridáva.** Cez UI beží import v režime `merge` — existujúce dáta sa nezmažú. Zároveň sa ale prompty a projekty **nededuplikujú**, takže dvojitý import tej istej zálohy vytvorí duplicitné záznamy. Platformy sa mapujú podľa mena, tie sa nezdvoja.
- 🗑️ **Zmazanie vlastného AI zmaže aj jeho obsah.** Cudzie kľúče majú `ON DELETE CASCADE`, takže spolu s platformou zmiznú aj jej prompty a projekty. Appka pred zmazaním ukáže, koľkých záznamov sa to týka.
- 🔒 **Predvolených 8 AI sa nedá zmazať.** Majú `is_custom = 0`; upraviť alebo odstrániť sa dajú len vlastné platformy.
- ✏️ **Duplicitný názov ponúkne prepis.** Ak uložíš prompt alebo projekt s názvom, ktorý v danom AI už existuje, appka sa spýta, či chceš pôvodný záznam prepísať.
- 🕐 **Auto-záloha beží pri štarte a potom každú hodinu.** Reálne sa vytvorí len vtedy, keď od poslednej uplynul nastavený interval (deň alebo týždeň). Staršie ako posledných 10 sa mažú.
- 📄 **Export projektu zapíše len samotný Markdown.** Status ani prepojený prompt sa do `.md` súboru neukladajú — na kompletný prenos použi `.zip` zálohu.

---

## 📄 Licencia

Projekt je licencovaný pod **GNU General Public License v3.0** — plné znenie nájdeš v súbore [LICENSE](LICENSE).

---

<div align="center">

Vytvoril **Alex Poliak** - [GitHub](https://github.com/Apoliak7777) - [alexpoliak21@gmail.com](mailto:alexpoliak21@gmail.com)

</div>
