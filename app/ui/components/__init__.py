"""QueueFlow UI Components Package

Reusable UI components and design system for the Queue Management System.

This sub-package provides:
- Design tokens (colors, fonts, spacing)
- Reusable widget components (buttons, cards, badges)

Example:
    from app.ui.components import THEME, StyledButton, TicketCard

Package Structure:
    ├── __init__.py    (this file - component exports)
    ├── theme.py       → THEME: Global design tokens
    └── widgets.py     → StyledButton, TicketCard, StatusBadge, etc.

Usage:
    # Import theme
    from app.ui.components import THEME
    label = tk.Label(root, bg=THEME["bg_dark"], fg=THEME["text"])
    
    # Import widgets
    from app.ui.components import StyledButton
    button = StyledButton(root, "Click Me", preset="primary")
"""

# Export design system and widgets
from .theme import THEME, apply_theme_mode, refresh_widget_theme
from .widgets import StyledButton, TicketCard, StatusBadge, SectionHeader, Divider

__all__ = [
    "THEME",
    "apply_theme_mode",
    "refresh_widget_theme",
    "StyledButton",
    "TicketCard",
    "StatusBadge",
    "SectionHeader",
    "Divider",
]
