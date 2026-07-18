"""Markdown -> štýlovaný ``tkinter.Text`` renderer (live preview projektov).

Namiesto HTML (tkhtmlview) renderujeme Markdown priamo do ``tk.Text`` widgetu
pomocou tag-ov. Dôvod: plná kontrola nad farbami (dark/light), spoľahlivosť a
žiadna extra závislosť. Používame mistune AST (``renderer=None``).

Podporované: nadpisy H1-H4, **tučné**, *kurzíva*, `inline kód`, code bloky,
zoznamy (aj vnorené, číslované), citáty, odkazy (klikateľné), ~~preškrtnuté~~,
horizontálne čiary, tabuľky.
"""
from __future__ import annotations

import tkinter as tk
import tkinter.font as tkfont
import webbrowser

import mistune

# AST parser s pluginmi
_md_parser = mistune.create_markdown(
    renderer=None, plugins=["strikethrough", "table", "url"]
)

DEFAULT_UI_FAMILY = "Segoe UI"
DEFAULT_MONO_FAMILY = "Consolas"

# Veľkosti nadpisov relatívne k base
_HEADING_DELTA = {1: 10, 2: 6, 3: 3, 4: 1}


def render_markdown(
    text: tk.Text,
    md_text: str,
    colors: dict,
    ui_family: str = DEFAULT_UI_FAMILY,
    mono_family: str = DEFAULT_MONO_FAMILY,
    base_size: int = 14,
) -> None:
    """Vyrenderuje ``md_text`` do ``text`` widgetu (prepíše obsah)."""
    state = text.cget("state")
    first = text.yview()[0]  # zachovaj scroll pozíciu pri re-renderi
    text.configure(state="normal")
    text.delete("1.0", "end")

    ctx = _Ctx(text, colors, ui_family, mono_family, base_size)
    text._md_ctx = ctx  # udrž referenciu (fonty + tag callbacky)

    tokens = _md_parser(md_text or "")
    _render_blocks(ctx, tokens)

    # odstráň prebytočné konce riadkov na konci
    content = text.get("1.0", "end-1c")
    trimmed = content.rstrip("\n")
    if trimmed != content:
        text.delete(f"1.0 + {len(trimmed)} chars", "end")

    text.configure(state="disabled" if state == "disabled" else state)
    text.yview_moveto(first)


class _Ctx:
    """Render kontext — drží fonty (aby ich GC nezmazal) a link registráciu."""

    def __init__(self, text, colors, ui_family, mono_family, base_size):
        self.text = text
        self.colors = colors
        self.ui_family = ui_family
        self.mono_family = mono_family
        self.base_size = base_size
        self.font_cache: dict[tuple, tkfont.Font] = {}
        self.link_counter = 0

    def font(self, bold=False, italic=False, code=False, heading=0) -> tkfont.Font:
        key = (bold, italic, code, heading)
        if key in self.font_cache:
            return self.font_cache[key]
        family = self.mono_family if code else self.ui_family
        size = self.base_size + _HEADING_DELTA.get(heading, 0)
        if code and not heading:
            size = self.base_size - 1
        f = tkfont.Font(
            family=family, size=size,
            weight="bold" if (bold or heading) else "normal",
            slant="italic" if italic else "roman",
        )
        self.font_cache[key] = f
        return f


# --------------------------------------------------------------------------- #
# Inline rendering
# --------------------------------------------------------------------------- #
def _insert(ctx: _Ctx, s: str, style: dict) -> None:
    if not s:
        return
    text = ctx.text
    colors = ctx.colors
    heading = style.get("heading", 0)
    bold = style.get("bold", False)
    italic = style.get("italic", False)
    code = style.get("code", False)
    strike = style.get("strike", False)
    quote = style.get("quote", False)
    link = style.get("link", False)

    font = ctx.font(bold=bold, italic=italic, code=code, heading=heading)

    fg = colors["text"]
    if heading:
        fg = colors.get("heading", colors["text"])
    if quote:
        fg = colors.get("muted", colors["text"])
    if code:
        fg = colors.get("code_fg", colors["text"])
    if link:
        fg = colors.get("accent", colors["text"])

    # Stabilný tag názov podľa štýlu
    tag = f"md_{int(bold)}{int(italic)}{int(code)}{int(strike)}{int(quote)}{heading}{int(link)}"
    text.tag_configure(
        tag, font=font, foreground=fg,
        underline=link, overstrike=strike,
    )
    if code and not heading:
        text.tag_configure(tag, background=colors.get("code_bg"))

    if link:
        url = style.get("url", "")
        ctx.link_counter += 1
        link_tag = f"mdlink_{ctx.link_counter}"
        start = text.index("end-1c")
        text.insert("end", s, (tag, link_tag))
        if url:
            text.tag_configure(link_tag, underline=True)
            text.tag_bind(link_tag, "<Button-1>",
                          lambda e, u=url: _open_url(u))
            text.tag_bind(link_tag, "<Enter>",
                          lambda e: text.configure(cursor="hand2"))
            text.tag_bind(link_tag, "<Leave>",
                          lambda e: text.configure(cursor=""))
        _ = start
    else:
        text.insert("end", s, (tag,))


def _open_url(url: str) -> None:
    try:
        webbrowser.open(url)
    except Exception:
        pass


def _inline(ctx: _Ctx, nodes: list, style: dict) -> None:
    for n in nodes or []:
        t = n.get("type")
        if t == "text":
            _insert(ctx, n.get("raw", ""), style)
        elif t == "strong":
            _inline(ctx, n.get("children", []), {**style, "bold": True})
        elif t == "emphasis":
            _inline(ctx, n.get("children", []), {**style, "italic": True})
        elif t == "codespan":
            _insert(ctx, n.get("raw", ""), {**style, "code": True})
        elif t == "strikethrough":
            _inline(ctx, n.get("children", []), {**style, "strike": True})
        elif t == "link":
            url = n.get("attrs", {}).get("url", "")
            _inline(ctx, n.get("children", []), {**style, "link": True, "url": url})
        elif t == "image":
            alt = _collect_text(n.get("children", [])) or n.get("attrs", {}).get("url", "")
            _insert(ctx, f"🖼 {alt}", {**style, "italic": True})
        elif t == "linebreak":
            _insert(ctx, "\n", style)
        elif t == "softbreak":
            _insert(ctx, " ", style)
        elif t in ("inline_html", "html"):
            pass
        else:
            if n.get("children"):
                _inline(ctx, n["children"], style)
            elif n.get("raw"):
                _insert(ctx, n["raw"], style)


def _collect_text(nodes: list) -> str:
    out = []
    for n in nodes or []:
        if n.get("raw"):
            out.append(n["raw"])
        elif n.get("children"):
            out.append(_collect_text(n["children"]))
    return "".join(out)


# --------------------------------------------------------------------------- #
# Block rendering
# --------------------------------------------------------------------------- #
def _nl(ctx: _Ctx, count: int = 1) -> None:
    ctx.text.insert("end", "\n" * count)


def _render_blocks(ctx: _Ctx, tokens: list) -> None:
    for tok in tokens or []:
        t = tok.get("type")
        if t == "heading":
            lvl = min(int(tok.get("attrs", {}).get("level", 1)), 4)
            _inline(ctx, tok.get("children", []), {"heading": lvl, "bold": True})
            _nl(ctx, 2)
        elif t == "paragraph":
            _inline(ctx, tok.get("children", []), {})
            _nl(ctx, 2)
        elif t == "block_text":
            _inline(ctx, tok.get("children", []), {})
        elif t == "block_code":
            _render_code_block(ctx, tok.get("raw", ""))
        elif t == "block_quote":
            _render_quote(ctx, tok.get("children", []))
        elif t == "list":
            _render_list(ctx, tok, depth=int(tok.get("attrs", {}).get("depth", 0)))
            _nl(ctx, 1)
        elif t == "thematic_break":
            _render_hr(ctx)
        elif t == "table":
            _render_table(ctx, tok)
        elif t == "blank_line":
            pass
        elif t in ("block_html", "html"):
            pass
        else:
            if tok.get("children"):
                _render_blocks(ctx, tok["children"])


def _render_code_block(ctx: _Ctx, code: str) -> None:
    text = ctx.text
    colors = ctx.colors
    font = ctx.font(code=True)
    text.tag_configure(
        "md_codeblock", font=font, foreground=colors.get("code_fg", colors["text"]),
        background=colors.get("code_bg"), lmargin1=16, lmargin2=16,
        rmargin=16, spacing1=2, spacing3=2,
    )
    code = code.rstrip("\n")
    text.insert("end", code + "\n", ("md_codeblock",))
    _nl(ctx, 1)


def _render_quote(ctx: _Ctx, blocks: list) -> None:
    for b in blocks or []:
        if b.get("type") == "paragraph":
            _insert(ctx, "▏ ", {"quote": True})
            _inline(ctx, b.get("children", []), {"quote": True})
            _nl(ctx, 1)
        else:
            _render_blocks(ctx, [b])
    _nl(ctx, 1)


def _render_list(ctx: _Ctx, list_tok: dict, depth: int = 0) -> None:
    ordered = list_tok.get("attrs", {}).get("ordered", False)
    start = list_tok.get("attrs", {}).get("start", 1) or 1
    idx = start
    for item in list_tok.get("children", []):
        if item.get("type") != "list_item":
            continue
        indent = "    " * depth
        marker = f"{idx}. " if ordered else "•  "
        _insert(ctx, indent + marker, {"bold": bool(ordered)})
        first = True
        for child in item.get("children", []):
            ct = child.get("type")
            if ct in ("block_text", "paragraph"):
                _inline(ctx, child.get("children", []), {})
                _nl(ctx, 1)
                first = False
            elif ct == "list":
                _render_list(ctx, child, depth=depth + 1)
            elif ct == "block_code":
                _render_code_block(ctx, child.get("raw", ""))
            else:
                _render_blocks(ctx, [child])
        if first:
            _nl(ctx, 1)
        idx += 1


def _render_hr(ctx: _Ctx) -> None:
    ctx.text.tag_configure(
        "md_hr", foreground=ctx.colors.get("muted"), justify="left",
    )
    ctx.text.insert("end", "─" * 48 + "\n", ("md_hr",))
    _nl(ctx, 1)


def _render_table(ctx: _Ctx, tok: dict) -> None:
    head: list[str] = []
    body: list[list[str]] = []
    for child in tok.get("children", []):
        ct = child.get("type")
        if ct == "table_head":
            head = [_collect_text(c.get("children", [])) for c in child.get("children", [])]
        elif ct == "table_body":
            for row in child.get("children", []):
                body.append([_collect_text(c.get("children", []))
                             for c in row.get("children", [])])
    cols = max([len(head)] + [len(r) for r in body] + [0])
    if cols == 0:
        return
    widths = [0] * cols
    for r in [head, *body]:
        for i, c in enumerate(r):
            widths[i] = max(widths[i], len(c))

    def fmt(row: list[str]) -> str:
        return " | ".join(
            (row[i] if i < len(row) else "").ljust(widths[i]) for i in range(cols)
        )

    font = ctx.font(code=True)
    ctx.text.tag_configure(
        "md_table", font=font, foreground=ctx.colors.get("code_fg", ctx.colors["text"]),
        lmargin1=8, lmargin2=8,
    )
    ctx.text.insert("end", fmt(head) + "\n", ("md_table",))
    ctx.text.insert("end", "-+-".join("-" * widths[i] for i in range(cols)) + "\n",
                    ("md_table",))
    for r in body:
        ctx.text.insert("end", fmt(r) + "\n", ("md_table",))
    _nl(ctx, 1)
