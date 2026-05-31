"""
app/ui/admin_panel.py
─────────────────────
Staff Admin Panel – manage the queue in real time.

Actions per ticket
------------------
  ▶ Call      – pull the next waiting ticket to "called"
  ↩ Recall    – call a previously skipped ticket again
  ✗ Skip      – mark as skipped (goes to bottom / skipped list)
  ✔ Complete  – mark as completed and clear counter

Layout
------
┌──────────────────────────────────────────────────────────┐
│  Header                                                  │
├──────────────────┬───────────────────────────────────────┤
│  Action bar      │  Ticket table (scrollable)            │
│  ─────────────── │                                       │
│  [▶ Call Next]   │  # | Number | Service | Status | Act  │
│  Counter info    │  ──┼────────┼─────────┼────────┼────  │
│                  │   …rows…                              │
└──────────────────┴───────────────────────────────────────┘

Usage
-----
    from app.ui.admin_panel import AdminPanel
    AdminPanel(parent, tickets=my_list, on_change=my_callback)
"""

"""Admin panel module with authentication and ticket management.

Provides secure admin authentication with password hashing and
ticket management capabilities for staff members.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import copy
import hashlib
import json
import os
import logging
from typing import Callable, Optional

from .components import THEME, StyledButton, Divider, SectionHeader, StatusBadge
from .counter_config import CounterConfigDialog
from app.services.counter_service import CounterService

# Optional Pillow support for image resizing
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except Exception:
    Image = None
    ImageTk = None
    PIL_AVAILABLE = False

logger = logging.getLogger(__name__)


class AdminAuth:
    """Handles admin authentication with password hashing and account lockout.
    
    Features:
    - SHA-256 password hashing (with future bcrypt support)
    - Failed login tracking
    - Account lockout after 5 failed attempts (15 minutes)
    - Persistent configuration storage
    """
    
    # Security constants
    CONFIG_FILE = "admin_config.json"
    MAX_FAILED_ATTEMPTS = 5
    LOCKOUT_DURATION = 900  # 15 minutes in seconds
    MIN_PASSWORD_LENGTH = 6
    
    def __init__(self) -> None:
        """Initialize authentication handler and load configuration."""
        self.config: dict = {}
        self._load_config()
        logger.info("AdminAuth initialized")
    
    def _load_config(self) -> None:
        """Load admin credentials from config file.
        
        Raises:
            Exception: If config file is corrupted (falls back to defaults)
        """
        default_config = {
            "admin": {
                "username": "admin",
                "password_hash": self._hash_password("admin123"),  # Default password
                "failed_attempts": 0,
                "locked_until": None
            }
        }
        
        if os.path.exists(self.CONFIG_FILE):
            try:
                with open(self.CONFIG_FILE, 'r') as f:
                    self.config = json.load(f)
                logger.info(f"Configuration loaded from {self.CONFIG_FILE}")
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Failed to load config file: {e}. Using defaults.")
                self.config = default_config
        else:
            self.config = default_config
            self._save_config()
    
    def _save_config(self) -> None:
        """Save admin credentials to config file.
        
        Raises:
            IOError: If file cannot be written
        """
        try:
            with open(self.CONFIG_FILE, 'w') as f:
                json.dump(self.config, f, indent=2)
            # Set secure permissions on Unix-like systems
            try:
                os.chmod(self.CONFIG_FILE, 0o600)
            except OSError as e:
                logger.warning(f"Could not set secure permissions on config file: {e}")
            logger.info(f"Configuration saved to {self.CONFIG_FILE}")
        except IOError as e:
            logger.error(f"Failed to save config file: {e}", exc_info=True)
            raise
    
    def _hash_password(self, password: str) -> str:
        """Create SHA-256 hash of password.
        
        TODO: Upgrade to bcrypt or argon2 for production use.
        
        Args:
            password: Plaintext password to hash
            
        Returns:
            Hexadecimal SHA-256 hash
        """
        if not isinstance(password, str):
            raise TypeError(f"Password must be string, got {type(password).__name__}")
        return hashlib.sha256(password.encode()).hexdigest()
    
    def verify_password(self, username: str, password: str) -> bool:
        """Verify username and password with account lockout support.
        
        Args:
            username: Admin username
            password: Admin password (plaintext)
            
        Returns:
            True if credentials are valid, False otherwise
        """
        if not isinstance(username, str) or not isinstance(password, str):
            logger.warning(f"Invalid credential types provided")
            return False
        
        if username not in self.config:
            logger.warning(f"Login attempt with non-existent username: {username}")
            return False
        
        admin_data = self.config[username]
        
        # Check if account is locked
        if admin_data.get("locked_until"):
            locked_until = admin_data["locked_until"]
            if isinstance(locked_until, (int, float)) and datetime.now().timestamp() < locked_until:
                logger.warning(f"Login attempt on locked account: {username}")
                return False
            else:
                # Unlock account
                admin_data["locked_until"] = None
                admin_data["failed_attempts"] = 0
                logger.info(f"Account unlocked: {username}")
        
        # Verify password
        if admin_data["password_hash"] == self._hash_password(password):
            admin_data["failed_attempts"] = 0
            self._save_config()
            logger.info(f"Successful login: {username}")
            return True
        else:
            admin_data["failed_attempts"] = admin_data.get("failed_attempts", 0) + 1
            attempts = admin_data["failed_attempts"]
            
            # Lock account after max failed attempts
            if attempts >= self.MAX_FAILED_ATTEMPTS:
                admin_data["locked_until"] = datetime.now().timestamp() + self.LOCKOUT_DURATION
                logger.warning(f"Account locked after {attempts} failed attempts: {username}")
                messagebox.showerror("Account Locked", 
                                    f"Too many failed attempts. Account locked for {self.LOCKOUT_DURATION // 60} minutes.")
            else:
                logger.warning(f"Failed login attempt ({attempts}/{self.MAX_FAILED_ATTEMPTS}): {username}")
            
            self._save_config()
            return False
    
    def change_password(self, username: str, old_password: str, new_password: str) -> bool:
        """Change admin password after verifying old password.
        
        Args:
            username: Admin username
            old_password: Current password for verification
            new_password: New password to set
            
        Returns:
            True if password changed successfully, False otherwise
        """
        if not self.verify_password(username, old_password):
            logger.warning(f"Password change attempt failed - invalid old password: {username}")
            return False
        
        if not isinstance(new_password, str) or len(new_password) < self.MIN_PASSWORD_LENGTH:
            messagebox.showerror("Weak Password", 
                                f"Password must be at least {self.MIN_PASSWORD_LENGTH} characters long.")
            logger.warning(f"Weak password provided: {username}")
            return False
        
        try:
            self.config[username]["password_hash"] = self._hash_password(new_password)
            self._save_config()
            logger.info(f"Password changed successfully: {username}")
            return True
        except Exception as e:
            logger.error(f"Failed to change password: {e}", exc_info=True)
            return False


class LoginDialog(tk.Toplevel):
    """Login dialog for admin panel"""
    
    def __init__(self, parent, auth: AdminAuth):
        super().__init__(parent)
        self.title("Admin Login")
        self.geometry("400x300")
        self.configure(bg=THEME["bg_dark"])
        self.resizable(False, False)
        self.grab_set()
        
        self.auth = auth
        self.authenticated = False
        
        self._build()
        self.center_window()
        
        # Bind Enter key to login
        self.bind('<Return>', lambda e: self._login())
    
    def center_window(self):
        """Center the window on screen"""
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (self.winfo_width() // 2)
        y = (self.winfo_screenheight() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")
    
    def _build(self):
        # Header
        header_frame = tk.Frame(self, bg=THEME["bg_card"], height=80)
        header_frame.pack(fill="x")
        
        tk.Label(
            header_frame,
            text="🔐 Admin Access",
            font=("Segoe UI", 18, "bold"),
            fg=THEME["accent"],
            bg=THEME["bg_card"]
        ).pack(pady=20)
        
        # Main content
        main_frame = tk.Frame(self, bg=THEME["bg_dark"])
        main_frame.pack(fill="both", expand=True, padx=40, pady=30)
        
        # Username
        tk.Label(
            main_frame,
            text="Username",
            font=THEME["font_label"],
            fg=THEME["text"],
            bg=THEME["bg_dark"]
        ).pack(anchor="w", pady=(0, 5))
        
        self.username_entry = tk.Entry(
            main_frame,
            font=("Segoe UI", 11),
            bg=THEME["bg_input"],
            fg=THEME["text"],
            insertbackground=THEME["accent"],
            relief="flat",
            highlightthickness=1,
            highlightcolor=THEME["accent"],
            highlightbackground=THEME["border"]
        )
        self.username_entry.pack(fill="x", pady=(0, 15))
        self.username_entry.focus()
        
        # Password
        tk.Label(
            main_frame,
            text="Password",
            font=THEME["font_label"],
            fg=THEME["text"],
            bg=THEME["bg_dark"]
        ).pack(anchor="w", pady=(0, 5))
        
        self.password_entry = tk.Entry(
            main_frame,
            font=("Segoe UI", 11),
            bg=THEME["bg_input"],
            fg=THEME["text"],
            insertbackground=THEME["accent"],
            relief="flat",
            show="•",
            highlightthickness=1,
            highlightcolor=THEME["accent"],
            highlightbackground=THEME["border"]
        )
        self.password_entry.pack(fill="x", pady=(0, 20))
        
        # Buttons
        button_frame = tk.Frame(main_frame, bg=THEME["bg_dark"])
        button_frame.pack(fill="x")
        
        StyledButton(
            button_frame,
            "Login",
            preset="primary",
            command=self._login
        ).pack(side="left", padx=(0, 10))
        
        StyledButton(
            button_frame,
            "Cancel",
            preset="muted",
            command=self.destroy
        ).pack(side="left")
        
        # Error message
        self.error_label = tk.Label(
            main_frame,
            text="",
            font=("Segoe UI", 9),
            fg="#e74c3c",
            bg=THEME["bg_dark"]
        )
        self.error_label.pack(pady=(15, 0))
    
    def _login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        
        if not username or not password:
            self.error_label.config(text="Please enter both username and password")
            return
        
        if self.auth.verify_password(username, password):
            self.authenticated = True
            self.destroy()
        else:
            self.error_label.config(text="Invalid username or password")
            self.password_entry.delete(0, tk.END)
            self.password_entry.focus()


class PasswordChangeDialog(tk.Toplevel):
    """Dialog for changing admin password"""
    
    def __init__(self, parent, auth: AdminAuth, username: str):
        super().__init__(parent)
        self.title("Change Password")
        self.geometry("400x350")
        self.configure(bg=THEME["bg_dark"])
        self.resizable(False, False)
        self.grab_set()
        
        self.auth = auth
        self.username = username
        self.changed = False
        
        self._build()
        self.center_window()
    
    def center_window(self):
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (self.winfo_width() // 2)
        y = (self.winfo_screenheight() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")
    
    def _build(self):
        main_frame = tk.Frame(self, bg=THEME["bg_dark"])
        main_frame.pack(fill="both", expand=True, padx=30, pady=30)
        
        tk.Label(
            main_frame,
            text="Change Admin Password",
            font=("Segoe UI", 14, "bold"),
            fg=THEME["accent"],
            bg=THEME["bg_dark"]
        ).pack(pady=(0, 20))
        
        # Old password
        tk.Label(
            main_frame,
            text="Current Password",
            font=THEME["font_label"],
            fg=THEME["text"],
            bg=THEME["bg_dark"]
        ).pack(anchor="w", pady=(0, 5))
        
        self.old_password = tk.Entry(
            main_frame,
            font=("Segoe UI", 11),
            bg=THEME["bg_input"],
            fg=THEME["text"],
            show="•",
            relief="flat"
        )
        self.old_password.pack(fill="x", pady=(0, 15))
        
        # New password
        tk.Label(
            main_frame,
            text="New Password (min. 6 characters)",
            font=THEME["font_label"],
            fg=THEME["text"],
            bg=THEME["bg_dark"]
        ).pack(anchor="w", pady=(0, 5))
        
        self.new_password = tk.Entry(
            main_frame,
            font=("Segoe UI", 11),
            bg=THEME["bg_input"],
            fg=THEME["text"],
            show="•",
            relief="flat"
        )
        self.new_password.pack(fill="x", pady=(0, 15))
        
        # Confirm password
        tk.Label(
            main_frame,
            text="Confirm New Password",
            font=THEME["font_label"],
            fg=THEME["text"],
            bg=THEME["bg_dark"]
        ).pack(anchor="w", pady=(0, 5))
        
        self.confirm_password = tk.Entry(
            main_frame,
            font=("Segoe UI", 11),
            bg=THEME["bg_input"],
            fg=THEME["text"],
            show="•",
            relief="flat"
        )
        self.confirm_password.pack(fill="x", pady=(0, 20))
        
        # Buttons
        button_frame = tk.Frame(main_frame, bg=THEME["bg_dark"])
        button_frame.pack(fill="x")
        
        StyledButton(
            button_frame,
            "Change Password",
            preset="primary",
            command=self._change_password
        ).pack(side="left", padx=(0, 10))
        
        StyledButton(
            button_frame,
            "Cancel",
            preset="muted",
            command=self.destroy
        ).pack(side="left")
        
        self.message_label = tk.Label(
            main_frame,
            text="",
            font=("Segoe UI", 9),
            bg=THEME["bg_dark"]
        )
        self.message_label.pack(pady=(15, 0))
    
    def _change_password(self):
        old = self.old_password.get()
        new = self.new_password.get()
        confirm = self.confirm_password.get()
        
        if not old or not new or not confirm:
            self.message_label.config(text="Please fill all fields", fg="#e74c3c")
            return
        
        if new != confirm:
            self.message_label.config(text="New passwords do not match", fg="#e74c3c")
            return
        
        if len(new) < 6:
            self.message_label.config(text="Password must be at least 6 characters", fg="#e74c3c")
            return
        
        if self.auth.change_password(self.username, old, new):
            self.message_label.config(text="Password changed successfully!", fg="#2ecc71")
            self.changed = True
            self.after(1500, self.destroy)
        else:
            self.message_label.config(text="Current password is incorrect", fg="#e74c3c")
            self.old_password.delete(0, tk.END)


class AdminPanel(tk.Toplevel):
    """
    Staff admin panel as a Toplevel window with authentication.

    Parameters
    ----------
    parent    : tk widget
    tickets   : list[dict]  – mutable list shared with the rest of the app
    on_change : callable(tickets)  – fired after every state mutation
    """

    def __init__(
        self,
        parent,
        tickets: list = None,
        daily_ticket_limit: int = None,
        on_change=None,
        counter_service: Optional[CounterService] = None,
        on_counters_change: Optional[Callable] = None,
        on_limit_change: Optional[Callable[[int], None]] = None,
        on_app_name_change: Optional[Callable[[str], None]] = None,
        on_theme_mode_change: Optional[Callable[[str], None]] = None,
        app_name: str = "QueueFlow",
        app_name_var: Optional[tk.StringVar] = None,
        app_logo_var: Optional[tk.StringVar] = None,
        on_app_logo_change: Optional[Callable[[str], None]] = None,
        theme_mode: str = "dark",
        **kwargs
    ):
        # First authenticate
        self.auth = AdminAuth()
        
        # Show login dialog
        login_dialog = LoginDialog(parent, self.auth)
        parent.wait_window(login_dialog)
        
        if not login_dialog.authenticated:
            # Authentication failed, don't create admin panel
            return
        
        super().__init__(parent, **kwargs)
        self.title("Admin Panel – Queue Management")
        self.geometry("900x650")
        self.configure(bg=THEME["bg_dark"])
        
        # Work on a deep copy so caller controls when it's applied
        self._tickets  = copy.deepcopy(tickets or [])
        self._callback = on_change
        self.counter_service = counter_service
        self._counters_callback = on_counters_change
        self.username = "admin"  # Store username for password changes
        
        self._current_number_var = tk.StringVar(value="—")
        self._current_svc_var    = tk.StringVar(value="No active ticket")
        self._counter_var = tk.StringVar(value="")
        self._daily_ticket_limit = daily_ticket_limit if daily_ticket_limit is not None else 0
        self._limit_callback = on_limit_change
        self._daily_limit_var = tk.StringVar(value=str(self._daily_ticket_limit))
        self._app_name_change_callback = on_app_name_change
        self._app_logo_change_callback = on_app_logo_change
        self._theme_mode_change_callback = on_theme_mode_change
        # Use provided StringVar to keep headers in sync across windows
        if app_name_var is not None:
            self._app_name_var = app_name_var
        else:
            self._app_name_var = tk.StringVar(value=app_name)
        if app_logo_var is not None:
            self._app_logo_var = app_logo_var
        else:
            self._app_logo_var = tk.StringVar(value="")
        self._theme_mode_var = tk.StringVar(value=theme_mode)
        self._counter_select_widget = None

        self._build()
        self._refresh_table()
        
        # Bind logout on window close
        self.protocol("WM_DELETE_WINDOW", self._on_close)
    
    def _on_close(self):
        """Handle window close"""
        self.destroy()
    
    # ── Build ─────────────────────────────────────────────────────────────────
    def _build(self):
        self._build_header()
        
        panes = tk.Frame(self, bg=THEME["bg_dark"])
        panes.pack(fill="both", expand=True,
                   padx=THEME["pad"], pady=THEME["pad"])
        
        self._build_sidebar(panes)
        tk.Frame(panes, bg=THEME["border"], width=1).pack(
            side="left", fill="y", padx=THEME["pad"]
        )
        self._build_table(panes)

    def refresh_theme(self):
        """Refresh admin panel UI using the active theme."""
        self.configure(bg=THEME["bg_dark"])
        for child in self.winfo_children():
            child.destroy()
        self._build()
        self._refresh_table()
    
    def _build_header(self):
        bar = tk.Frame(self, bg=THEME["bg_card"], pady=0)
        bar.pack(fill="x")
        # Logo + Title
        self._logo_image = None
        logo_lbl = tk.Label(bar, bg=THEME["bg_card"])
        logo_lbl.pack(side="left", padx=(THEME["pad"], 8))

        header_text = f"  ⚙  {self._app_name_var.get()} Admin Panel"
        self._header_title_var = tk.StringVar(value=header_text)
        if self._app_name_var is not None:
            try:
                self._app_name_var.trace_add("write", lambda *a: self._header_title_var.set(f"  ⚙  {self._app_name_var.get()} Admin Panel"))
            except Exception:
                pass
        tk.Label(
            bar, textvariable=self._header_title_var,
            font=("Segoe UI", 15, "bold"),
            fg=THEME["text"], bg=THEME["bg_card"],
            pady=14,
        ).pack(side="left", padx=0)

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
        
        # Admin info and buttons
        right_frame = tk.Frame(bar, bg=THEME["bg_card"])
        right_frame.pack(side="right", padx=THEME["pad"])
        
        # Show logged in user
        tk.Label(
            right_frame,
            text=f"👤 {self.username}",
            font=THEME["font_small"],
            fg=THEME["text_dim"],
            bg=THEME["bg_card"]
        ).pack(side="left", padx=(0, 10))
        
        # Change password button
        StyledButton(
            right_frame,
            "🔑 Change Password",
            preset="warning",
            command=self._change_password
        ).pack(side="left", padx=(0, 5))
        
        # Logout button
        StyledButton(
            right_frame,
            "🚪 Logout",
            preset="danger",
            command=self._logout
        ).pack(side="left")
        
        StyledButton(bar, "✕  Close", preset="muted",
                     command=self.destroy).pack(side="right", padx=THEME["pad"])
        Divider(self).pack(fill="x")
    
    def _build_sidebar(self, parent):
        # Create a scrollable left column container
        side_container = tk.Frame(parent, bg=THEME["bg_dark"], width=220)
        side_container.pack(side="left", fill="y")
        side_container.pack_propagate(False)

        canvas = tk.Canvas(side_container, bg=THEME["bg_dark"], highlightthickness=0)
        vscroll = ttk.Scrollbar(side_container, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vscroll.set)
        vscroll.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        side = tk.Frame(canvas, bg=THEME["bg_dark"], width=220)
        win = canvas.create_window((0, 0), window=side, anchor="nw")
        def _on_resize(e):
            try:
                canvas.itemconfig(win, width=e.width)
            except Exception:
                pass
        canvas.bind("<Configure>", _on_resize)
        side.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        
        SectionHeader(side, "NOW SERVING").pack(anchor="w", pady=(0, 10))
        
        card = tk.Frame(side, bg=THEME["bg_card"], padx=12, pady=12)
        card.pack(fill="x")
        
        tk.Label(card, textvariable=self._current_number_var,
                 font=("Courier New", 28, "bold"),
                 fg=THEME["accent"], bg=THEME["bg_card"]).pack()
        tk.Label(card, textvariable=self._current_svc_var,
                 font=THEME["font_small"], fg=THEME["text_dim"],
                 bg=THEME["bg_card"], wraplength=180).pack(pady=(4, 0))
        
        tk.Frame(side, bg=THEME["bg_dark"], height=16).pack()
        
        if self.counter_service:
            active_counters = self.counter_service.get_all_counters(active_only=True)
            self._counter_ids_by_label = {
                self._counter_label(counter): counter.counter_id
                for counter in active_counters
            }
            counter_labels = list(self._counter_ids_by_label)
            if counter_labels:
                self._counter_var.set(counter_labels[0])
                tk.Label(
                    side,
                    text="Counter",
                    font=THEME["font_label"],
                    fg=THEME["text_dim"],
                    bg=THEME["bg_dark"],
                ).pack(anchor="w", pady=(0, 3))
                self._counter_select_widget = ttk.Combobox(
                    side,
                    textvariable=self._counter_var,
                    values=counter_labels,
                    state="readonly",
                    width=24,
                )
                self._counter_select_widget.pack(fill="x", pady=(0, 8))
            else:
                self._counter_ids_by_label = {}
                tk.Label(
                    side,
                    text="No active counters configured",
                    font=THEME["font_small"],
                    fg=THEME["warning"],
                    bg=THEME["bg_dark"],
                    wraplength=190,
                ).pack(anchor="w", pady=(0, 8))

        if self.counter_service:
            StyledButton(side, "+ Add Counter", preset="primary",
                         command=self._open_counter_config).pack(fill="x", pady=8)

        SectionHeader(side, "SETTINGS").pack(anchor="w", pady=(16, 8))
        tk.Label(
            side,
            text="Daily Ticket Limit",
            font=THEME["font_label"],
            fg=THEME["text_dim"],
            bg=THEME["bg_dark"],
        ).pack(anchor="w", pady=(0, 4))
        tk.Entry(
            side,
            textvariable=self._daily_limit_var,
            bg=THEME["bg_input"],
            fg=THEME["text"],
            relief="flat",
            highlightthickness=1,
            highlightcolor=THEME["accent"],
            highlightbackground=THEME["border"],
        ).pack(fill="x", pady=(0, 8))
        StyledButton(
            side,
            "Save Limit",
            preset="muted",
            command=self._save_daily_limit,
        ).pack(fill="x")
        
        SectionHeader(side, "APPLICATION").pack(anchor="w", pady=(16, 8))
        tk.Label(
            side,
            text="App Name",
            font=THEME["font_label"],
            fg=THEME["text_dim"],
            bg=THEME["bg_dark"],
        ).pack(anchor="w", pady=(0, 4))
        tk.Entry(
            side,
            textvariable=self._app_name_var,
            bg=THEME["bg_input"],
            fg=THEME["text"],
            relief="flat",
            highlightthickness=1,
            highlightcolor=THEME["accent"],
            highlightbackground=THEME["border"],
        ).pack(fill="x", pady=(0, 8))
        StyledButton(
            side,
            "Save App Name",
            preset="primary",
            command=self._save_app_name,
        ).pack(fill="x", pady=(0, 8))

        # Logo selector
        tk.Label(
            side,
            text="Logo",
            font=THEME["font_label"],
            fg=THEME["text_dim"],
            bg=THEME["bg_dark"],
        ).pack(anchor="w", pady=(8, 4))
        tk.Entry(
            side,
            textvariable=self._app_logo_var,
            bg=THEME["bg_input"],
            fg=THEME["text"],
            relief="flat",
            highlightthickness=1,
            highlightcolor=THEME["accent"],
            highlightbackground=THEME["border"],
        ).pack(fill="x", pady=(0, 6))
        StyledButton(side, "Choose Logo", preset="muted", command=self._choose_logo).pack(fill="x", pady=(0, 6))
        StyledButton(side, "Save Logo", preset="primary", command=self._save_app_logo).pack(fill="x", pady=(0, 8))

        tk.Label(
            side,
            text="Theme Mode",
            font=THEME["font_label"],
            fg=THEME["text_dim"],
            bg=THEME["bg_dark"],
        ).pack(anchor="w", pady=(0, 4))
        theme_modes = ["light", "dark"]
        self._theme_select_widget = ttk.Combobox(
            side,
            textvariable=self._theme_mode_var,
            values=theme_modes,
            state="readonly",
            width=24,
        )
        self._theme_select_widget.pack(fill="x", pady=(0, 8))
        StyledButton(
            side,
            "Apply Theme",
            preset="success",
            command=self._save_theme_mode,
        ).pack(fill="x")
        
        # Stats
        tk.Frame(side, bg=THEME["bg_dark"], height=16).pack()
        Divider(side).pack(fill="x")
        self._stats_frame = tk.Frame(side, bg=THEME["bg_dark"])
        self._stats_frame.pack(fill="x", pady=8)
        self._render_stats()
    
    def _render_stats(self):
        for w in self._stats_frame.winfo_children():
            w.destroy()
        statuses = ["waiting", "called", "completed", "skipped"]
        for s in statuses:
            count  = sum(1 for t in self._tickets if t["status"] == s)
            colour = THEME["status"].get(s, THEME["muted"])
            tk.Label(
                self._stats_frame,
                text=f"● {s.capitalize()}  {count}",
                font=THEME["font_small"],
                fg=colour, bg=THEME["bg_dark"],
            ).pack(anchor="w", pady=1)
    
    def _build_table(self, parent):
        right = tk.Frame(parent, bg=THEME["bg_dark"])
        right.pack(side="left", fill="both", expand=True)
        
        SectionHeader(right, "TICKET QUEUE").pack(anchor="w", pady=(0, 10))
        
        # Treeview
        style = ttk.Style()
        style.theme_use("default")
        style.configure(
            "Queue.Treeview",
            background=THEME["bg_card"],
            foreground=THEME["text"],
            rowheight=40,
            fieldbackground=THEME["bg_card"],
            borderwidth=0,
            font=THEME["font_body"],
        )
        style.configure(
            "Queue.Treeview.Heading",
            background=THEME["bg_input"],
            foreground=THEME["text_dim"],
            relief="flat",
            font=THEME["font_label"],
        )
        style.map("Queue.Treeview",
                  background=[("selected", THEME["accent"])],
                  foreground=[("selected", THEME["text"])])
        
        cols = ("priority", "number", "service", "status", "time")
        self._tree = ttk.Treeview(
            right, columns=cols, show="headings",
            style="Queue.Treeview", selectmode="browse",
        )
        
        column_configs = [
            ("priority", "🎯 Priority", 100),
            ("number",   "#",           100),
            ("service",  "Service",     200),
            ("status",   "Status",      100),
            ("time",     "Time",        80),
        ]
        
        for col, heading, width in column_configs:
            self._tree.heading(col, text=heading)
            self._tree.column(col, width=width, anchor="center")
        
        # Right-side action column (vertical buttons)
        action_col = tk.Frame(right, bg=THEME["bg_dark"], width=160)
        action_col.pack(side="right", fill="y", padx=(THEME["pad"], 0))
        action_col.pack_propagate(False)

        scroll = ttk.Scrollbar(right, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self._tree.pack(side="left", fill="both", expand=True)

        # Vertical stacked buttons for ticket actions
        StyledButton(action_col, "Call Selected", preset="primary",
                 command=self._call_selected).pack(fill="x", pady=(12, 6), padx=8)
        StyledButton(action_col, "Skip Selected", preset="danger",
                 command=self._skip_selected).pack(fill="x", pady=6, padx=8)
        StyledButton(action_col, "Complete Selected", preset="success",
                 command=self._complete_selected).pack(fill="x", pady=6, padx=8)
    
    # ── Authentication methods ─────────────────────────────────────────────────
    def _change_password(self):
        """Open password change dialog"""
        PasswordChangeDialog(self, self.auth, self.username)
    
    def _logout(self):
        """Logout and close admin panel"""
        if messagebox.askyesno("Logout", "Are you sure you want to logout?", parent=self):
            self.destroy()
    
    # ── Priority helper ────────────────────────────────────────────────────────
    def _get_priority_value(self, ticket):
        """Return priority value for sorting (lower number = higher priority)"""
        priority_map = {
            "PWD": 0,
            "Senior Citizen": 1,
            "Pregnant": 2,
            "Regular": 3
        }
        return priority_map.get(ticket.get("priority", "Regular"), 4)

    def _counter_label(self, counter) -> str:
        """Return display text for a counter dropdown option."""
        label = counter.counter_name
        if counter.department:
            label = f"{label} ({counter.department})"
        return label

    def _selected_counter_id(self) -> str | None:
        """Return selected counter ID, if counter support is enabled."""
        if not self.counter_service:
            return None
        return getattr(self, "_counter_ids_by_label", {}).get(self._counter_var.get())

    def _notify_counters_changed(self, updated_counters=None) -> None:
        """Notify the parent window that counter state has changed."""
        if self.counter_service and callable(self._counters_callback):
            self._counters_callback(updated_counters or self.counter_service.get_all_counters())

    def _refresh_counter_selection(self) -> None:
        """Refresh the counter dropdown options after configuration changes."""
        if not self.counter_service or self._counter_select_widget is None:
            return

        active_counters = self.counter_service.get_all_counters(active_only=True)
        self._counter_ids_by_label = {
            self._counter_label(counter): counter.counter_id
            for counter in active_counters
        }
        counter_labels = list(self._counter_ids_by_label)
        self._counter_select_widget['values'] = counter_labels

        if counter_labels:
            self._counter_var.set(counter_labels[0])
        else:
            self._counter_var.set("")

    def _open_counter_config(self) -> None:
        """Open the counter configuration dialog."""
        dialog = CounterConfigDialog(
            self,
            self.counter_service,
            on_counters_changed=self._notify_counters_changed,
        )
        self.wait_window(dialog)
        self._refresh_counter_selection()

    def _save_daily_limit(self) -> None:
        """Save the daily ticket limit from admin settings."""
        value = self._daily_limit_var.get().strip()
        if not value.isdigit():
            messagebox.showwarning("Invalid Limit", "Please enter a valid number.", parent=self)
            return

        limit = int(value)
        if limit < 1:
            messagebox.showwarning("Invalid Limit", "Daily ticket limit must be at least 1.", parent=self)
            return

        self._daily_ticket_limit = limit
        if callable(self._limit_callback):
            self._limit_callback(limit)

        messagebox.showinfo("Saved", f"Daily ticket limit set to {limit}.", parent=self)

    def _choose_logo(self) -> None:
        """Open file dialog to choose a logo image file."""
        path = filedialog.askopenfilename(
            parent=self,
            title="Choose Logo Image",
            filetypes=[
                ("PNG Images", "*.png"),
                ("GIF Images", "*.gif"),
                ("All Images", "*.png;*.gif;*.ico;*.ppm;*.pgm"),
            ],
        )
        if path:
            try:
                self._app_logo_var.set(path)
            except Exception:
                pass

    def _save_app_logo(self) -> None:
        """Save the chosen app logo path via callback."""
        path = (self._app_logo_var.get() or "").strip()
        if not path:
            # Allow clearing logo
            if callable(self._app_logo_change_callback):
                self._app_logo_change_callback("")
            messagebox.showinfo("Saved", "Application logo cleared.", parent=self)
            return

        # Basic validation: try to load
        try:
            if PIL_AVAILABLE:
                try:
                    im = Image.open(path)
                    im.verify()
                except Exception:
                    # Fallback to tk.PhotoImage
                    tk.PhotoImage(file=path)
            else:
                tk.PhotoImage(file=path)
        except Exception:
            messagebox.showwarning("Invalid Image", "Could not load the selected image file.", parent=self)
            return

        if callable(self._app_logo_change_callback):
            self._app_logo_change_callback(path)
        messagebox.showinfo("Saved", "Application logo updated.", parent=self)

    def _save_app_name(self):
        name = self._app_name_var.get().strip()
        if not name:
            messagebox.showwarning("Invalid App Name", "Please enter an application name.", parent=self)
            return
        if callable(self._app_name_change_callback):
            self._app_name_change_callback(name)
        messagebox.showinfo("Saved", f"Application name updated to {name}.", parent=self)

    def _save_theme_mode(self):
        mode = self._theme_mode_var.get().strip().lower()
        if mode not in ("light", "dark"):
            messagebox.showwarning("Invalid Theme", "Please select Light or Dark mode.", parent=self)
            return
        if callable(self._theme_mode_change_callback):
            self._theme_mode_change_callback(mode)
        messagebox.showinfo("Saved", f"Theme mode set to {mode}.", parent=self)

    def _assign_to_selected_counter(self, ticket: dict) -> None:
        """Assign a called ticket to the selected counter."""
        counter_id = self._selected_counter_id()
        if not counter_id:
            return
        self.counter_service.assign_ticket_to_counter(counter_id, ticket["number"])
        self._notify_counters_changed()

    def _clear_counter_for_ticket(self, ticket: dict, increment_served: bool = False) -> None:
        """Clear a ticket from whichever counter is serving it."""
        if not self.counter_service:
            return

        for counter in self.counter_service.get_all_counters():
            if counter.current_ticket_id == ticket["number"]:
                if increment_served:
                    self.counter_service.increment_counter_tickets(counter.counter_id)
                self.counter_service.clear_ticket_from_counter(counter.counter_id)

        self._notify_counters_changed()
    
    # ── Table refresh ─────────────────────────────────────────────────────────
    def _refresh_table(self):
        self._tree.delete(*self._tree.get_children())
        
        # Sort by priority first, then by status order, then by time
        def sort_key(ticket):
            priority_value = self._get_priority_value(ticket)
            status_order = {"called": 0, "waiting": 1, "skipped": 2, "completed": 3}
            status_value = status_order.get(ticket["status"], 9)
            time_str = ticket.get("time", "00:00")
            return (priority_value, status_value, time_str)
        
        sorted_tickets = sorted(self._tickets, key=sort_key)
        
        priority_icons = {
            "PWD": "⭐ PWD",
            "Senior Citizen": "👴 Senior",
            "Pregnant": "🤰 Pregnant",
            "Regular": "👤 Regular"
        }
        
        for t in sorted_tickets:
            priority_display = priority_icons.get(t.get("priority", "Regular"), "👤 Regular")
            
            self._tree.insert(
                "", "end",
                iid=t["number"],
                values=(
                    priority_display,
                    t["number"],
                    t["service"],
                    t["status"].upper(),
                    t.get("time", "")
                ),
            )
        
        # Update serving card for the selected counter
        active = self._selected_counter_ticket() or next((t for t in self._tickets if t["status"] == "called"), None)
        if active:
            priority_icon = {
                "PWD": "⭐",
                "Senior Citizen": "👴",
                "Pregnant": "🤰",
                "Regular": "👤"
            }.get(active.get("priority", "Regular"), "👤")
            self._current_number_var.set(f"{priority_icon} {active['number']}")
            self._current_svc_var.set(active["service"])
        else:
            self._current_number_var.set("—")
            self._current_svc_var.set("No active ticket")
        
        self._render_stats()

    def update_tickets(self, tickets: list):
        """Update the admin panel ticket list and refresh the view."""
        self._tickets = copy.deepcopy(tickets or [])
        self._refresh_table()

    def _notify_ticket_change(self):
        """Notify the application about ticket state changes made in the admin panel."""
        if callable(self._callback):
            self._callback(copy.deepcopy(self._tickets))

    def update_counters(self, counters: list):
        """Refresh the admin panel view after counters change."""
        # CounterService is shared, so just refresh the display.
        self._refresh_table()

    def update_daily_limit(self, daily_limit: int):
        """Update the daily ticket limit display in the admin panel."""
        self._daily_ticket_limit = daily_limit
        self._daily_limit_var.set(str(daily_limit))
        self._refresh_table()
    
    # ── Ticket mutation helpers ────────────────────────────────────────────────
    def _find(self, status, counter_id: str = None) -> dict | None:
        if self.counter_service:
            if not counter_id:
                counter_id = self._selected_counter_id()
            if counter_id:
                counter = self.counter_service.get_counter(counter_id)
                if counter and counter.current_ticket_id:
                    ticket = next((t for t in self._tickets if t["number"] == counter.current_ticket_id), None)
                    if ticket and ticket["status"] == status:
                        return ticket
        return next((t for t in self._tickets if t["status"] == status), None)

    def _selected_counter_ticket(self) -> dict | None:
        counter_id = self._selected_counter_id()
        if not counter_id or not self.counter_service:
            return None
        counter = self.counter_service.get_counter(counter_id)
        if not counter or not counter.current_ticket_id:
            return None
        return next((t for t in self._tickets if t["number"] == counter.current_ticket_id), None)

    def _set_status(self, ticket: dict, new_status: str):
        ticket["status"]  = new_status
        ticket["time"]    = datetime.now().strftime("%H:%M")

    def _clear_current_counter(self):
        """Clear the currently selected counter's active ticket only."""
        ticket = self._selected_counter_ticket()
        if ticket:
            self._clear_counter_for_ticket(ticket)
            if ticket["status"] == "called":
                self._set_status(ticket, "waiting")
    
    # ── Sidebar button actions ────────────────────────────────────────────────
    def _call_next(self):
        """Call the next ticket based on priority"""
        waiting_tickets = [t for t in self._tickets if t["status"] == "waiting"]
        
        if not waiting_tickets:
            messagebox.showinfo("Queue Empty", "No waiting tickets.", parent=self)
            return
        
        # Sort waiting tickets by priority
        waiting_tickets.sort(key=lambda t: self._get_priority_value(t))
        nxt = waiting_tickets[0]
        
        self._clear_current_counter()
        self._set_status(nxt, "called")
        self._assign_to_selected_counter(nxt)
        self._refresh_table()
        self._notify_ticket_change()
    
    def _recall(self):
        skipped = self._find("skipped")
        if not skipped:
            messagebox.showinfo("None Skipped", "No skipped tickets to recall.", parent=self)
            return
        self._clear_current_counter()
        self._set_status(skipped, "called")
        self._assign_to_selected_counter(skipped)
        self._refresh_table()
        self._notify_ticket_change()
    
    def _skip_current(self):
        active = self._selected_counter_ticket()
        if not active:
            messagebox.showinfo("No Active Ticket", "No ticket is currently being served on this counter.", parent=self)
            return
        self._clear_counter_for_ticket(active)
        self._set_status(active, "skipped")
        self._call_next()
    
    def _complete_current(self):
        active = self._selected_counter_ticket()
        if not active:
            messagebox.showinfo("No Active Ticket", "No ticket is currently being served on this counter.", parent=self)
            return
        self._clear_counter_for_ticket(active, increment_served=True)
        self._set_status(active, "completed")
        self._refresh_table()
        self._notify_ticket_change()
    
    # ── Table row button actions ───────────────────────────────────────────────
    def _selected_ticket(self) -> dict | None:
        sel = self._tree.selection()
        if not sel:
            messagebox.showwarning("No Selection", "Please select a ticket first.", parent=self)
            return None
        number = sel[0]
        return next((t for t in self._tickets if t["number"] == number), None)
    
    def _call_selected(self):
        t = self._selected_ticket()
        if not t:
            return
        if t["status"] == "called":
            messagebox.showinfo("Already Called", f"{t['number']} is already active.", parent=self)
            return
        self._clear_current_counter()
        self._set_status(t, "called")
        self._assign_to_selected_counter(t)
        self._refresh_table()
        self._notify_ticket_change()
    
    def _skip_selected(self):
        t = self._selected_ticket()
        if not t:
            return
        self._clear_counter_for_ticket(t)
        self._set_status(t, "skipped")
        self._refresh_table()
        self._notify_ticket_change()
    
    def _complete_selected(self):
        t = self._selected_ticket()
        if not t:
            return
        self._clear_counter_for_ticket(t, increment_served=t["status"] == "called")
        self._set_status(t, "completed")
        self._refresh_table()
        self._notify_ticket_change()


# ── Standalone preview ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    DEMO = [
        {"number": "P-001", "service": "Billing", "priority": "PWD", "status": "called", "time": "09:01"},
        {"number": "S-001", "service": "Account Help", "priority": "Senior Citizen", "status": "waiting", "time": "09:05"},
        {"number": "M-001", "service": "Loan Inquiry", "priority": "Pregnant", "status": "waiting", "time": "09:08"},
        {"number": "R-001", "service": "General", "priority": "Regular", "status": "waiting", "time": "09:12"},
    ]
    root = tk.Tk()
    root.withdraw()
    root.configure(bg=THEME["bg_dark"])
    
    def on_change(t):
        print("Changed:", [x["status"] for x in t])
    
    AdminPanel(root, tickets=DEMO, on_change=on_change)
    root.mainloop()
