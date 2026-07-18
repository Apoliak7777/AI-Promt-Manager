"""AI Prompt Manager — spúšťací bod aplikácie.

Lokálna desktop appka (CustomTkinter + SQLite) na organizovanie AI promptov
a projektov podľa jednotlivých AI platforiem.
"""
from __future__ import annotations

import sqlite3
import sys
import traceback


def _log_error(text: str) -> None:
    """Best-effort zápis chyby do error.log v config priečinku."""
    try:
        from datetime import datetime

        from app import config

        config.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(config.CONFIG_DIR / "error.log", "a", encoding="utf-8") as fh:
            fh.write(f"[{datetime.now().isoformat()}]\n{text}\n")
    except Exception:
        pass


def _fatal(exc: BaseException) -> None:
    """Zobrazí zrozumiteľnú chybovú hlášku ak spustenie zlyhá."""
    msg = f"{type(exc).__name__}: {exc}"
    traceback.print_exc()
    _log_error("".join(traceback.format_exception(type(exc), exc, exc.__traceback__)))
    try:
        import tkinter.messagebox as mb
        mb.showerror("AI Prompt Manager — chyba", f"Aplikáciu sa nepodarilo spustiť.\n\n{msg}")
    except Exception:
        pass


def main() -> int:
    try:
        from app import config
        from app.db import database
        from app.ui.app_window import AppWindow

        try:
            database.init_db()
        except (OSError, sqlite3.Error):
            if config.get_db_path() != config.DEFAULT_DB_PATH:
                # Vlastné umiestnenie DB (napr. odpojený disk) nie je dostupné — návrat na default
                traceback.print_exc()
                try:
                    import tkinter.messagebox as mb
                    mb.showwarning(
                        "AI Prompt Manager",
                        "Vlastné umiestnenie databázy nie je dostupné, používam predvolené.",
                    )
                except Exception:
                    pass
                config.set_db_path(config.DEFAULT_DB_PATH)
                database.init_db()
            else:
                raise

        # Auto-záloha na pozadí (podľa nastavenia)
        try:
            from app.utils import backup
            backup.run_auto_backup()
        except Exception:
            traceback.print_exc()

        app = AppWindow()

        # Globálna viditeľnosť chýb (windowed exe nemá konzolu) — error.log + messagebox
        def _report_error(exc_type, exc, tb) -> None:
            _log_error("".join(traceback.format_exception(exc_type, exc, tb)))
            try:
                import tkinter.messagebox as mb
                mb.showerror("AI Prompt Manager — chyba", f"{exc_type.__name__}: {exc}")
            except Exception:
                pass

        app.report_callback_exception = _report_error
        sys.excepthook = _report_error

        # Pravidelná auto-záloha pri dlho bežiacej aplikácii (každú hodinu)
        def _periodic_backup() -> None:
            try:
                from app.utils import backup
                backup.run_auto_backup()
            except Exception:
                traceback.print_exc()
            app.after(3_600_000, _periodic_backup)

        app.after(3_600_000, _periodic_backup)

        # Ikona aplikácie
        ico = config.resource_path("assets/icon.ico")
        if ico.exists():
            app.set_app_icon(ico)

        app.mainloop()
        return 0
    except Exception as exc:  # noqa: BLE001
        _fatal(exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
