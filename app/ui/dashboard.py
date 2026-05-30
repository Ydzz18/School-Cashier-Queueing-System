"""
app/ui/dashboard.py
───────────────────
Main dashboard view for the Queue Management System.

Layout
------
┌─────────────────────────────────────────────────────────┐
│  Header bar  (title + nav buttons)                      │
├──────────────────────┬──────────────────────────────────┤
│  NOW SERVING panel   │  QUEUE LIST (scrollable)         │
│                      │                                  │
│  Big ticket number   │  TicketCard × N                  │
│  Service name        │                                  │
│  Counter info        │                                  │
├──────────────────────┴──────────────────────────────────┤
│  Footer stats bar   (waiting · called · completed)      │
└─────────────────────────────────────────────────────────┘
"""

import tkinter as tk
from tkinter import ttk
from datetime import datetime
import logging
from typing import Callable, Optional

from .components import THEME, StyledButton, TicketCard, Divider, SectionHeader

logger = logging.getLogger(__name__)

# STARTING WITH EMPTY QUEUE
_SAMPLE_TICKETS: list[dict] = []


class Dashboard(tk.Frame):
    CLOCK_UPDATE_INTERVAL = 1000

    def __init__(
        self,
        master: tk.Widget,
        tickets: Optional[list[dict]] = None,
        open_queue_cb: Optional[Callable[[], None]] = None,
        open_admin_cb: Optional[Callable[[], None]] = None,
        **kwargs
    ) -> None:

        super().__init__(master, bg=THEME["bg_dark"], **kwargs)
        self.tickets = tickets if tickets is not None else _SAMPLE_TICKETS
        self._open_queue = open_queue_cb
        self._open_admin = open_admin_cb
        self._clock_label: Optional[tk.Label] = None

        try:
            self._build()
            self._tick_clock()
            logger.info("Dashboard initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize dashboard: {e}", exc_info=True)
            raise

    # ── Build ─────────────────────────────────────────────────────────────────
    def _build(self):
        self._build_header()
        self._build_body()
        self._build_footer()

    def _build_header(self):
        bar = tk.Frame(self, bg=THEME["bg_card"], pady=0)
        bar.pack(fill="x")

        # Left – logo / title
        tk.Label(
            bar,
            text="  ◈  QueueFlow",
            font=("Segoe UI", 16, "bold"),
            fg=THEME["accent"],
            bg=THEME["bg_card"],
            pady=14,
        ).pack(side="left", padx=THEME["pad"])

        # Right – clock + nav buttons
        right = tk.Frame(bar, bg=THEME["bg_card"])
        right.pack(side="right", padx=THEME["pad"])

        self._clock_label = tk.Label(
            right,
            font=THEME["font_small"],
            fg=THEME["text_dim"],
            bg=THEME["bg_card"],
        )
        self._clock_label.pack(side="left", padx=(0, 16))

        StyledButton(right, "＋  New Ticket",  preset="primary",
                     command=self._open_queue).pack(side="left", padx=4)
        StyledButton(right, "⚙  Admin Panel", preset="muted",
                     command=self._open_admin).pack(side="left", padx=4)

        Divider(self).pack(fill="x")

    def _build_body(self):
        body = tk.Frame(self, bg=THEME["bg_dark"])
        body.pack(fill="both", expand=True, padx=THEME["pad"], pady=THEME["pad"])

        # Left – Now Serving
        self._build_now_serving(body)

        # Separator
        tk.Frame(body, bg=THEME["border"], width=1).pack(
            side="left", fill="y", padx=THEME["pad"]
        )

        # Right – Queue list
        self._build_queue_list(body)

    def _build_now_serving(self, parent):
        panel = tk.Frame(parent, bg=THEME["bg_dark"], width=260)
        panel.pack(side="left", fill="y", pady=4)
        panel.pack_propagate(False)

        SectionHeader(panel, "NOW SERVING",
                      "Currently at the counter").pack(anchor="w", pady=(0, 16))

        # Card
        card = tk.Frame(panel, bg=THEME["bg_card"], padx=24, pady=20)
        card.pack(fill="x")

        serving = next(
            (t for t in self.tickets if t["status"] == "called"),
            {"number": "—", "service": "No active ticket", "time": "", "priority": "Regular"},
        )

        # Show priority icon for serving ticket
        priority_icons = {
            "PWD": "⭐",
            "Senior Citizen": "👴",
            "Pregnant": "🤰",
            "Regular": "👤"
        }
        priority_icon = priority_icons.get(serving.get("priority", "Regular"), "👤")
        
        tk.Label(
            card,
            text=f"{priority_icon} {serving['number']}",
            font=THEME["font_ticket"],
            fg=THEME["accent"],
            bg=THEME["bg_card"],
        ).pack()

        tk.Label(
            card,
            text=serving["service"],
            font=THEME["font_body"],
            fg=THEME["text"],
            bg=THEME["bg_card"],
        ).pack(pady=(4, 0))

        tk.Label(
            card,
            text=f"Called at {serving['time']}" if serving["time"] else "",
            font=THEME["font_small"],
            fg=THEME["text_dim"],
            bg=THEME["bg_card"],
        ).pack()

        # Mini stats below card
        stats_frame = tk.Frame(panel, bg=THEME["bg_dark"])
        stats_frame.pack(fill="x", pady=(16, 0))

        waiting_count   = sum(1 for t in self.tickets if t["status"] == "waiting")
        completed_count = sum(1 for t in self.tickets if t["status"] == "completed")

        self._mini_stat(stats_frame, str(waiting_count),   "Waiting")
        self._mini_stat(stats_frame, str(completed_count), "Done today")

    def _mini_stat(self, parent, value, label):
        f = tk.Frame(parent, bg=THEME["bg_card"], padx=12, pady=8)
        f.pack(side="left", padx=(0, 8), fill="x", expand=True)
        tk.Label(f, text=value, font=THEME["font_sub"],
                 fg=THEME["text"], bg=THEME["bg_card"]).pack()
        tk.Label(f, text=label, font=THEME["font_small"],
                 fg=THEME["text_dim"], bg=THEME["bg_card"]).pack()

    def _get_priority_order(self, ticket):
        """Return priority value for sorting (lower number = higher priority)"""
        priority_map = {
            "PWD": 0,
            "Senior Citizen": 1,
            "Pregnant": 2,
            "Regular": 3
        }
        return priority_map.get(ticket.get("priority", "Regular"), 4)

    def _build_queue_list(self, parent):
        right = tk.Frame(parent, bg=THEME["bg_dark"])
        right.pack(side="left", fill="both", expand=True)

        SectionHeader(right, "QUEUE", f"{len(self.tickets)} tickets").pack(
            anchor="w", pady=(0, 12)
        )

        # Scrollable area
        canvas = tk.Canvas(right, bg=THEME["bg_dark"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(right, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        inner = tk.Frame(canvas, bg=THEME["bg_dark"])
        win = canvas.create_window((0, 0), window=inner, anchor="nw")

        def _on_resize(e):
            canvas.itemconfig(win, width=e.width)
        canvas.bind("<Configure>", _on_resize)

        inner.bind("<Configure>",
                   lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        # Sort tickets by priority for display
        sorted_tickets = sorted(self.tickets, key=self._get_priority_order)
        
        # Show message when queue is empty
        if not self.tickets:
            empty_label = tk.Label(
                inner,
                text="✨ No tickets in queue\n\nClick 'New Ticket' to get started",
                font=("Segoe UI", 12),
                fg=THEME["text_dim"],
                bg=THEME["bg_dark"],
                justify="center"
            )
            empty_label.pack(expand=True, fill="both", pady=50)
        else:
            for ticket in sorted_tickets:
                card = TicketCard(inner, ticket)
                card.pack(fill="x", pady=2)

    def _build_footer(self):
        Divider(self).pack(fill="x")
        bar = tk.Frame(self, bg=THEME["bg_card"], pady=8)
        bar.pack(fill="x")

        statuses = ["waiting", "called", "completed", "skipped"]
        for s in statuses:
            count = sum(1 for t in self.tickets if t["status"] == s)
            colour = THEME["status"].get(s, THEME["muted"])
            lbl = tk.Label(
                bar,
                text=f"● {s.capitalize()}  {count}",
                font=THEME["font_small"],
                fg=colour,
                bg=THEME["bg_card"],
            )
            lbl.pack(side="left", padx=THEME["pad"])

    # ── Clock ─────────────────────────────────────────────────────────────────
    def _tick_clock(self):
        now = datetime.now().strftime("%A, %d %b %Y  %H:%M:%S")
        if self._clock_label:
            self._clock_label.config(text=now)
        self.after(1000, self._tick_clock)

    # ── Public API ────────────────────────────────────────────────────────────
    def refresh(self, tickets: list):
        """Re-render with an updated ticket list."""
        self.tickets = tickets
        for widget in self.winfo_children():
            widget.destroy()
        self._build()
        self._tick_clock()


# ── Standalone preview ────────────────────────────────────────────────────────
if __name__ == "__main__":
    root = tk.Tk()
    root.title("QueueFlow – Dashboard")
    root.geometry("900x580")
    root.configure(bg=THEME["bg_dark"])
    Dashboard(root).pack(fill="both", expand=True)
    root.mainloop()
