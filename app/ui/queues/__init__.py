"""QueueFlow Queues Package

Queue management UI components for the Queue Management System.

This package contains queue-specific UI modules:

Example:
    from app.ui.queues import QueueWindow, AdminPanel

Package Structure:
    ├── __init__.py           (this file - component exports)
    ├── queue_window.py       → QueueWindow class (ticket generation)
    ├── admin_panel.py        → AdminPanel class (staff management)
    └── components/
        ├── __init__.py       (component exports - theme, widgets)
        ├── theme.py          → THEME dictionary (colors, fonts)
        └── widgets.py        → Reusable components (buttons, cards, badges)
"""

# Export queue-related UI classes
from .components import THEME, StyledButton, TicketCard, StatusBadge, SectionHeader, Divider
from .queue_window import QueueWindow
from .admin_panel import AdminPanel

__all__ = [
    "QueueWindow",
    "AdminPanel",
    "THEME",
    "StyledButton",
    "TicketCard",
    "StatusBadge",
    "SectionHeader",
    "Divider",
]
