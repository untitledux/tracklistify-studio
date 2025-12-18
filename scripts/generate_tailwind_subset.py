#!/usr/bin/env python3
"""
Generate a minimal Tailwind-like CSS file for offline use.

This script scans the Jinja templates for utility class names and writes a
subset of Tailwind-compatible CSS rules to ``static/css/tailwind.css``.
It is intentionally small and only covers the classes present in the
repository so we can avoid the production CDN.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, Iterable, List

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES_DIR = ROOT / "templates"
OUTPUT_PATH = ROOT / "static" / "css" / "tailwind.css"

# Tailwind default scales (only the values we need)
SPACING: Dict[str, str] = {
    "0": "0rem",
    "0.5": "0.125rem",
    "1": "0.25rem",
    "1.5": "0.375rem",
    "2": "0.5rem",
    "2.5": "0.625rem",
    "3": "0.75rem",
    "3.5": "0.875rem",
    "4": "1rem",
    "5": "1.25rem",
    "6": "1.5rem",
    "7": "1.75rem",
    "8": "2rem",
    "9": "2.25rem",
    "10": "2.5rem",
    "11": "2.75rem",
    "12": "3rem",
    "14": "3.5rem",
    "16": "4rem",
    "20": "5rem",
    "24": "6rem",
    "28": "7rem",
    "32": "8rem",
    "36": "9rem",
    "40": "10rem",
    "44": "11rem",
    "48": "12rem",
    "52": "13rem",
    "56": "14rem",
    "60": "15rem",
    "64": "16rem",
    "72": "18rem",
    "80": "20rem",
    "96": "24rem",
}

FONT_SIZES = {
    "text-xs": ("0.75rem", "1rem"),
    "text-sm": ("0.875rem", "1.25rem"),
    "text-base": ("1rem", "1.5rem"),
    "text-lg": ("1.125rem", "1.75rem"),
    "text-xl": ("1.25rem", "1.75rem"),
    "text-2xl": ("1.5rem", "2rem"),
    "text-3xl": ("1.875rem", "2.25rem"),
}

FONT_WEIGHTS = {
    "font-medium": "500",
    "font-semibold": "600",
    "font-bold": "700",
    "font-extrabold": "800",
    "font-mono": "'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace",
}

LETTER_SPACING = {
    "tracking-tight": "-0.025em",
    "tracking-wide": "0.025em",
    "tracking-wider": "0.05em",
}

LINE_HEIGHT = {
    "leading-none": "1",
    "leading-tight": "1.25",
}

RADIUS = {
    "rounded": "0.25rem",
    "rounded-lg": "0.5rem",
    "rounded-xl": "0.75rem",
    "rounded-2xl": "1rem",
    "rounded-full": "9999px",
}

SHADOWS = {
    "shadow-sm": "0 1px 2px 0 rgb(0 0 0 / 0.05)",
    "shadow": "0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)",
    "shadow-md": "0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)",
    "shadow-lg": "0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)",
    "shadow-xl": "0 20px 25px -5px rgb(0 0 0 / 0.1), 0 10px 10px -5px rgb(0 0 0 / 0.04)",
    "shadow-2xl": "0 25px 50px -12px rgb(0 0 0 / 0.25)",
    "shadow-inner": "inset 0 2px 4px 0 rgb(0 0 0 / 0.05)",
}

RING_WIDTHS = {
    "ring": "1px",
    "ring-1": "1px",
    "ring-2": "2px",
}

COLOR_PALETTE = {
    "white": {"base": "#ffffff"},
    "black": {"base": "#000000"},
    "gray": {
        50: "#f9fafb",
        100: "#f3f4f6",
        200: "#e5e7eb",
        300: "#d1d5db",
        400: "#9ca3af",
        500: "#6b7280",
        600: "#4b5563",
        700: "#374151",
        800: "#1f2937",
        900: "#111827",
    },
    "slate": {
        200: "#e2e8f0",
        400: "#94a3b8",
        700: "#334155",
        800: "#1e293b",
        900: "#0f172a",
        950: "#020617",
    },
    "blue": {50: "#eff6ff", 100: "#dbeafe", 200: "#bfdbfe", 700: "#1d4ed8"},
    "emerald": {50: "#ecfdf3", 100: "#d1fae5", 200: "#a7f3d0", 700: "#047857"},
    "green": {50: "#f0fdf4", 100: "#dcfce7", 200: "#bbf7d0", 500: "#22c55e", 600: "#16a34a", 700: "#15803d"},
    "teal": {50: "#f0fdfa", 100: "#ccfbf1", 200: "#99f6e4", 700: "#0f766e"},
    "orange": {50: "#fff7ed", 100: "#ffedd5", 200: "#fed7aa", 400: "#fb923c", 500: "#f97316", 600: "#ea580c"},
    "yellow": {100: "#fef9c3", 700: "#a16207"},
    "pink": {50: "#fdf2f8", 100: "#fce7f3", 500: "#ec4899", 600: "#db2777"},
    "red": {50: "#fef2f2", 100: "#fee2e2", 200: "#fecdd3", 400: "#f87171", 500: "#ef4444", 600: "#dc2626", 700: "#b91c1c"},
    "blue-raw": {"50/50": "#eff6ff"},
}

OPACITY_DEFAULTS = {
    "50": 0.5,
    "60": 0.6,
    "40": 0.4,
    "30": 0.3,
    "20": 0.2,
}

RESPONSIVE = {"sm": "640px", "md": "768px", "lg": "1024px"}

CSS: List[str] = []


def escape(cls: str) -> str:
    return re.sub(r"([:/\.\[\]\(\)'%])", r"\\\\\1", cls)


def hex_to_rgba(hex_value: str, alpha: float | None = None) -> str:
    hex_value = hex_value.lstrip("#")
    if len(hex_value) == 3:
        hex_value = "".join(ch * 2 for ch in hex_value)
    r, g, b = tuple(int(hex_value[i : i + 2], 16) for i in (0, 2, 4))
    if alpha is None:
        return f"rgb({r} {g} {b})"
    return f"rgb({r} {g} {b} / {alpha})"


def resolve_color(token: str) -> str | None:
    match = re.match(r"([a-z-]+)-(\d{2,3})(?:/(\d{1,3}))?", token)
    if match:
        family, shade_str, opacity_str = match.groups()
    else:
        base_match = re.match(r"(white|black)/(\d{1,3})", token)
        if base_match:
            family, shade_str, opacity_str = base_match.group(1), "base", base_match.group(2)
        elif token in ("white", "black"):
            family, shade_str, opacity_str = token, "base", None
        else:
            return None

    family_key = family.replace("-raw", "")
    palette = COLOR_PALETTE.get(family_key)
    if not palette:
        return None
    shade_key: int | str = int(shade_str) if shade_str.isdigit() else shade_str
    base = palette.get(shade_key) if isinstance(palette, dict) else None
    if not base and shade_key == "base":
        base = palette.get("base") if isinstance(palette, dict) else None
    if not base:
        return None

    if opacity_str:
        opacity = int(opacity_str) / 100
        return hex_to_rgba(base, opacity)
    return hex_to_rgba(base)


def add_rule(selector: str, body: str, *, pseudo: str | None = None, media: str | None = None, raw: bool | None = None) -> None:
    if raw is None:
        raw = " " in selector or selector.startswith("group:hover")
    if raw:
        sel = selector if pseudo is None else f"{selector}{pseudo}"
        block = f"{sel} {{{body}}}"
    else:
        base = escape(selector)
        sel = base if pseudo is None else f"{base}{pseudo}"
        block = f".{sel} {{{body}}}"
    if media:
        CSS.append(f"@media (min-width: {media}) {{{block}}}")
    else:
        CSS.append(block)


def add_gradient(selector: str, body: str, media: str | None = None) -> None:
    raw = " " in selector or selector.startswith("group:hover")
    block = f"{selector} {{{body}}}" if raw else f".{escape(selector)} {{{body}}}"
    if media:
        CSS.append(f"@media (min-width: {media}) {{{block}}}")
    else:
        CSS.append(block)


def spacing_value(key: str) -> str | None:
    if key in SPACING:
        return SPACING[key]
    if key.endswith("px"):
        return key
    return None


def fraction_value(fraction: str) -> str | None:
    if "/" in fraction:
        num, denom = fraction.split("/", 1)
        try:
            return f"{(float(num) / float(denom)) * 100:.6f}%"
        except ZeroDivisionError:
            return None
    return None


def handle_size(prefix: str, token: str, value: str, pseudo: str | None, media: str | None):
    prop = "padding"
    if prefix.startswith("m"):
        prop = "margin"
    axis = prefix[1:]  # '', x, y, t, b, l, r
    css_value = spacing_value(value)
    if css_value is None:
        return

    if axis == "":
        body = f"{prop}: {css_value};"
    elif axis == "x":
        body = f"{prop}-left: {css_value}; {prop}-right: {css_value};"
    elif axis == "y":
        body = f"{prop}-top: {css_value}; {prop}-bottom: {css_value};"
    elif axis == "t":
        body = f"{prop}-top: {css_value};"
    elif axis == "b":
        body = f"{prop}-bottom: {css_value};"
    elif axis == "l":
        body = f"{prop}-left: {css_value};"
    elif axis == "r":
        body = f"{prop}-right: {css_value};"
    else:
        return
    add_rule(token, body, pseudo=pseudo, media=media)


def handle_width_height(prefix: str, token: str, raw_value: str, pseudo: str | None, media: str | None):
    prop = "width" if prefix == "w" else "height"
    value = spacing_value(raw_value)
    if value is None and raw_value.endswith("vh"):
        value = raw_value
    if value is None:
        frac = fraction_value(raw_value)
        if frac:
            value = frac
    if value is None and raw_value == "full":
        value = "100%"
    if value is None and raw_value == "screen" and prop == "height":
        value = "100vh"
    if value is None:
        return
    add_rule(token, f"{prop}: {value};", pseudo=pseudo, media=media)


def handle_position(token: str, pseudo: str | None, media: str | None, selector: str | None = None):
    target = selector or token
    mapping = {
        "absolute": "absolute",
        "relative": "relative",
        "fixed": "fixed",
        "sticky": "sticky",
    }
    if token in mapping:
        add_rule(target, f"position: {mapping[token]};", pseudo=pseudo, media=media)

    for side in ("top", "bottom", "left", "right"):
        if token.startswith(f"{side}-"):
            value = token.split("-", 1)[1]
            if value == "1/2":
                resolved = "50%"
            elif value.endswith(".5"):
                resolved = spacing_value(value)
            else:
                resolved = spacing_value(value) or value.replace("[", "").replace("]", "")
            if resolved:
                add_rule(target, f"{side}: {resolved};", pseudo=pseudo, media=media)

    if token.startswith("inset-"):
        value = token.split("-", 1)[1]
        if value == "0":
            add_rule(target, "inset: 0;", pseudo=pseudo, media=media)
        elif value == "y-0":
            add_rule(target, "top: 0; bottom: 0;", pseudo=pseudo, media=media)

    if token.startswith("z-"):
        try:
            z_index = int(token.split("-", 1)[1])
            add_rule(target, f"z-index: {z_index};", pseudo=pseudo, media=media)
        except ValueError:
            pass


def handle_border(token: str, pseudo: str | None, media: str | None, selector: str | None = None):
    widths = {
        "border": "1px",
        "border-2": "2px",
        "border-t": "1px",
        "border-r": "1px",
        "border-b": "1px",
        "border-l": "1px",
    }
    sides = {
        "border": "",
        "border-2": "",
        "border-t": "top",
        "border-r": "right",
        "border-b": "bottom",
        "border-l": "left",
    }
    target = selector or token
    if token in widths:
        width = widths[token]
        side = sides[token]
        prop = "border" if not side else f"border-{side}"
        add_rule(target, f"{prop}: {width} solid currentColor;", pseudo=pseudo, media=media)
        return True
    if token.startswith("border-"):
        color = token.replace("border-", "", 1)
        resolved = resolve_color(color)
        if resolved:
            add_rule(target, f"border-color: {resolved};", pseudo=pseudo, media=media)
            return True
    return False


def handle_ring(token: str, pseudo: str | None, media: str | None, selector: str | None = None):
    if not token.startswith("ring"):
        return False
    target = selector or token
    declarations = []
    if token in RING_WIDTHS:
        declarations.append(f"--tw-ring-width: {RING_WIDTHS[token]};")
    elif token.startswith("ring-"):
        maybe_color = token.replace("ring-", "", 1)
        resolved = resolve_color(maybe_color)
        if resolved:
            declarations.append(f"--tw-ring-color: {resolved};")
    if declarations:
        declarations.append("box-shadow: 0 0 0 var(--tw-ring-width) var(--tw-ring-color);")
        add_rule(target, " ".join(declarations), pseudo=pseudo, media=media)
        return True
    return False


def handle_radius(token: str, pseudo: str | None, media: str | None, selector: str | None = None):
    target = selector or token
    if token in RADIUS:
        add_rule(target, f"border-radius: {RADIUS[token]};", pseudo=pseudo, media=media)
    elif token.startswith("rounded-l-"):
        key = "rounded-" + token.split("-", 2)[2]
        value = RADIUS.get(key)
        if value:
            add_rule(target, f"border-top-left-radius: {value}; border-bottom-left-radius: {value};", pseudo=pseudo, media=media)


def handle_shadow(token: str, pseudo: str | None, media: str | None, selector: str | None = None):
    target = selector or token
    if token in SHADOWS:
        add_rule(target, f"box-shadow: {SHADOWS[token]};", pseudo=pseudo, media=media)
        return
    if token.startswith("shadow-["):
        custom = token[len("shadow-") :].strip("[]")
        add_rule(target, f"box-shadow: {custom};", pseudo=pseudo, media=media)
        return
    if token.startswith("shadow-" ) and "orange" in token:
        color = token.split("shadow-",1)[1]
        rgba = resolve_color(color)
        if rgba:
            add_rule(target, f"box-shadow: 0 10px 15px -3px {rgba};", pseudo=pseudo, media=media)


def handle_text(token: str, pseudo: str | None, media: str | None, selector: str | None = None):
    target = selector or token
    if token in FONT_SIZES:
        size, line = FONT_SIZES[token]
        add_rule(target, f"font-size: {size}; line-height: {line};", pseudo=pseudo, media=media)
        return True
    if re.match(r"text-\[\d+px\]", token):
        value = token[5:].strip("[]")
        add_rule(target, f"font-size: {value};", pseudo=pseudo, media=media)
        return True
    if token in ("text-left", "text-right", "text-center"):
        align = token.split("-")[1]
        add_rule(target, f"text-align: {align};", pseudo=pseudo, media=media)
        return True
    if token.startswith("text-"):
        color = token.replace("text-", "", 1)
        resolved = resolve_color(color)
        if resolved:
            add_rule(target, f"color: {resolved};", pseudo=pseudo, media=media)
            return True
    return False


def handle_bg(token: str, pseudo: str | None, media: str | None, selector: str | None = None):
    target = selector or token
    if token.startswith("bg-gradient-to-"):
        direction_key = token.split("-")[-1]
        direction = {
            "r": "to right",
            "b": "to bottom",
            "br": "to bottom right",
        }.get(direction_key)
        if direction:
            body = "background-image: linear-gradient(" + direction + ", var(--tw-gradient-stops));"
            add_gradient(target, body, media=media)
        return True
    if token.startswith("bg-"):
        color = token.replace("bg-", "", 1)
        resolved = resolve_color(color)
        if resolved:
            add_rule(target, f"background-color: {resolved};", pseudo=pseudo, media=media)
            return True
    return False


def handle_gradient_stop(token: str, pseudo: str | None, media: str | None, selector: str | None = None):
    target = selector or token
    if token.startswith("from-"):
        color = resolve_color(token.replace("from-", "", 1))
        if color:
            body = "--tw-gradient-from: {0}; --tw-gradient-to: rgb(var(--tw-from-rgb, 255 255 255) / 0); --tw-gradient-stops: var(--tw-gradient-from), var(--tw-gradient-to);".format(color)
            add_rule(target, body, pseudo=pseudo, media=media)
            return True
    if token.startswith("via-"):
        color = resolve_color(token.replace("via-", "", 1))
        if color:
            body = "--tw-gradient-stops: var(--tw-gradient-from), {0}, var(--tw-gradient-to);".format(color)
            add_rule(target, body, pseudo=pseudo, media=media)
            return True
    if token.startswith("to-"):
        color = resolve_color(token.replace("to-", "", 1))
        if color:
            body = f"--tw-gradient-to: {color};"
            add_rule(target, body, pseudo=pseudo, media=media)
            return True
    return False


def handle_misc(token: str, pseudo: str | None, media: str | None, selector: str | None = None):
    target = selector or token
    misc_map = {
        "flex": "display: flex;",
        "grid": "display: grid;",
        "block": "display: block;",
        "inline-flex": "display: inline-flex;",
        "inline": "display: inline;",
        "hidden": "display: none;",
        "items-center": "align-items: center;",
        "items-start": "align-items: flex-start;",
        "items-end": "align-items: flex-end;",
        "justify-center": "justify-content: center;",
        "justify-between": "justify-content: space-between;",
        "justify-start": "justify-content: flex-start;",
        "justify-end": "justify-content: flex-end;",
        "overflow-hidden": "overflow: hidden;",
        "overflow-auto": "overflow: auto;",
        "overflow-y-auto": "overflow-y: auto;",
        "truncate": "overflow: hidden; text-overflow: ellipsis; white-space: nowrap;",
        "uppercase": "text-transform: uppercase;",
        "lowercase": "text-transform: lowercase;",
        "capitalize": "text-transform: capitalize;",
        "text-ellipsis": "text-overflow: ellipsis;",
        "whitespace-nowrap": "white-space: nowrap;",
        "break-all": "word-break: break-all;",
        "antialiased": "-webkit-font-smoothing: antialiased; -moz-osx-font-smoothing: grayscale;",
        "select-none": "user-select: none;",
        "pointer-events-none": "pointer-events: none;",
        "fill-current": "fill: currentColor;",
        "backdrop-blur": "backdrop-filter: blur(8px);",
        "backdrop-blur-sm": "backdrop-filter: blur(6px);",
        "backdrop-blur-md": "backdrop-filter: blur(12px);",
    }
    if token in misc_map:
        add_rule(target, misc_map[token], pseudo=pseudo, media=media)
        return True

    if token.startswith("gap-"):
        value = spacing_value(token.split("-", 1)[1])
        if value:
            add_rule(target, f"gap: {value};", pseudo=pseudo, media=media)
            return True
    if token.startswith("grid-cols-" ):
        try:
            count = int(token.split("-")[2])
            add_rule(target, f"grid-template-columns: repeat({count}, minmax(0, 1fr));", pseudo=pseudo, media=media)
            return True
        except ValueError:
            pass
    if token.startswith("col-span-"):
        try:
            span = int(token.split("-")[2])
            add_rule(target, f"grid-column: span {span} / span {span};", pseudo=pseudo, media=media)
            return True
        except ValueError:
            pass
    if token.startswith("space-y-"):
        value = spacing_value(token.split("-")[2])
        if value:
            body = f"--tw-space-y-reverse: 0; margin-top: calc({value} * (1 - var(--tw-space-y-reverse))); margin-bottom: calc({value} * var(--tw-space-y-reverse));"
            CSS.append(
                f".{escape(target)} > :not([hidden]) ~ :not([hidden]) {{{body}}}"
            )
            return True
    if token.startswith("divide-y-"):
        value = spacing_value(token.split("-")[2])
        if value:
            body = f"--tw-divide-y-reverse: 0; border-top-width: calc({value} * (1 - var(--tw-divide-y-reverse))); border-bottom-width: calc({value} * var(--tw-divide-y-reverse)); border-style: solid;"
            CSS.append(
                f".{escape(target)} > :not([hidden]) ~ :not([hidden]) {{{body}}}"
            )
            return True
    if token == "divide-y":
        body = "border-top-width: 1px; border-style: solid;"
        CSS.append(f".{escape(target)} > :not([hidden]) ~ :not([hidden]) {{{body}}}")
        return True
    if token.startswith("divide-"):
        color = resolve_color(token.replace("divide-", "", 1))
        if color:
            body = f"border-color: {color}; border-style: solid; border-top-width: 1px;"
            CSS.append(f".{escape(target)} > :not([hidden]) ~ :not([hidden]) {{{body}}}")
            return True
    if token.startswith("opacity-"):
        try:
            opacity = int(token.split("-")[1]) / 100
            add_rule(target, f"opacity: {opacity};", pseudo=pseudo, media=media)
            return True
        except ValueError:
            pass
    if token.startswith("duration-"):
        try:
            dur = int(token.split("-")[1])
            add_rule(target, f"transition-duration: {dur}ms;", pseudo=pseudo, media=media)
            return True
        except ValueError:
            pass
    if token.startswith("ease-"):
        mapping = {"in-out": "cubic-bezier(0.4, 0, 0.2, 1)"}
        key = token.split("-", 1)[1]
        if key in mapping:
            add_rule(target, f"transition-timing-function: {mapping[key]};", pseudo=pseudo, media=media)
            return True
    if token.startswith("tracking-["):
        value = token[len("tracking-") :].strip("[]")
        add_rule(target, f"letter-spacing: {value};", pseudo=pseudo, media=media)
        return True
    if token.startswith("leading-["):
        value = token[len("leading-") :].strip("[]")
        add_rule(target, f"line-height: {value};", pseudo=pseudo, media=media)
        return True
    if token.startswith("translate-") or "translate" in token:
        mapping = {
            "-translate-x-1/2": "translate(-50%, 0)",
            "-translate-y-1/2": "translate(0, -50%)",
            "hover:-translate-y-0.5": "translateY(-0.125rem)",
            "hover:-translate-y-[1px]": "translateY(-1px)",
        }
        if token in mapping:
            add_rule(target, f"transform: {mapping[token]};", pseudo=pseudo, media=media)
            return True
    if token.startswith("scale-"):
        scale_map = {"scale-125": 1.25, "scale-110": 1.1, "scale-105": 1.05, "scale-95": 0.95}
        value = scale_map.get(token)
        if value:
            add_rule(target, f"transform: scale({value});", pseudo=pseudo, media=media)
            return True
    if token == "transform":
        add_rule(target, "transform: translate(0,0);", pseudo=pseudo, media=media)
        return True
    if token.startswith("transition"):
        add_rule(target, "transition-property: all;", pseudo=pseudo, media=media)
        return True
    return False


def collect_tokens() -> Iterable[str]:
    tokens = set()
    for path in TEMPLATES_DIR.rglob("*.html"):
        text = path.read_text()
        for attr in re.findall(r'(?:class|:class)\s*=\s*"([^"]*)"', text):
            tokens.update(attr.replace("\n", " ").split())
        for attr in re.findall(r"'([^']*)'", text):
            if any(key in attr for key in ("bg-", "text-", "border-", "hover:", "focus:", "active:", "ring-", "shadow", "rounded", "px-", "py-", "mt-", "mb-", "ml-", "mr-", "grid", "flex", "w-", "h-", "gap-", "tracking-", "leading-", "from-", "to-", "via-")):
                tokens.update(attr.split())
    # add manual tokens used in scripts
    tokens.update(["group", "group-hover:scale-110", "file:bg-orange-50", "file:px-3", "file:py-2", "file:text-sm", "file:border", "file:border-orange-100", "file:rounded-lg"])
    return tokens


def process_token(raw_token: str):
    pseudo = None
    media = None
    token = raw_token
    selector_override = None

    for prefix, breakpoint in RESPONSIVE.items():
        if raw_token.startswith(prefix + ":"):
            media = breakpoint
            token = raw_token[len(prefix) + 1 :]
            break

    for pfx in ("hover:", "focus:", "active:", "group-hover:", "file:"):
        if token.startswith(pfx):
            token = token[len(pfx) :]
            if pfx == "group-hover:":
                selector_override = f"group:hover .{escape('group-hover:' + token)}"
            elif pfx == "file:":
                selector_override = raw_token
                pseudo = "::file-selector-button"
            else:
                pseudo = ":" + pfx.rstrip(":")
            break

    if token == "group":
        add_rule("group", "position: relative;", pseudo=None, media=media)
        return

    selector = selector_override or token

    if handle_bg(token, pseudo, media if selector_override is None else None, selector=selector):
        return
    if handle_gradient_stop(token, pseudo, media if selector_override is None else None, selector=selector):
        return
    if handle_text(token, pseudo, media if selector_override is None else None, selector=selector):
        return
    if token in FONT_WEIGHTS:
        value = FONT_WEIGHTS[token]
        prop = "font-family" if token == "font-mono" else "font-weight"
        add_rule(selector if selector_override else (raw_token if raw_token.startswith(("hover:", "focus:", "active:", "group-hover:")) else token), f"{prop}: {value};", pseudo=pseudo, media=media)
        return
    if token in LETTER_SPACING:
        add_rule(selector if selector_override else (raw_token if pseudo else token), f"letter-spacing: {LETTER_SPACING[token]};", pseudo=pseudo, media=media)
        return
    if token in LINE_HEIGHT:
        add_rule(selector if selector_override else (raw_token if pseudo else token), f"line-height: {LINE_HEIGHT[token]};", pseudo=pseudo, media=media)
        return
    if handle_border(token, pseudo, media if selector_override is None else None, selector=selector):
        return
    if token.startswith("p") or token.startswith("m"):
        match = re.match(r"([mp][trblxy]?)-(.+)", token)
        if match:
            handle_size(match.group(1), selector if selector_override else (raw_token if pseudo or media else token), match.group(2), pseudo, media)
            return
    if token.startswith("w-"):
        handle_width_height("w", selector if selector_override else (raw_token if pseudo or media else token), token[2:], pseudo, media if selector_override is None else None)
        return
    if token.startswith("h-"):
        handle_width_height("h", selector if selector_override else (raw_token if pseudo or media else token), token[2:], pseudo, media if selector_override is None else None)
        return
    if token.startswith("min-") or token.startswith("max-"):
        prop = "min-width" if token.startswith("min-w") else "min-height" if token.startswith("min-h") else "max-width" if token.startswith("max-w") else "max-height"
        value = token.split("-", 2)[2]
        if value in ("full", "screen"):
            css_val = "100%" if value == "full" else "100vh"
        elif value.startswith("["):
            css_val = value.strip("[]")
        elif value in SPACING:
            css_val = SPACING[value]
        else:
            sizes = {
                "xs": "20rem",
                "sm": "24rem",
                "md": "28rem",
                "lg": "32rem",
                "xl": "36rem",
                "2xl": "42rem",
                "3xl": "48rem",
                "4xl": "56rem",
                "5xl": "64rem",
                "6xl": "72rem",
            }
            css_val = sizes.get(value)
        if css_val:
            add_rule(selector if selector_override else (raw_token if pseudo or media else token), f"{prop}: {css_val};", pseudo=pseudo, media=media if selector_override is None else None)
            return
    if handle_radius(token, pseudo, media if selector_override is None else None, selector=selector):
        return
    if handle_ring(token, pseudo, media if selector_override is None else None, selector=selector):
        return
    if handle_shadow(token, pseudo, media if selector_override is None else None, selector=selector):
        return
    if handle_misc(token, pseudo, media if selector_override is None else None, selector=selector):
        return
    handle_position(token, pseudo, media if selector_override is None else None, selector=selector)


def main():
    CSS.append("*{box-sizing:border-box;}")
    CSS.append("body{margin:0;}")
    CSS.append(":root{--tw-ring-width:1px;--tw-ring-color:rgb(59 130 246 / 0.5);}")
    for token in sorted(collect_tokens()):
        process_token(token)
    OUTPUT_PATH.write_text("\n".join(CSS))
    print(f"Wrote {len(CSS)} rules to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
