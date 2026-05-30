"""Reusable Tkinter widgets for the Queue Management System.

Provides styled components with consistent theming:
- StyledButton: Flat button with presets (primary, success, danger, warning, muted)
- TicketCard: Card displaying ticket information with priority indicators
- StatusBadge: Colored label for ticket status (waiting, called, completed, skipped)
- SectionHeader: Bold section title with optional subtitle
- Divider: Horizontal visual separator
"""

import tkinter as tk
import logging
from typing import Callable, Optional

from .theme import THEME

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
class StyledButton(tk.Button):
    """
    A flat, styled button that supports colour presets:
      preset="primary"  → accent blue
      preset="success"  → green
      preset="danger"   → red
      preset="muted"    → grey ghost
    """

    PRESETS = {
        "primary": (THEME["accent"],       THEME["accent_hover"],  THEME["text"]),
        "success": (THEME["success"],      "#27AE60",              THEME["text"]),
        "danger":  (THEME["danger"],       THEME["danger_hover"],  THEME["text"]),
        "warning": (THEME["warning"],      "#D68910",              THEME["text"]),
        "muted":   (THEME["bg_input"],     THEME["border"],        THEME["text_dim"]),
    }

    def __init__(self, master, text="", preset="primary", command=None,
                 width=None, **kwargs):
        bg, hover_bg, fg = self.PRESETS.get(preset, self.PRESETS["primary"])
        self._bg       = bg
        self._hover_bg = hover_bg

        opts = dict(
            text=text,
            bg=bg,
            fg=fg,
            activebackground=hover_bg,
            activeforeground=fg,
            relief="flat",
            borderwidth=0,
            cursor="hand2",
            font=THEME["font_label"],
            padx=THEME["pad"],
            pady=THEME["pad_s"],
            command=command,
        )
        if width:
            opts["width"] = width
        opts.update(kwargs)
        super().__init__(master, **opts)

        self.bind("<Enter>", lambda _: self.config(bg=self._hover_bg))
        self.bind("<Leave>", lambda _: self.config(bg=self._bg))


# ─────────────────────────────────────────────────────────────────────────────
class TicketCard(tk.Frame):
    """
    A card that shows a single ticket's number, service, priority, and status.

    Parameters
    ----------
    ticket : dict  e.g. {"number": "P-001", "service": "Billing", "priority": "PWD", "status": "waiting"}
    """

    def __init__(self, master, ticket: dict, **kwargs):
        super().__init__(
            master,
            bg=THEME["bg_card"],
            relief="flat",
            bd=0,
            padx=THEME["pad"],
            pady=THEME["pad_s"],
            **kwargs,
        )
        self._build(ticket)

    def _build(self, ticket):
        # Priority indicator and color
        priority = ticket.get("priority", "Regular")
        priority_icons = {
            "PWD": "⭐",
            "Senior Citizen": "👴",
            "Pregnant": "🤰",
            "Regular": "👤"
        }
        priority_colors = {
            "PWD": THEME["accent"],
            "Senior Citizen": THEME["warning"],
            "Pregnant": "#9B59B6",
            "Regular": THEME["text_dim"]
        }
        
        icon = priority_icons.get(priority, "👤")
        color = priority_colors.get(priority, THEME["text_dim"])
        
        # Left – ticket number with priority icon
        num_frame = tk.Frame(self, bg=THEME["bg_card"])
        num_frame.grid(row=0, column=0, rowspan=2, padx=(0, 12), sticky="ns")
        
        priority_label = tk.Label(
            num_frame,
            text=icon,
            font=("Segoe UI", 12),
            fg=color,
            bg=THEME["bg_card"]
        )
        priority_label.pack()
        
        num_label = tk.Label(
            num_frame,
            text=ticket.get("number", "—"),
            font=("Courier New", 16, "bold"),
            fg=THEME["accent"],
            bg=THEME["bg_card"],
        )
        num_label.pack()

        # Middle – service name and priority text
        info_frame = tk.Frame(self, bg=THEME["bg_card"])
        info_frame.grid(row=0, column=1, rowspan=2, sticky="w")
        
        svc_label = tk.Label(
            info_frame,
            text=ticket.get("service", "General"),
            font=THEME["font_label"],
            fg=THEME["text"],
            bg=THEME["bg_card"],
            anchor="w",
        )
        svc_label.pack(anchor="w")
        
        # Priority text
        priority_text = tk.Label(
            info_frame,
            text=f"({priority})",
            font=THEME["font_small"],
            fg=color,
            bg=THEME["bg_card"],
            anchor="w",
        )
        priority_text.pack(anchor="w")

        # Time
        time_str = ticket.get("time", "")
        time_label = tk.Label(
            self,
            text=time_str,
            font=THEME["font_small"],
            fg=THEME["text_dim"],
            bg=THEME["bg_card"],
            anchor="w",
        )
        time_label.grid(row=0, column=2, padx=(10, 0), sticky="w")

        # Right – status badge
        badge = StatusBadge(self, status=ticket.get("status", "waiting"))
        badge.grid(row=0, column=3, rowspan=2, padx=(12, 0), sticky="e")

        self.columnconfigure(1, weight=1)

        # Subtle bottom border
        sep = tk.Frame(self, bg=THEME["border"], height=1)
        sep.grid(row=2, column=0, columnspan=4, sticky="ew", pady=(THEME["pad_s"], 0))


# ─────────────────────────────────────────────────────────────────────────────
class StatusBadge(tk.Label):
    """Small coloured pill label for a ticket status."""

    def __init__(self, master, status: str = "waiting", **kwargs):
        colour = THEME["status"].get(status.lower(), THEME["muted"])
        super().__init__(
            master,
            text=status.upper(),
            font=THEME["font_small"],
            fg=colour,
            bg=THEME["bg_card"],
            **kwargs,
        )


# ─────────────────────────────────────────────────────────────────────────────
class SectionHeader(tk.Frame):
    """Bold section title with an optional dim subtitle."""

    def __init__(self, master, title: str, subtitle: str = "", **kwargs):
        super().__init__(master, bg=THEME["bg_dark"], **kwargs)

        tk.Label(
            self,
            text=title,
            font=THEME["font_sub"],
            fg=THEME["text"],
            bg=THEME["bg_dark"],
        ).pack(anchor="w")

        if subtitle:
            tk.Label(
                self,
                text=subtitle,
                font=THEME["font_small"],
                fg=THEME["text_dim"],
                bg=THEME["bg_dark"],
            ).pack(anchor="w")


# ─────────────────────────────────────────────────────────────────────────────
class Divider(tk.Frame):
    """1-pixel horizontal rule."""

    def __init__(self, master, **kwargs):
        super().__init__(master, bg=THEME["border"], height=1, **kwargs)
