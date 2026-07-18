"""Zálohovanie — export/import všetkých dát ako ``.zip``.

Formát zálohy (zip):
  - ``manifest.json`` — {"app", "version", "format", "created_at", "counts"}
  - ``data.json``     — dump tabuliek (platforms, prompts, projects, settings)

Import je defaultne **merge** (nezmaže existujúce dáta), voliteľne **replace**.
"""
from __future__ import annotations

import json
import zipfile
from datetime import datetime
from pathlib import Path

from app import config
from app.db import models

BACKUP_FORMAT = "aipm-backup-1"


def export_backup(dest_path: str | Path) -> Path:
    """Vytvorí ``.zip`` zálohu na ``dest_path``. Vráti cestu k súboru."""
    dest = Path(dest_path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    data = models.export_data()
    manifest = {
        "app": config.APP_NAME,
        "version": config.APP_VERSION,
        "format": BACKUP_FORMAT,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "counts": {
            "platforms": len(data.get("platforms", [])),
            "prompts": len(data.get("prompts", [])),
            "projects": len(data.get("projects", [])),
        },
    }
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
        zf.writestr("data.json", json.dumps(data, ensure_ascii=False, indent=2))
    return dest


def validate_backup(src_path: str | Path) -> tuple[bool, str, dict | None]:
    """Overí štruktúru zálohy. Vráti (ok, správa, manifest)."""
    src = Path(src_path)
    if not src.exists():
        return False, "Súbor neexistuje.", None
    try:
        with zipfile.ZipFile(src, "r") as zf:
            names = set(zf.namelist())
            if "data.json" not in names:
                return False, "Súbor nie je platný zálohovací súbor (chýba data.json).", None
            manifest = {}
            if "manifest.json" in names:
                try:
                    manifest = json.loads(zf.read("manifest.json").decode("utf-8"))
                except ValueError:
                    manifest = {}
            data = json.loads(zf.read("data.json").decode("utf-8"))
            if not isinstance(data, dict) or "prompts" not in data \
                    or "platforms" not in data:
                return False, "Súbor nie je platný zálohovací súbor (neplatná štruktúra).", None
    except (zipfile.BadZipFile, ValueError, OSError):
        return False, "Súbor nie je platný ZIP / je poškodený.", None
    return True, "OK", manifest


def import_backup(src_path: str | Path, mode: str = "merge") -> dict:
    """Naimportuje zálohu. Vráti počty naimportovaných záznamov.

    Vyhodí ``ValueError`` ak je súbor neplatný.
    """
    ok, msg, _ = validate_backup(src_path)
    if not ok:
        raise ValueError(msg)
    with zipfile.ZipFile(Path(src_path), "r") as zf:
        data = json.loads(zf.read("data.json").decode("utf-8"))
    return models.import_data(data, mode=mode)


def auto_backup_dir() -> Path:
    d = config.CONFIG_DIR / "backups"
    d.mkdir(parents=True, exist_ok=True)
    return d


def run_auto_backup() -> Path | None:
    """Spustí auto-zálohu podľa nastavenia (denne/týždenne). Vráti cestu alebo None."""
    setting = models.get_setting("auto_backup", "off")
    if setting not in ("daily", "weekly"):
        return None
    last = models.get_setting("last_backup", "")
    now = datetime.now()
    if last:
        try:
            last_dt = datetime.fromisoformat(last)
            delta = (now - last_dt).days
            if setting == "daily" and delta < 1:
                return None
            if setting == "weekly" and delta < 7:
                return None
        except ValueError:
            pass
    stamp = now.strftime("%Y%m%d_%H%M%S")
    path = auto_backup_dir() / f"auto_backup_{stamp}.zip"
    export_backup(path)
    models.set_setting("last_backup", now.isoformat(timespec="seconds"))
    _prune_auto_backups(keep=10)
    return path


def _prune_auto_backups(keep: int = 10) -> None:
    files = sorted(auto_backup_dir().glob("auto_backup_*.zip"),
                   key=lambda p: p.stat().st_mtime, reverse=True)
    for old in files[keep:]:
        try:
            old.unlink()
        except OSError:
            pass
