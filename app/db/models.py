"""Dátový prístup (DAL) — CRUD nad platformami, promptami, projektmi, nastaveniami.

Views nikdy nesiahajú priamo na SQL — používajú funkcie z tohto modulu. Tagy sú
uložené ako JSON pole (``["kód","analýza"]``). Triedenie a filtrovanie podľa tagu
sa robí v Pythone (kvôli správnej abecede so slovenskou diakritikou a robustnosti
pri malých objemoch dát).
"""
from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field

from app import config
from app.db.database import connection

# --------------------------------------------------------------------------- #
# Dátové triedy
# --------------------------------------------------------------------------- #
@dataclass
class Platform:
    id: int
    name: str
    color: str
    icon: str = ""
    is_custom: bool = False
    sort_order: int = 0


@dataclass
class Prompt:
    id: int
    ai_id: int
    name: str
    content: str
    tags: list[str] = field(default_factory=list)
    note: str = ""
    favorite: bool = False
    created_at: str = ""
    updated_at: str = ""


@dataclass
class Project:
    id: int
    ai_id: int
    name: str
    content_md: str = ""
    status: str = "Nápad"
    linked_prompt_id: int | None = None
    created_at: str = ""
    updated_at: str = ""


# --------------------------------------------------------------------------- #
# Tag helpers
# --------------------------------------------------------------------------- #
def tags_to_json(tags: list[str] | str | None) -> str:
    if tags is None:
        return "[]"
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",") if t.strip()]
    clean = [t.strip() for t in tags if t and t.strip()]
    return json.dumps(clean, ensure_ascii=False)


def tags_from_json(raw: str | None) -> list[str]:
    if not raw:
        return []
    try:
        data = json.loads(raw)
        if isinstance(data, list):
            return [str(t) for t in data]
    except (ValueError, TypeError):
        # Legacy: čiarkami oddelené
        return [t.strip() for t in str(raw).split(",") if t.strip()]
    return []


# --------------------------------------------------------------------------- #
# Row -> dataclass
# --------------------------------------------------------------------------- #
def _platform(row: sqlite3.Row) -> Platform:
    return Platform(
        id=row["id"], name=row["name"], color=row["color"],
        icon=row["icon"] or "", is_custom=bool(row["is_custom"]),
        sort_order=row["sort_order"],
    )


def _prompt(row: sqlite3.Row) -> Prompt:
    return Prompt(
        id=row["id"], ai_id=row["ai_id"], name=row["name"], content=row["content"],
        tags=tags_from_json(row["tags"]), note=row["note"] or "",
        favorite=bool(row["favorite"]), created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _project(row: sqlite3.Row) -> Project:
    return Project(
        id=row["id"], ai_id=row["ai_id"], name=row["name"],
        content_md=row["content_md"] or "", status=row["status"],
        linked_prompt_id=row["linked_prompt_id"],
        created_at=row["created_at"], updated_at=row["updated_at"],
    )


# --------------------------------------------------------------------------- #
# Triedenie (v Pythone, s diakritikou)
# --------------------------------------------------------------------------- #
def _sort_prompts(items: list[Prompt], sort: str) -> list[Prompt]:
    if sort == "Najstaršie":
        return sorted(items, key=lambda p: (p.created_at, p.id))
    if sort == "Abecedne":
        return sorted(items, key=lambda p: p.name.casefold())
    if sort == "Obľúbené prvé":
        return sorted(items, key=lambda p: (not p.favorite, _neg_key(p.created_at, p.id)))
    # Najnovšie (default)
    return sorted(items, key=lambda p: (p.created_at, p.id), reverse=True)


def _sort_projects(items: list[Project], sort: str) -> list[Project]:
    if sort == "Najstaršie":
        return sorted(items, key=lambda p: (p.created_at, p.id))
    if sort == "Abecedne":
        return sorted(items, key=lambda p: p.name.casefold())
    # "Obľúbené prvé" nemá pri projektoch zmysel -> ako Najnovšie
    return sorted(items, key=lambda p: (p.created_at, p.id), reverse=True)


class _neg_key:
    """Umožní zostupné triedenie textového created_at v rámci tuple key."""
    __slots__ = ("created_at", "id")

    def __init__(self, created_at: str, id_: int):
        self.created_at = created_at
        self.id = id_

    def __lt__(self, other: "_neg_key") -> bool:
        return (self.created_at, self.id) > (other.created_at, other.id)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, _neg_key) and \
            (self.created_at, self.id) == (other.created_at, other.id)


# --------------------------------------------------------------------------- #
# Platformy
# --------------------------------------------------------------------------- #
def list_platforms() -> list[Platform]:
    with connection() as conn:
        rows = conn.execute(
            "SELECT * FROM ai_platforms ORDER BY sort_order ASC, id ASC"
        ).fetchall()
    return [_platform(r) for r in rows]


def get_platform(pid: int) -> Platform | None:
    with connection() as conn:
        row = conn.execute("SELECT * FROM ai_platforms WHERE id = ?", (pid,)).fetchone()
    return _platform(row) if row else None


def add_platform(name: str, color: str, icon: str = "", is_custom: bool = True) -> int:
    with connection() as conn:
        order = conn.execute(
            "SELECT COALESCE(MAX(sort_order), -1) + 1 FROM ai_platforms"
        ).fetchone()[0]
        cur = conn.execute(
            "INSERT INTO ai_platforms (name, color, icon, is_custom, sort_order) "
            "VALUES (?, ?, ?, ?, ?)",
            (name.strip(), color, icon, int(is_custom), order),
        )
        return cur.lastrowid


def update_platform(pid: int, name: str, color: str, icon: str = "") -> None:
    with connection() as conn:
        conn.execute(
            "UPDATE ai_platforms SET name = ?, color = ?, icon = ? WHERE id = ?",
            (name.strip(), color, icon, pid),
        )


def delete_platform(pid: int) -> None:
    with connection() as conn:
        conn.execute("DELETE FROM ai_platforms WHERE id = ?", (pid,))


def platform_id_by_name(name: str, exclude_id: int | None = None) -> int | None:
    """Nájde id platformy s rovnakým menom (case-insensitive aj s diakritikou).

    SQLite NOCASE skladá len ASCII, preto porovnávame v Pythone cez casefold().
    """
    target = name.strip().casefold()
    with connection() as conn:
        rows = conn.execute("SELECT id, name FROM ai_platforms").fetchall()
    for r in rows:
        if r["id"] != exclude_id and str(r["name"]).strip().casefold() == target:
            return r["id"]
    return None


def platform_name_exists(name: str, exclude_id: int | None = None) -> bool:
    return platform_id_by_name(name, exclude_id=exclude_id) is not None


# --------------------------------------------------------------------------- #
# Prompty
# --------------------------------------------------------------------------- #
def list_prompts(
    ai_id: int,
    sort: str = "Najnovšie",
    tag: str | None = None,
    search: str | None = None,
) -> list[Prompt]:
    with connection() as conn:
        rows = conn.execute(
            "SELECT * FROM prompts WHERE ai_id = ?", (ai_id,)
        ).fetchall()
    items = [_prompt(r) for r in rows]
    if search:
        q = search.casefold().strip()
        items = [p for p in items if q in p.name.casefold() or q in p.content.casefold()]
    if tag and tag != "Všetky tagy":
        items = [p for p in items if tag in p.tags]
    return _sort_prompts(items, sort)


def get_prompt(pid: int) -> Prompt | None:
    with connection() as conn:
        row = conn.execute("SELECT * FROM prompts WHERE id = ?", (pid,)).fetchone()
    return _prompt(row) if row else None


def add_prompt(ai_id: int, name: str, content: str, tags=None,
               note: str = "", favorite: bool = False) -> int:
    with connection() as conn:
        cur = conn.execute(
            "INSERT INTO prompts (ai_id, name, content, tags, note, favorite) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (ai_id, name.strip(), content, tags_to_json(tags), note, int(favorite)),
        )
        return cur.lastrowid


def update_prompt(pid: int, name: str, content: str, tags=None,
                  note: str = "", favorite: bool = False) -> None:
    with connection() as conn:
        conn.execute(
            "UPDATE prompts SET name = ?, content = ?, tags = ?, note = ?, "
            "favorite = ?, updated_at = datetime('now') WHERE id = ?",
            (name.strip(), content, tags_to_json(tags), note, int(favorite), pid),
        )


def delete_prompt(pid: int) -> None:
    with connection() as conn:
        conn.execute("DELETE FROM prompts WHERE id = ?", (pid,))


def toggle_favorite(pid: int) -> bool:
    with connection() as conn:
        row = conn.execute("SELECT favorite FROM prompts WHERE id = ?", (pid,)).fetchone()
        if row is None:
            return False
        new_val = 0 if row["favorite"] else 1
        conn.execute(
            "UPDATE prompts SET favorite = ?, updated_at = datetime('now') WHERE id = ?",
            (new_val, pid),
        )
    return bool(new_val)


def duplicate_prompt(pid: int) -> int | None:
    p = get_prompt(pid)
    if p is None:
        return None
    new_name = _unique_copy_name(p.name, {x.name for x in list_prompts(p.ai_id)})
    return add_prompt(p.ai_id, new_name, p.content, p.tags, p.note, p.favorite)


def prompt_id_by_name(ai_id: int, name: str, exclude_id: int | None = None) -> int | None:
    """Nájde id promptu s rovnakým menom (case-insensitive aj s diakritikou).

    SQLite NOCASE skladá len ASCII, preto porovnávame v Pythone cez casefold().
    """
    target = name.strip().casefold()
    with connection() as conn:
        rows = conn.execute(
            "SELECT id, name FROM prompts WHERE ai_id = ?", (ai_id,)
        ).fetchall()
    for r in rows:
        if r["id"] != exclude_id and str(r["name"]).strip().casefold() == target:
            return r["id"]
    return None


def prompt_name_exists(ai_id: int, name: str, exclude_id: int | None = None) -> bool:
    return prompt_id_by_name(ai_id, name, exclude_id=exclude_id) is not None


def count_prompts(ai_id: int) -> int:
    with connection() as conn:
        return conn.execute(
            "SELECT COUNT(*) FROM prompts WHERE ai_id = ?", (ai_id,)
        ).fetchone()[0]


def all_tags(ai_id: int) -> list[str]:
    """Zoznam unikátnych tagov použitých v promptoch daného AI (zoradený)."""
    tags: set[str] = set()
    for p in list_prompts(ai_id):
        tags.update(p.tags)
    return sorted(tags, key=str.casefold)


# --------------------------------------------------------------------------- #
# Projekty
# --------------------------------------------------------------------------- #
def list_projects(ai_id: int, sort: str = "Najnovšie",
                  search: str | None = None) -> list[Project]:
    with connection() as conn:
        rows = conn.execute(
            "SELECT * FROM projects WHERE ai_id = ?", (ai_id,)
        ).fetchall()
    items = [_project(r) for r in rows]
    if search:
        q = search.casefold().strip()
        items = [p for p in items
                 if q in p.name.casefold() or q in p.content_md.casefold()]
    return _sort_projects(items, sort)


def get_project(pid: int) -> Project | None:
    with connection() as conn:
        row = conn.execute("SELECT * FROM projects WHERE id = ?", (pid,)).fetchone()
    return _project(row) if row else None


def add_project(ai_id: int, name: str, content_md: str = "",
                status: str = "Nápad", linked_prompt_id: int | None = None) -> int:
    with connection() as conn:
        cur = conn.execute(
            "INSERT INTO projects (ai_id, name, content_md, status, linked_prompt_id) "
            "VALUES (?, ?, ?, ?, ?)",
            (ai_id, name.strip(), content_md, status, linked_prompt_id),
        )
        return cur.lastrowid


def update_project(pid: int, name: str, content_md: str, status: str,
                   linked_prompt_id: int | None = None) -> None:
    with connection() as conn:
        conn.execute(
            "UPDATE projects SET name = ?, content_md = ?, status = ?, "
            "linked_prompt_id = ?, updated_at = datetime('now') WHERE id = ?",
            (name.strip(), content_md, status, linked_prompt_id, pid),
        )


def delete_project(pid: int) -> None:
    with connection() as conn:
        conn.execute("DELETE FROM projects WHERE id = ?", (pid,))


def duplicate_project(pid: int) -> int | None:
    p = get_project(pid)
    if p is None:
        return None
    existing = {x.name for x in list_projects(p.ai_id)}
    new_name = _unique_copy_name(p.name, existing)
    return add_project(p.ai_id, new_name, p.content_md, "Nápad", p.linked_prompt_id)


def project_id_by_name(ai_id: int, name: str, exclude_id: int | None = None) -> int | None:
    """Nájde id projektu s rovnakým menom (case-insensitive aj s diakritikou).

    SQLite NOCASE skladá len ASCII, preto porovnávame v Pythone cez casefold().
    """
    target = name.strip().casefold()
    with connection() as conn:
        rows = conn.execute(
            "SELECT id, name FROM projects WHERE ai_id = ?", (ai_id,)
        ).fetchall()
    for r in rows:
        if r["id"] != exclude_id and str(r["name"]).strip().casefold() == target:
            return r["id"]
    return None


def project_name_exists(ai_id: int, name: str, exclude_id: int | None = None) -> bool:
    return project_id_by_name(ai_id, name, exclude_id=exclude_id) is not None


def count_projects(ai_id: int) -> int:
    with connection() as conn:
        return conn.execute(
            "SELECT COUNT(*) FROM projects WHERE ai_id = ?", (ai_id,)
        ).fetchone()[0]


# --------------------------------------------------------------------------- #
# Globálne vyhľadávanie (naprieč všetkými AI)
# --------------------------------------------------------------------------- #
def search_global(query: str) -> dict:
    """Vráti prompty aj projekty (naprieč AI), ktoré matchujú query.

    Návrat: ``{"prompts": [(Prompt, Platform)], "projects": [(Project, Platform)]}``
    """
    query = (query or "").strip()
    result: dict = {"prompts": [], "projects": []}
    if not query:
        return result
    q = query.casefold()
    platforms = {p.id: p for p in list_platforms()}
    with connection() as conn:
        prow = conn.execute("SELECT * FROM prompts").fetchall()
        jrow = conn.execute("SELECT * FROM projects").fetchall()
    for r in prow:
        pr = _prompt(r)
        if q in pr.name.casefold() or q in pr.content.casefold() \
                or any(q in t.casefold() for t in pr.tags):
            plat = platforms.get(pr.ai_id)
            if plat:
                result["prompts"].append((pr, plat))
    for r in jrow:
        pj = _project(r)
        if q in pj.name.casefold() or q in pj.content_md.casefold():
            plat = platforms.get(pj.ai_id)
            if plat:
                result["projects"].append((pj, plat))
    result["prompts"].sort(key=lambda t: (t[0].created_at, t[0].id), reverse=True)
    result["projects"].sort(key=lambda t: (t[0].created_at, t[0].id), reverse=True)
    return result


# --------------------------------------------------------------------------- #
# Nastavenia (key-value)
# --------------------------------------------------------------------------- #
def get_setting(key: str, default: str | None = None) -> str | None:
    with connection() as conn:
        row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else default


def set_setting(key: str, value: str) -> None:
    with connection() as conn:
        conn.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, str(value)),
        )


def get_all_settings() -> dict[str, str]:
    with connection() as conn:
        rows = conn.execute("SELECT key, value FROM settings").fetchall()
    return {r["key"]: r["value"] for r in rows}


# --------------------------------------------------------------------------- #
# Štatistiky
# --------------------------------------------------------------------------- #
def platform_stats() -> list[dict]:
    stats = []
    with connection() as conn:
        for plat in list_platforms():
            pc = conn.execute(
                "SELECT COUNT(*) FROM prompts WHERE ai_id = ?", (plat.id,)
            ).fetchone()[0]
            jc = conn.execute(
                "SELECT COUNT(*) FROM projects WHERE ai_id = ?", (plat.id,)
            ).fetchone()[0]
            fc = conn.execute(
                "SELECT COUNT(*) FROM prompts WHERE ai_id = ? AND favorite = 1",
                (plat.id,),
            ).fetchone()[0]
            stats.append({
                "platform": plat, "prompts": pc, "projects": jc, "favorites": fc,
            })
    return stats


def totals() -> dict:
    with connection() as conn:
        p = conn.execute("SELECT COUNT(*) FROM prompts").fetchone()[0]
        j = conn.execute("SELECT COUNT(*) FROM projects").fetchone()[0]
        f = conn.execute("SELECT COUNT(*) FROM prompts WHERE favorite = 1").fetchone()[0]
        a = conn.execute("SELECT COUNT(*) FROM ai_platforms").fetchone()[0]
    return {"prompts": p, "projects": j, "favorites": f, "platforms": a}


# --------------------------------------------------------------------------- #
# Export / Import (pre zálohovanie)
# --------------------------------------------------------------------------- #
def export_data() -> dict:
    """Kompletný dump všetkých tabuliek do serializovateľného dictu."""
    with connection() as conn:
        def dump(table: str) -> list[dict]:
            return [dict(r) for r in conn.execute(f"SELECT * FROM {table}").fetchall()]
        return {
            "platforms": dump("ai_platforms"),
            "prompts": dump("prompts"),
            "projects": dump("projects"),
            "settings": dump("settings"),
        }


def import_data(data: dict, mode: str = "merge") -> dict:
    """Naimportuje dáta zo zálohy.

    ``mode='merge'`` (default) — nezmaže existujúce dáta; platformy sa mapujú
    podľa mena (existujúca sa použije, nová sa vytvorí), prompty/projekty sa
    pridajú. ``mode='replace'`` — vymaže existujúce dáta a nahradí zálohou.

    Návrat: počty naimportovaných záznamov.
    """
    counts = {"platforms": 0, "prompts": 0, "projects": 0}
    platforms = data.get("platforms", [])
    prompts = data.get("prompts", [])
    projects = data.get("projects", [])

    with connection() as conn:
        if mode == "replace":
            conn.execute("DELETE FROM projects")
            conn.execute("DELETE FROM prompts")
            conn.execute("DELETE FROM ai_platforms")

        # id (v zálohe) -> nové id v tejto DB
        plat_map: dict[int, int] = {}
        name_to_id: dict[str, int] = {}
        for r in conn.execute("SELECT id, name FROM ai_platforms").fetchall():
            name_to_id[str(r["name"]).casefold()] = r["id"]

        for p in platforms:
            old_id = p.get("id")
            key = str(p.get("name", "")).casefold()
            if mode == "merge" and key in name_to_id:
                plat_map[old_id] = name_to_id[key]
                continue
            cur = conn.execute(
                "INSERT INTO ai_platforms (name, color, icon, is_custom, sort_order) "
                "VALUES (?, ?, ?, ?, ?)",
                (p.get("name", "AI"), p.get("color", config.DEFAULT_ACCENT),
                 p.get("icon", ""), int(p.get("is_custom", 1)),
                 p.get("sort_order", 0)),
            )
            plat_map[old_id] = cur.lastrowid
            name_to_id[key] = cur.lastrowid
            counts["platforms"] += 1

        prompt_map: dict[int, int] = {}
        for pr in prompts:
            new_ai = plat_map.get(pr.get("ai_id"))
            if new_ai is None:
                continue
            cur = conn.execute(
                "INSERT INTO prompts (ai_id, name, content, tags, note, favorite, "
                "created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, "
                "COALESCE(?, datetime('now')), COALESCE(?, datetime('now')))",
                (new_ai, pr.get("name", ""), pr.get("content", ""),
                 pr.get("tags", "[]"), pr.get("note", ""), int(pr.get("favorite", 0)),
                 pr.get("created_at"), pr.get("updated_at")),
            )
            prompt_map[pr.get("id")] = cur.lastrowid
            counts["prompts"] += 1

        for pj in projects:
            new_ai = plat_map.get(pj.get("ai_id"))
            if new_ai is None:
                continue
            linked = prompt_map.get(pj.get("linked_prompt_id"))
            conn.execute(
                "INSERT INTO projects (ai_id, name, content_md, status, "
                "linked_prompt_id, created_at, updated_at) VALUES (?, ?, ?, ?, ?, "
                "COALESCE(?, datetime('now')), COALESCE(?, datetime('now')))",
                (new_ai, pj.get("name", ""), pj.get("content_md", ""),
                 pj.get("status", "Nápad"), linked,
                 pj.get("created_at"), pj.get("updated_at")),
            )
            counts["projects"] += 1

        if mode == "replace":
            for s in data.get("settings", []):
                conn.execute(
                    "INSERT INTO settings (key, value) VALUES (?, ?) "
                    "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                    (s.get("key"), s.get("value")),
                )
    return counts


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _unique_copy_name(base: str, existing: set[str]) -> str:
    candidate = f"{base} (kópia)"
    i = 2
    while candidate in existing:
        candidate = f"{base} (kópia {i})"
        i += 1
    return candidate
