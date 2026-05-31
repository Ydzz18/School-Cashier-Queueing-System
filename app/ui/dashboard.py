"""
app/ui/dashboard.py
───────────────────
Main dashboard view for the Queue Management System.

Layout
------
┌─────────────────────────────────────────────────────────┐
│  Header bar  (title + nav buttons)                      │
├──────────────────────┬──────────────────────────────────┤
│  COUNTERS panel      │  QUEUE LIST (scrollable)         │
│  (multiple cards)    │                                  │
│  Counter 1  Counter2 │  TicketCard × N                  │
├──────────────────────┴──────────────────────────────────┤
│  Footer stats bar   (waiting · called · completed)      │
└─────────────────────────────────────────────────────────┘
"""

import tkinter as tk
from tkinter import ttk
from datetime import datetime
import logging
from typing import Callable, Optional, List

from .components import THEME, StyledButton, TicketCard, Divider, SectionHeader
from app.models.counter import Counter

logger = logging.getLogger(__name__)

# STARTING WITH EMPTY QUEUE
_SAMPLE_TICKETS: list[dict] = []
_SAMPLE_COUNTERS: list[Counter] = []


class Dashboard(tk.Frame):
    CLOCK_UPDATE_INTERVAL = 1000

    def __init__(
        self,
        master: tk.Widget,
        tickets: Optional[list[dict]] = None,
        counters: Optional[List[Counter]] = None,
        open_queue_cb: Optional[Callable[[], None]] = None,
        open_admin_cb: Optional[Callable[[], None]] = None,
        open_counters_cb: Optional[Callable[[], None]] = None,
        **kwargs
    ) -> None:

        super().__init__(master, bg=THEME["bg_dark"], **kwargs)
        self.tickets = tickets if tickets is not None else _SAMPLE_TICKETS
        self.counters = counters if counters is not None else _SAMPLE_COUNTERS
        self._open_queue = open_queue_cb
        self._open_admin = open_admin_cb
        self._open_counters = open_counters_cb
        self._clock_label: Optional[tk.Label] = None
        self._clock_after_id: Optional[str] = None

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
        StyledButton(right, "⚙  Counters", preset="muted",
                     command=self._open_counters).pack(side="left", padx=4)
        StyledButton(right, "⚙  Admin Panel", preset="muted",
                     command=self._open_admin).pack(side="left", padx=4)

        Divider(self).pack(fill="x")

    def _build_body(self):
        body = tk.Frame(self, bg=THEME["bg_dark"])
        body.pack(fill="both", expand=True, padx=THEME["pad"], pady=THEME["pad"])

        # Left – Counters display
        self._build_counters_display(body)

        # Separator
        tk.Frame(body, bg=THEME["border"], width=1).pack(
            side="left", fill="y", padx=THEME["pad"]
        )

        # Right – Queue list
        self._build_queue_list(body)

    def _build_counters_display(self, parent):
        """Display all active counters with current tickets."""
        panel = tk.Frame(parent, bg=THEME["bg_dark"], width=260)
        panel.pack(side="left", fill="both", expand=True, pady=4)
        
        active_counters = [counter for counter in self.counters if counter.is_active]

        SectionHeader(panel, "COUNTERS",
                      f"{len(active_counters)} active").pack(anchor="w", pady=(0, 12))
        
        # If no counters, show message
        if not active_counters:
            tk.Label(
                panel,
                text="No counters configured\nClick ⚙ Counters to add",
                font=("Segoe UI", 10),
                fg=THEME["text_dim"],
                bg=THEME["bg_dark"],
                justify="center"
            ).pack(pady=20)
            
            # Mini stats
            stats_frame = tk.Frame(panel, bg=THEME["bg_dark"])
            stats_frame.pack(fill="x", pady=(16, 0))
            waiting_count = sum(1 for t in self.tickets if t["status"] == "waiting")
            completed_count = sum(1 for t in self.tickets if t["status"] == "completed")
            self._mini_stat(stats_frame, str(waiting_count), "Waiting")
            self._mini_stat(stats_frame, str(completed_count), "Done")
            return
        
        # Create scrollable area for counters
        canvas = tk.Canvas(panel, bg=THEME["bg_dark"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(panel, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        
        inner = tk.Frame(canvas, bg=THEME["bg_dark"])
        
        def _on_resize(e):
            canvas.itemconfig(win, width=e.width)
        
        win = canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.bind("<Configure>", _on_resize)
        
        inner.bind("<Configure>",
                   lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        
        # Draw counter cards
        for counter in active_counters:
            self._draw_counter_card(inner, counter)
        
        # Mini stats at bottom
        stats_frame = tk.Frame(panel, bg=THEME["bg_dark"])
        stats_frame.pack(fill="x", pady=(12, 0))
        waiting_count = sum(1 for t in self.tickets if t["status"] == "waiting")
        completed_count = sum(1 for t in self.tickets if t["status"] == "completed")
        self._mini_stat(stats_frame, str(waiting_count), "Waiting")
        self._mini_stat(stats_frame, str(completed_count), "Done")
    
    def _draw_counter_card(self, parent, counter: Counter):
        """Draw a single counter card."""
        card = tk.Frame(parent, bg=THEME["bg_card"], padx=16, pady=12)
        card.pack(fill="x", pady=6)
        
        # Counter name
        tk.Label(
            card,
            text=counter.counter_name,
            font=("Segoe UI", 12, "bold"),
            fg=THEME["accent"],
            bg=THEME["bg_card"],
        ).pack(anchor="w")
        
        # Department
        if counter.department:
            tk.Label(
                card,
                text=counter.department,
                font=("Segoe UI", 9),
                fg=THEME["text_dim"],
                bg=THEME["bg_card"],
            ).pack(anchor="w")
        
        # Current ticket
        if counter.current_ticket_id:
            ticket = next((t for t in self.tickets if t.get("ticket_id") == counter.current_ticket_id or t.get("number") == counter.current_ticket_id), None)
            if ticket:
                priority_icon = self._get_priority_icon(ticket.get("priority", "Regular"))
                tk.Label(
                    card,
                    text=f"{priority_icon} Serving: {ticket.get('number', '—')}",
                    font=("Segoe UI", 10),
                    fg=THEME["success"],
                    bg=THEME["bg_card"],
                ).pack(anchor="w", pady=(6, 0))
            else:
                tk.Label(
                    card,
                    text="• No ticket assigned",
                    font=("Segoe UI", 9),
                    fg=THEME["text_dim"],
                    bg=THEME["bg_card"],
                ).pack(anchor="w", pady=(6, 0))
        else:
            tk.Label(
                card,
                text="• Idle - Ready for next customer",
                font=("Segoe UI", 9),
                fg=THEME["text_dim"],
                bg=THEME["bg_card"],
            ).pack(anchor="w", pady=(6, 0))
        
        # Operator and stats
        info_text = f"Served today: {counter.tickets_served_today}"
        if counter.operator_name:
            info_text = f"{counter.operator_name} • {info_text}"
        
        tk.Label(
            card,
            text=info_text,
            font=("Segoe UI", 8),
            fg=THEME["text_dim"],
            bg=THEME["bg_card"],
        ).pack(anchor="w", pady=(4, 0))
    
    def _get_priority_icon(self, priority: str) -> str:
        """Get emoji icon for priority."""
        icons = {
            "PWD": "⭐",
            "Senior Citizen": "👴",
            "Pregnant": "🤰",
            "Regular": "👤"
        }
        return icons.get(priority, "👤")

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
        self._clock_after_id = self.after(self.CLOCK_UPDATE_INTERVAL, self._tick_clock)

    # ── Public API ────────────────────────────────────────────────────────────
    def refresh(self, tickets: list = None, counters: List[Counter] = None):
        """Re-render with updated ticket and counter lists.
        
        Args:
            tickets: Updated ticket list
            counters: Updated counter list
        """
        if tickets is not None:
            self.tickets = tickets
        if counters is not None:
            self.counters = counters

        if self._clock_after_id:
            try:
                self.after_cancel(self._clock_after_id)
            except tk.TclError:
                pass
            self._clock_after_id = None
        
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
