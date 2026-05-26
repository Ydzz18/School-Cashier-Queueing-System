"""QueueFlow UI Package

Main user interface components for the Queue Management System.

This package contains all UI modules and makes them easily importable:

Example:
    from app.ui import Dashboard, QueueWindow, AdminPanel, THEME

Package Structure:
    ├── __init__.py           (this file - main UI exports)
    ├── dashboard.py          → Dashboard class (main display)
    ├── queue_window.py       → QueueWindow class (ticket generation)
    ├── admin_panel.py        → AdminPanel class (staff management)
    └── components/
        ├── __init__.py       (component exports - theme, widgets)
        ├── theme.py          → THEME dictionary (colors, fonts)
        └── widgets.py        → Reusable components (buttons, cards, badges)
"""

# Export main UI classes for easy importing
from .components import THEME, StyledButton, TicketCard, StatusBadge, SectionHeader, Divider
from .dashboard import Dashboard
from .queue_window import QueueWindow
from .admin_panel import AdminPanel

__all__ = [
    "Dashboard",
    "QueueWindow",
    "AdminPanel",
    "THEME",
    "StyledButton",
    "TicketCard",
    "StatusBadge",
    "SectionHeader",
    "Divider",
]
