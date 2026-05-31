"""
Global design tokens for the Queue Management System UI.

All colours, fonts, and spacing live here so every module stays consistent.
Use THEME dictionary throughout the application for consistent styling.

Example:
    from app.ui.components.theme import THEME
    label = tk.Label(root, bg=THEME["bg_dark"], fg=THEME["text"])
"""

import tkinter as tk
from tkinter import ttk

DARK_THEME = {
    # ── Palette ──────────────────────────────────────────────────────────────
    "bg_dark":      "#0F1117",   # app background
    "bg_card":      "#1A1D27",   # card / panel surface
    "bg_input":     "#252836",   # entry fields
    "accent":       "#4F8EF7",   # primary blue
    "accent_hover": "#3A72D4",
    "success":      "#2ECC71",
    "warning":      "#F39C12",
    "danger":       "#E74C3C",
    "danger_hover": "#C0392B",
    "muted":        "#5A6070",
    "text":         "#E8EAF0",
    "text_dim":     "#8A90A0",
    "border":       "#2A2D3E",

    # ── Typography ───────────────────────────────────────────────────────────
    "font_heading": ("Segoe UI", 22, "bold"),
    "font_sub":     ("Segoe UI", 14, "bold"),
    "font_body":    ("Segoe UI", 11),
    "font_small":   ("Segoe UI", 9),
    "font_ticket":  ("Courier New", 36, "bold"),   # big queue number
    "font_label":   ("Segoe UI", 10, "bold"),

    # ── Spacing ───────────────────────────────────────────────────────────────
    "pad":  16,
    "pad_s": 8,
    "radius": 8,         # used in canvas-drawn widgets

    # ── Status colours map ────────────────────────────────────────────────────
    "status": {
        "waiting":    "#F39C12",
        "called":     "#4F8EF7",
        "completed":  "#2ECC71",
        "skipped":    "#E74C3C",
    }
}

LIGHT_THEME = {
    "bg_dark":      "#F5F7FA",
    "bg_card":      "#FFFFFF",
    "bg_input":     "#EBF0F5",
    "accent":       "#4F8EF7",
    "accent_hover": "#3A72D4",
    "success":      "#2ECC71",
    "warning":      "#F39C12",
    "danger":       "#E74C3C",
    "danger_hover": "#C0392B",
    "muted":        "#7F8C8D",
    "text":         "#2C3E50",
    "text_dim":     "#7F8C8D",
    "border":       "#D7DBDD",
    "status": {
        "waiting":    "#F39C12",
        "called":     "#4F8EF7",
        "completed":  "#2ECC71",
        "skipped":    "#E74C3C",
    }
}

THEME = DARK_THEME.copy()


def apply_theme_mode(mode: str = "dark"):
    """Apply the selected theme mode to the shared design tokens."""
    mode = (mode or "dark").lower()
    source = DARK_THEME if mode == "dark" else LIGHT_THEME
    THEME.update(source)


def _theme_key_for_color(color: str) -> str | None:
    for theme in (DARK_THEME, LIGHT_THEME):
        for key, value in theme.items():
            if isinstance(value, dict):
                continue
            if value == color:
                return key
    return None


def refresh_widget_theme(widget):
    """Update an existing widget tree to use the current theme colours."""
    try:
        cfg = widget.configure()
        if "bg" in cfg:
            try:
                current = widget.cget("bg")
                key = _theme_key_for_color(current)
                if key:
                    widget.configure(bg=THEME.get(key, current))
            except tk.TclError:
                pass
        if "fg" in cfg:
            try:
                current = widget.cget("fg")
                key = _theme_key_for_color(current)
                if key:
                    widget.configure(fg=THEME.get(key, current))
            except tk.TclError:
                pass
        if "highlightbackground" in cfg:
            try:
                current = widget.cget("highlightbackground")
                key = _theme_key_for_color(current)
                if key:
                    widget.configure(highlightbackground=THEME.get(key, current))
            except tk.TclError:
                pass
        if "highlightcolor" in cfg:
            try:
                current = widget.cget("highlightcolor")
                key = _theme_key_for_color(current)
                if key:
                    widget.configure(highlightcolor=THEME.get(key, current))
            except tk.TclError:
                pass
        if "activebackground" in cfg:
            try:
                current = widget.cget("activebackground")
                key = _theme_key_for_color(current)
                if key:
                    widget.configure(activebackground=THEME.get(key, current))
            except tk.TclError:
                pass
        if "activeforeground" in cfg:
            try:
                current = widget.cget("activeforeground")
                key = _theme_key_for_color(current)
                if key:
                    widget.configure(activeforeground=THEME.get(key, current))
            except tk.TclError:
                pass
        if isinstance(widget, tk.Entry):
            widget.configure(bg=THEME["bg_input"], fg=THEME["text"], insertbackground=THEME["text"])
        if hasattr(widget, "refresh_style"):
            try:
                widget.refresh_style()
            except Exception:
                pass
    except Exception:
        pass

    for child in widget.winfo_children():
        refresh_widget_theme(child)

    try:
        if isinstance(widget, ttk.Treeview):
            style = ttk.Style()
            style.configure(
                "Queue.Treeview",
                background=THEME["bg_card"],
                foreground=THEME["text"],
                fieldbackground=THEME["bg_card"],
            )
            style.configure(
                "Queue.Treeview.Heading",
                background=THEME["bg_input"],
                foreground=THEME["text_dim"],
            )
        if isinstance(widget, ttk.Combobox):
            style = ttk.Style()
            style.configure(
                "TCombobox",
                fieldbackground=THEME["bg_input"],
                background=THEME["bg_input"],
                foreground=THEME["text"],
            )
    except Exception:
        pass
