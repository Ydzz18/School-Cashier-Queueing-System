"""
Global design tokens for the Queue Management System UI.

All colours, fonts, and spacing live here so every module stays consistent.
Use THEME dictionary throughout the application for consistent styling.

Example:
    from app.ui.components.theme import THEME
    label = tk.Label(root, bg=THEME["bg_dark"], fg=THEME["text"])
"""

THEME = {
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