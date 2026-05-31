import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import logging
from typing import Callable, Optional

from .components import THEME, StyledButton, Divider, SectionHeader

# Optional Pillow support for image resizing
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except Exception:
    Image = None
    ImageTk = None
    PIL_AVAILABLE = False

logger = logging.getLogger(__name__)


SERVICES = [
    "Enrollment Payment (Tuition & Fees)",
    "Partial Payment / Installment",
    "Down Payment & Reservation",
    "Miscellaneous Fees (Library, Lab, etc.)",
    "Graduation Fee Payment",
    "Releasing of Official Receipt",
    "Request for Statement of Account",
    "Payment for Lost ID / Book",
    "Scholarship & Discount Validation",
    "Sports / Cultural Enrollment Fee",
    "Summer Class Payment",
    "Re-enrollment Payment (Back Subjects)",
    "Payment for Transcript of Records (TOR)",
    "Assessment Dispute / Adjustment",
    "Cash Advance for School Activities",
    "Payment for School Uniform / Equipment",
]

# Priority categories with their codes and order
PRIORITIES: dict[str, dict] = {
    "PWD": {"code": "P", "order": 0, "label": "👥 PWD (Person with Disability)"},
    "Senior Citizen": {"code": "S", "order": 1, "label": "👴 Senior Citizen"},
    "Pregnant": {"code": "M", "order": 2, "label": "🤰 Pregnant"},
    "Regular": {"code": "R", "order": 3, "label": "👤 Regular Customer"},
}


class QueueWindow(tk.Toplevel):
    """Toplevel dialog for ticket generation with landscape card layout."""

    def __init__(
        self,
        parent: tk.Widget,
        on_ticket_created: Optional[Callable[[dict], None]] = None,
        counter: Optional[dict[str, int]] = None,
        daily_limit: Optional[int] = None,
        tickets_issued_today: int = 0,
        app_name_var: Optional[tk.StringVar] = None,
        app_logo_var: Optional[tk.StringVar] = None,
        **kwargs
    ) -> None:
        super().__init__(parent, **kwargs)
        self.title("Get a Queue Ticket")
        self.geometry("900x750")
        self.minsize(800, 650)
        self.configure(bg=THEME["bg_dark"])

        self._callback = on_ticket_created
        self._daily_limit = daily_limit
        self._tickets_issued_today = tickets_issued_today
        if counter is None:
            self._counter: dict[str, int] = {
                "current": 0,
                "pwd": 0,
                "senior": 0,
                "pregnant": 0,
                "regular": 0
            }
        else:
            self._counter = counter
            for priority in PRIORITIES:
                key = priority.lower().replace(" ", "_")
                if key not in self._counter:
                    self._counter[key] = 0

        self._selected_service = tk.StringVar(value=SERVICES[0])
        self._selected_priority = tk.StringVar(value="Regular")
        self._last_ticket: Optional[dict] = None
        self._app_name_var = app_name_var
        self._app_logo_var = app_logo_var

        self._build()

    def _build(self):
        pad = THEME["pad"]

        # Header
        hdr = tk.Frame(self, bg=THEME["bg_card"], pady=14)
        hdr.pack(fill="x")
        # Logo + header text
        self._logo_image = None
        logo_lbl = tk.Label(hdr, bg=THEME["bg_card"])
        logo_lbl.pack(side="left", padx=(pad, 8))

        if getattr(self, "_app_name_var", None) is not None:
            title_text = f"◈  {self._app_name_var.get()} Ticket"
            self._hdr_title_var = tk.StringVar(value=title_text)
            try:
                self._app_name_var.trace_add("write", lambda *a: self._hdr_title_var.set(f"◈  {self._app_name_var.get()} Ticket"))
            except Exception:
                pass
            tk.Label(
                hdr, textvariable=self._hdr_title_var,
                font=("Segoe UI", 15, "bold"),
                fg=THEME["accent"], bg=THEME["bg_card"],
            ).pack(padx=pad, anchor="w")
        else:
            tk.Label(
                hdr, text="◈  Queue Ticket",
                font=("Segoe UI", 15, "bold"),
                fg=THEME["accent"], bg=THEME["bg_card"],
            ).pack(padx=pad, anchor="w")

        def _update_logo(*a):
            path = (self._app_logo_var.get() if self._app_logo_var else "")
            try:
                if path:
                    max_h = 48
                    max_w = 240
                    if PIL_AVAILABLE:
                        try:
                            im = Image.open(path)
                            w, h = im.size
                            ratio = min(1.0, float(max_w) / max(1, w), float(max_h) / max(1, h))
                            if ratio < 1.0:
                                new_w = max(1, int(w * ratio))
                                new_h = max(1, int(h * ratio))
                                im = im.resize((new_w, new_h), Image.LANCZOS)
                            img = ImageTk.PhotoImage(im)
                        except Exception:
                            img = tk.PhotoImage(file=path)
                            try:
                                w, h = img.width(), img.height()
                                factor = max(1, int(max(1, h) / max_h), int(max(1, w) / max_w))
                                if factor > 1:
                                    img = img.subsample(factor, factor)
                            except Exception:
                                pass
                    else:
                        img = tk.PhotoImage(file=path)
                        try:
                            w, h = img.width(), img.height()
                            factor = max(1, int(max(1, h) / max_h), int(max(1, w) / max_w))
                            if factor > 1:
                                img = img.subsample(factor, factor)
                        except Exception:
                            pass
                    self._logo_image = img
                    logo_lbl.config(image=self._logo_image)
                else:
                    logo_lbl.config(image="")
                    self._logo_image = None
            except Exception:
                logo_lbl.config(image="")
                self._logo_image = None

        if self._app_logo_var is not None:
            try:
                self._app_logo_var.trace_add("write", _update_logo)
            except Exception:
                pass
        _update_logo()
        Divider(self).pack(fill="x")

        # Main content area with two columns
        main_container = tk.Frame(self, bg=THEME["bg_dark"])
        main_container.pack(fill="both", expand=True, padx=pad, pady=pad)
        
        # Left column - Priority selection
        left_col = tk.Frame(main_container, bg=THEME["bg_dark"])
        left_col.pack(side="left", fill="both", expand=True, padx=(0, pad//2))
        
        # Right column - Service selection (landscape cards)
        right_col = tk.Frame(main_container, bg=THEME["bg_dark"])
        right_col.pack(side="left", fill="both", expand=True, padx=(pad//2, 0))
        
        self._build_left_column(left_col, pad)
        self._build_right_column(right_col, pad)

        # Bottom area - Preview and buttons
        bottom_frame = tk.Frame(self, bg=THEME["bg_dark"])
        bottom_frame.pack(fill="x", padx=pad, pady=(0, pad))
        
        self._build_preview(bottom_frame, pad)
        self._build_buttons(bottom_frame, pad)

    def refresh_theme(self):
        """Refresh this ticket window using the current theme."""
        self.configure(bg=THEME["bg_dark"])
        for child in self.winfo_children():
            child.destroy()
        self._build()

    def _build_left_column(self, parent, pad):
        """Build priority selection column."""
        # Priority section
        priority_frame = tk.Frame(parent, bg=THEME["bg_card"], padx=pad, pady=pad)
        priority_frame.pack(fill="x", pady=(0, pad))
        
        SectionHeader(priority_frame, "Customer Category",
                      "Select your priority category").pack(anchor="w", pady=(0, 10))
        
        for priority_key, priority_info in PRIORITIES.items():
            rb_frame = tk.Frame(priority_frame, bg=THEME["bg_card"])
            rb_frame.pack(fill="x", pady=8)
            
            color_map = {
                "PWD": THEME["accent"],
                "Senior Citizen": THEME["warning"],
                "Pregnant": "#9B59B6",
                "Regular": THEME["text_dim"]
            }
            color = color_map.get(priority_key, THEME["text_dim"])
            
            rb = tk.Radiobutton(
                rb_frame,
                text=priority_info["label"],
                variable=self._selected_priority,
                value=priority_key,
                font=("Segoe UI", 11),
                fg=color,
                bg=THEME["bg_card"],
                activebackground=THEME["bg_card"],
                activeforeground=color,
                selectcolor=THEME["bg_input"],
                indicatoron=True,
                cursor="hand2",
            )
            rb.pack(anchor="w", padx=20)
            
            if priority_key in ["PWD", "Senior Citizen", "Pregnant"]:
                badge = tk.Label(
                    rb_frame,
                    text="⭐ PRIORITY",
                    font=("Segoe UI", 8, "bold"),
                    fg=color,
                    bg=THEME["bg_card"]
                )
                badge.pack(anchor="w", padx=(35, 0))

    def _build_right_column(self, parent, pad):
        """Build service selection column with landscape card layout."""
        # Service selection with scrollable canvas
        service_header = tk.Frame(parent, bg=THEME["bg_dark"])
        service_header.pack(fill="x", pady=(0, 5))
        
        SectionHeader(service_header, "Select Service",
                      "Click on any card to choose your service").pack(anchor="w")
        
        # Scrollable area for service cards
        canvas = tk.Canvas(parent, bg=THEME["bg_dark"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        
        services_frame = tk.Frame(canvas, bg=THEME["bg_dark"])
        canvas_window = canvas.create_window((0, 0), window=services_frame, anchor="nw")
        
        # Configure grid for landscape cards (2 columns)
        for i in range(2):  # 2 columns for landscape layout
            services_frame.columnconfigure(i, weight=1)
        
        def on_canvas_configure(e):
            canvas.itemconfig(canvas_window, width=e.width)
            # Adjust number of columns based on width
            width = e.width
            if width > 600:
                cols = 2
            else:
                cols = 1
            for widget in services_frame.winfo_children():
                widget.grid_configure()
        
        canvas.bind("<Configure>", on_canvas_configure)
        services_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        
        # Create service cards
        self._service_cards = {}
        for idx, service in enumerate(SERVICES):
            row = idx // 2
            col = idx % 2
            card = self._create_service_card(services_frame, service, idx)
            card.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
            self._service_cards[service] = card

    def _create_service_card(self, parent, service_name, idx):
        """Create a clickable landscape card for a service."""
        card = tk.Frame(
            parent,
            bg=THEME["bg_card"],
            relief="flat",
            bd=1,
            highlightthickness=1,
            highlightcolor=THEME["accent"],
            highlightbackground=THEME["border"],
            cursor="hand2",
            padx=12,
            pady=12
        )
        
        # Icon based on service type
        icon = self._get_service_icon(service_name)
        
        # Left side - Icon
        icon_label = tk.Label(
            card,
            text=icon,
            font=("Segoe UI", 24),
            fg=THEME["accent"],
            bg=THEME["bg_card"]
        )
        icon_label.pack(side="left", padx=(0, 12))
        
        # Right side - Text
        text_frame = tk.Frame(card, bg=THEME["bg_card"])
        text_frame.pack(side="left", fill="both", expand=True)
        
        # Service name
        name_label = tk.Label(
            text_frame,
            text=service_name,
            font=("Segoe UI", 10, "bold"),
            fg=THEME["text"],
            bg=THEME["bg_card"],
            wraplength=250,
            justify="left"
        )
        name_label.pack(anchor="w")
        
        # Brief description
        desc = self._get_service_description(service_name)
        desc_label = tk.Label(
            text_frame,
            text=desc,
            font=("Segoe UI", 8),
            fg=THEME["text_dim"],
            bg=THEME["bg_card"],
            wraplength=250,
            justify="left"
        )
        desc_label.pack(anchor="w", pady=(2, 0))
        
        # Selection indicator
        self._update_card_selection(card, service_name == self._selected_service.get())
        
        # Bind click event
        card.bind("<Button-1>", lambda e, s=service_name: self._select_service(s))
        for child in [icon_label, text_frame, name_label, desc_label]:
            child.bind("<Button-1>", lambda e, s=service_name: self._select_service(s))
        
        return card

    def _get_service_icon(self, service_name):
        """Return appropriate icon for service type."""
        icons = {
            "Enrollment": "📚",
            "Payment": "💰",
            "Installment": "💳",
            "Reservation": "📝",
            "Library": "📖",
            "Graduation": "🎓",
            "Receipt": "🧾",
            "Statement": "📄",
            "Lost": "🆔",
            "Scholarship": "🏆",
            "Sports": "⚽",
            "Summer": "☀️",
            "Transcript": "📜",
            "Dispute": "⚖️",
            "Cash": "💵",
            "Uniform": "👕"
        }
        for key, icon in icons.items():
            if key in service_name:
                return icon
        return "📋"

    def _get_service_description(self, service_name):
        """Return brief description for service."""
        descriptions = {
            "Enrollment Payment": "Pay tuition and other enrollment fees",
            "Partial Payment": "Make installment payments",
            "Down Payment": "Pay initial down payment",
            "Miscellaneous Fees": "Library, lab, and other fees",
            "Graduation Fee": "Pay graduation-related fees",
            "Releasing": "Get your official receipt",
            "Statement of Account": "Request account summary",
            "Lost ID": "Pay for lost ID or book replacement",
            "Scholarship": "Validate scholarship eligibility",
            "Summer Class": "Pay summer class fees",
            "Re-enrollment": "Pay for back subjects",
            "Transcript": "Request and pay for TOR",
            "Dispute": "Resolve assessment issues",
            "Cash Advance": "Request cash for activities",
            "Uniform": "Pay for school uniform/equipment"
        }
        for key, desc in descriptions.items():
            if key in service_name:
                return desc
        return "Select this service"

    def _update_card_selection(self, card, is_selected):
        """Update card appearance based on selection."""
        if is_selected:
            card.configure(bg=THEME["accent"], highlightbackground=THEME["accent"])
            for child in card.winfo_children():
                if isinstance(child, tk.Frame):
                    child.configure(bg=THEME["accent"])
                    for grandchild in child.winfo_children():
                        grandchild.configure(bg=THEME["accent"])
                else:
                    child.configure(bg=THEME["accent"])
                    if isinstance(child, tk.Label) and child != card.winfo_children()[0]:
                        child.configure(fg=THEME["text"])
        else:
            card.configure(bg=THEME["bg_card"], highlightbackground=THEME["border"])
            for child in card.winfo_children():
                if isinstance(child, tk.Frame):
                    child.configure(bg=THEME["bg_card"])
                    for grandchild in child.winfo_children():
                        grandchild.configure(bg=THEME["bg_card"])
                        if isinstance(grandchild, tk.Label):
                            if "icon" not in str(grandchild):
                                grandchild.configure(fg=THEME["text"])
                            else:
                                grandchild.configure(fg=THEME["accent"])
                else:
                    child.configure(bg=THEME["bg_card"])
                    if isinstance(child, tk.Label) and child != card.winfo_children()[0]:
                        child.configure(fg=THEME["accent"])

    def _select_service(self, service_name):
        """Handle service selection."""
        self._selected_service.set(service_name)
        # Update all cards
        for service, card in self._service_cards.items():
            self._update_card_selection(card, service == service_name)

    def _build_preview(self, parent, pad):
        """Build ticket preview area."""
        self._preview_frame = tk.Frame(parent, bg=THEME["bg_card"], padx=20, pady=16)
        self._preview_frame.pack(fill="x", pady=(0, pad))
        self._preview_label = tk.Label(
            self._preview_frame,
            text="Your ticket will appear here",
            font=THEME["font_body"],
            fg=THEME["text_dim"],
            bg=THEME["bg_card"],
        )
        self._preview_label.pack()

    def _build_buttons(self, parent, pad):
        """Build action buttons."""
        btn_row = tk.Frame(parent, bg=THEME["bg_dark"])
        btn_row.pack(fill="x")
        
        StyledButton(btn_row, "Get Ticket  →", preset="primary",
                     command=self._generate_ticket, width=18).pack(side="left", padx=(0, 10))
        StyledButton(btn_row, "Close", preset="muted",
                     command=self.destroy).pack(side="right")

    def _generate_ticket(self):
        if self._daily_limit is not None and self._tickets_issued_today >= self._daily_limit:
            messagebox.showwarning(
                "Daily Ticket Limit Reached",
                f"The daily ticket limit of {self._daily_limit} has already been reached.",
                parent=self,
            )
            return

        service = self._selected_service.get()
        priority = self._selected_priority.get()
        prefix = PRIORITIES[priority]["code"]
        
        counter_key = priority.lower().replace(" ", "_")
        self._counter[counter_key] = self._counter.get(counter_key, 0) + 1
        self._counter["current"] += 1
        
        number = f"{prefix}-{self._counter[counter_key]:03d}"
        now_str = datetime.now().strftime("%H:%M")
        today_str = datetime.now().date().isoformat()

        ticket = {
            "number": number,
            "service": service,
            "priority": priority,
            "priority_code": prefix,
            "priority_order": PRIORITIES[priority]["order"],
            "status": "waiting",
            "time": now_str,
            "date": today_str,
        }
        self._last_ticket = ticket

        # Update preview
        for w in self._preview_frame.winfo_children():
            w.destroy()

        priority_colors = {
            "PWD": THEME["accent"],
            "Senior Citizen": THEME["warning"],
            "Pregnant": "#9B59B6",
            "Regular": THEME["text_dim"]
        }
        
        priority_frame = tk.Frame(self._preview_frame, bg=THEME["bg_card"])
        priority_frame.pack()
        
        priority_label = tk.Label(
            priority_frame,
            text=f"⭐ {priority}",
            font=("Segoe UI", 10, "bold"),
            fg=priority_colors.get(priority, THEME["text_dim"]),
            bg=THEME["bg_card"]
        )
        priority_label.pack()
        
        tk.Label(
            self._preview_frame,
            text=number,
            font=THEME["font_ticket"],
            fg=THEME["accent"],
            bg=THEME["bg_card"],
        ).pack()
        tk.Label(
            self._preview_frame,
            text=service,
            font=THEME["font_body"],
            fg=THEME["text"],
            bg=THEME["bg_card"],
        ).pack(pady=(4, 0))
        tk.Label(
            self._preview_frame,
            text=f"Issued at {now_str}  ·  Please wait for your number to be called",
            font=THEME["font_small"],
            fg=THEME["text_dim"],
            bg=THEME["bg_card"],
        ).pack(pady=(4, 0))
        
        if priority in ["PWD", "Senior Citizen", "Pregnant"]:
            tk.Label(
                self._preview_frame,
                text="🔔 Priority queue - you will be served next in your category",
                font=("Segoe UI", 9, "italic"),
                fg=priority_colors.get(priority),
                bg=THEME["bg_card"]
            ).pack(pady=(8, 0))

        if callable(self._callback):
            self._callback(ticket)
        self._tickets_issued_today += 1


if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    root.configure(bg=THEME["bg_dark"])

    def _on_ticket(t):
        print("Ticket created:", t)

    win = QueueWindow(root, on_ticket_created=_on_ticket)
    root.mainloop()
