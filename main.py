import sys
import os
import tkinter as tk
from datetime import date
from tkinter import messagebox

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.ui.dashboard import Dashboard
from app.ui.components import THEME, StyledButton, apply_theme_mode, refresh_widget_theme
from app.ui.queues.queue_window import QueueWindow
from app.ui.queues.admin_panel import AdminPanel
from app.ui.queues.counter_config import CounterConfigDialog
from app.database.db_manager import DatabaseManager
from app.services.counter_service import CounterService
from app.utils.constants import DAILY_TICKET_LIMIT

# Global state for tickets and counters
tickets_data = []
counters_data = []
ticket_counters = {
    "current": 0,
    "pwd": 0,
    "senior_citizen": 0,
    "pregnant": 0,
    "regular": 0,
}
ticket_counter_date = date.today().isoformat()
db_manager = None
counter_service = None
dashboard = None
root = None
# Keep references to all open dashboard windows so they refresh together
dashboard_windows = []
admin_windows = []
queue_windows = []
# Work with a mutable app state from admin settings
app_name = "QueueFlow"
theme_mode = "dark"
daily_ticket_limit = DAILY_TICKET_LIMIT
# Tkinter StringVar that mirrors `app_name` for live UI updates.
# Initialized when `root` is created in `main()`.
app_name_var = None
app_logo = None
# StringVar holding logo file path for live UI updates
app_logo_var = None

def _cleanup_dashboards():
    global dashboard_windows
    dashboard_windows = [dash for dash in dashboard_windows if dash.winfo_exists()]


def _cleanup_admin_panels():
    global admin_windows
    admin_windows = [panel for panel in admin_windows if panel.winfo_exists()]


def _register_dashboard(dashboard_instance):
    global dashboard_windows
    if dashboard_instance not in dashboard_windows:
        dashboard_windows.append(dashboard_instance)


def _close_dashboard_window(window, dashboard_instance):
    if dashboard_instance in dashboard_windows:
        dashboard_windows.remove(dashboard_instance)
    window.destroy()


def _cleanup_queue_windows():
    global queue_windows
    queue_windows = [w for w in queue_windows if w.winfo_exists()]


def _register_queue_window(window):
    global queue_windows
    if window not in queue_windows:
        queue_windows.append(window)


def _set_window_titles():
    if root:
        root.title(f"{app_name} Launcher")
    for dash in dashboard_windows:
        if dash.winfo_exists() and hasattr(dash, "master"):
            try:
                dash.master.title(f"{app_name} – Ticket Window")
            except tk.TclError:
                pass
    for panel in admin_windows:
        if panel.winfo_exists():
            panel.title(f"{app_name} Admin Panel")
    _cleanup_queue_windows()
    for win in queue_windows:
        if win.winfo_exists():
            try:
                win.title(f"{app_name} – Ticket Window")
            except tk.TclError:
                pass

    # Also update any other existing Toplevels that are ticket windows
    try:
        for child in root.winfo_children():
            # If it's a Toplevel (separate window) and not the root itself
            if isinstance(child, tk.Toplevel):
                try:
                    cur = child.title() or ""
                except Exception:
                    cur = ""
                # Heuristic: update windows that reference ticket/queue in their title
                if any(k in cur for k in ("Ticket", "Queue", "Ticket Window")):
                    try:
                        child.title(f"{app_name} – Ticket Window")
                    except Exception:
                        pass
    except Exception:
        pass


def _refresh_queue_windows():
    _cleanup_queue_windows()
    for win in queue_windows:
        if not win.winfo_exists():
            continue
        try:
            win.configure(bg=THEME["bg_dark"])
        except tk.TclError:
            pass
        if hasattr(win, "refresh_theme"):
            win.refresh_theme()
        else:
            refresh_widget_theme(win)


def _refresh_dashboards(tickets=None, counters=None):
    _cleanup_dashboards()
    for dash in dashboard_windows:
        dash.refresh(tickets=tickets, counters=counters)


def _refresh_admin_panels(tickets=None, counters=None, daily_limit=None):
    _cleanup_admin_panels()
    for panel in admin_windows:
        if hasattr(panel, "refresh_theme"):
            panel.refresh_theme()
        if tickets is not None and hasattr(panel, "update_tickets"):
            panel.update_tickets(tickets)
        if counters is not None and hasattr(panel, "update_counters"):
            panel.update_counters(counters)
        if daily_limit is not None and hasattr(panel, "update_daily_limit"):
            panel.update_daily_limit(daily_limit)


def reset_daily_ticket_state_if_needed():
    """Reset in-memory tickets and sequence counters when a new day starts."""
    global tickets_data, ticket_counter_date
    today = date.today().isoformat()
    if ticket_counter_date == today:
        return

    tickets_data = []
    ticket_counter_date = today
    sync_ticket_counters()
    _refresh_dashboards(tickets=tickets_data)
    _refresh_admin_panels(tickets=tickets_data)
    print(f"New day detected ({today}); daily ticket state was reset.")

def tickets_issued_today() -> int:
    """Return the number of tickets issued for the current date."""
    today = date.today().isoformat()
    return sum(1 for ticket in tickets_data if ticket.get("date", today) == today)

def sync_ticket_counters():
    """Synchronize in-memory ticket sequence counters from existing tickets."""
    global ticket_counters
    ticket_counters = {
        "current": len(tickets_data),
        "pwd": 0,
        "senior_citizen": 0,
        "pregnant": 0,
        "regular": 0,
    }

    priority_to_key = {
        "PWD": "pwd",
        "Senior Citizen": "senior_citizen",
        "Pregnant": "pregnant",
        "Regular": "regular",
    }

    for ticket in tickets_data:
        key = priority_to_key.get(ticket.get("priority", "Regular"), "regular")
        number = ticket.get("number", "")
        try:
            sequence = int(number.split("-")[-1])
        except (ValueError, IndexError):
            sequence = 0
        ticket_counters[key] = max(ticket_counters[key], sequence)

def on_ticket_created(ticket_info: dict):
    """Callback when a new ticket is created."""
    reset_daily_ticket_state_if_needed()
    if tickets_issued_today() >= daily_ticket_limit:
        messagebox.showwarning(
            "Daily Ticket Limit Reached",
            f"The daily ticket limit of {daily_ticket_limit} has already been reached.",
            parent=root,
        )
        return

    tickets_data.append(ticket_info)
    sync_ticket_counters()
    # Refresh all open dashboard windows and admin panels with new ticket data
    _refresh_dashboards(tickets=tickets_data)
    _refresh_admin_panels(tickets=tickets_data)
    print(f"New ticket created: {ticket_info}")

def open_queue_window():
    """Open the queue/ticket creation window."""
    reset_daily_ticket_state_if_needed()
    issued_today = tickets_issued_today()
    if issued_today >= daily_ticket_limit:
        messagebox.showwarning(
            "Daily Ticket Limit Reached",
            f"The daily ticket limit of {daily_ticket_limit} has already been reached.",
            parent=root,
        )
        return

    sync_ticket_counters()
    qwin = QueueWindow(
        root,
        on_ticket_created=on_ticket_created,
        counter=ticket_counters,
        daily_limit=daily_ticket_limit,
        tickets_issued_today=issued_today,
        app_name_var=app_name_var,
        app_logo_var=app_logo_var,
    )
    if qwin is not None and qwin.winfo_exists():
        qwin.title(f"{app_name} – Ticket Window")
        _register_queue_window(qwin)

def open_admin_panel():
    """Open the admin panel for staff."""
    panel = AdminPanel(
        root,
        tickets=tickets_data,
        daily_ticket_limit=daily_ticket_limit,
        counter_service=counter_service,
        on_change=on_tickets_updated,
        on_counters_change=on_counters_updated,
        on_limit_change=on_daily_ticket_limit_changed,
        on_app_name_change=on_app_name_changed,
        on_theme_mode_change=on_theme_mode_changed,
        app_name=app_name,
        app_name_var=app_name_var,
        app_logo_var=app_logo_var,
        on_app_logo_change=on_app_logo_changed,
        theme_mode=theme_mode,
    )
    # The AdminPanel __init__ may return early (authentication failed)
    # in which case the instance is not a real Toplevel (no `.tk` attr).
    if panel is not None and getattr(panel, "tk", None) is not None:
        try:
            if panel.winfo_exists():
                admin_windows.append(panel)
        except Exception:
            # Defensive: ignore partially initialized panels
            pass


def on_daily_ticket_limit_changed(new_limit: int):
    """Update the application daily ticket limit from admin settings."""
    global daily_ticket_limit
    daily_ticket_limit = new_limit
    if db_manager:
        settings = db_manager.data.setdefault('settings', {})
        settings['daily_ticket_limit'] = daily_ticket_limit
        db_manager.save_database()
    print(f"Daily ticket limit updated to {daily_ticket_limit}")
    _refresh_admin_panels(daily_limit=daily_ticket_limit)


def on_app_name_changed(new_name: str):
    """Update and persist the application name."""
    global app_name
    if not new_name or not new_name.strip():
        return
    app_name = new_name.strip()
    if db_manager:
        settings = db_manager.data.setdefault('settings', {})
        settings['app_name'] = app_name
        db_manager.save_database()
    _set_window_titles()
    # Update any StringVar bindings so labels refresh automatically
    try:
        if app_name_var is not None:
            app_name_var.set(app_name)
    except Exception:
        pass
    # Refresh logos/titles in other windows
    _refresh_dashboards(tickets=tickets_data, counters=counters_data)
    _refresh_admin_panels(tickets=tickets_data, counters=counters_data)
    _refresh_queue_windows()
    print(f"Application name updated to {app_name}")


def on_app_logo_changed(new_path: str):
    """Update and persist the application logo path."""
    global app_logo
    if not new_path:
        # Allow clearing logo
        app_logo = ""
    else:
        app_logo = new_path
    if db_manager:
        settings = db_manager.data.setdefault('settings', {})
        settings['app_logo'] = app_logo
        db_manager.save_database()
    # Update StringVar so UI bindings refresh
    try:
        if app_logo_var is not None:
            app_logo_var.set(app_logo or "")
    except Exception:
        pass
    # Refresh windows so header logos update
    _refresh_dashboards(tickets=tickets_data, counters=counters_data)
    _refresh_admin_panels(tickets=tickets_data, counters=counters_data)
    _refresh_queue_windows()
    print(f"Application logo updated to {app_logo}")


def on_theme_mode_changed(new_mode: str):
    """Apply and persist theme mode changes."""
    global theme_mode
    theme_mode = (new_mode or "dark").lower()
    if db_manager:
        settings = db_manager.data.setdefault('settings', {})
        settings['theme_mode'] = theme_mode
        db_manager.save_database()
    apply_theme_mode(theme_mode)
    StyledButton.refresh_presets()
    if root:
        try:
            root.configure(bg=THEME["bg_dark"])
            refresh_widget_theme(root)
        except tk.TclError:
            pass
    _refresh_dashboards(tickets=tickets_data, counters=counters_data)
    _refresh_admin_panels(tickets=tickets_data, counters=counters_data)
    _refresh_queue_windows()
    _set_window_titles()
    print(f"Theme mode updated to {theme_mode}")


def open_ticket_window():
    """Open the ticket/dashboard window in a separate top-level."""
    window = tk.Toplevel(root)
    window.title(f"{app_name} – Ticket Window")
    window.geometry("1000x650")
    window.configure(bg=THEME["bg_dark"])

    dashboard_frame = Dashboard(
        window,
        tickets=tickets_data,
        counters=counters_data,
        open_queue_cb=open_queue_window,
        open_admin_cb=open_admin_panel,
        open_counters_cb=open_counter_management,
        show_navigation=False,
        app_name_var=app_name_var,
        app_logo_var=app_logo_var,
    )
    dashboard_frame.pack(fill="both", expand=True)
    _register_dashboard(dashboard_frame)
    _register_queue_window(window)
    window.protocol(
        "WM_DELETE_WINDOW",
        lambda w=window, d=dashboard_frame: _close_dashboard_window(w, d),
    )


def open_counter_management():
    """Open the counter management dialog."""
    CounterConfigDialog(root, counter_service, on_counters_changed=on_counters_updated)

def on_counters_updated(updated_counters=None):
    """Callback when counter records change."""
    global counters_data
    counters_data = (
        [counter for counter in updated_counters if counter.is_active]
        if updated_counters is not None
        else counter_service.get_all_counters(active_only=True)
    )
    _refresh_dashboards(counters=counters_data)
    _refresh_admin_panels(counters=counters_data)
    print(f"Counters updated: {len(counters_data)} active")


def on_tickets_updated(updated_tickets: list):
    """Callback when admin updates tickets."""
    global tickets_data
    tickets_data = updated_tickets
    sync_ticket_counters()
    _refresh_dashboards(tickets=tickets_data, counters=counter_service.get_all_counters(active_only=True))
    _refresh_admin_panels(tickets=tickets_data)
    print("Tickets updated from admin panel")

def load_counters_from_db():
    """Load counters from database."""
    global counters_data
    counters = counter_service.get_all_counters(active_only=True)
    counters_data = counters
    return counters_data


def load_app_settings():
    """Load application settings from database."""
    global daily_ticket_limit, app_name, theme_mode
    if not db_manager:
        return
    settings = db_manager.data.setdefault('settings', {})
    daily_ticket_limit = settings.get('daily_ticket_limit', DAILY_TICKET_LIMIT)
    app_name = settings.get('app_name', app_name)
    theme_mode = settings.get('theme_mode', theme_mode)
    # Logo path may be stored in settings
    global app_logo
    app_logo = settings.get('app_logo', app_logo)
    settings['daily_ticket_limit'] = daily_ticket_limit
    settings['app_name'] = app_name
    settings['theme_mode'] = theme_mode
    db_manager.save_database()
    apply_theme_mode(theme_mode)
    StyledButton.refresh_presets()
    # Keep StringVar in sync if it exists
    try:
        if app_name_var is not None:
            app_name_var.set(app_name)
    except Exception:
        pass
    try:
        if app_logo_var is not None:
            app_logo_var.set(app_logo or "")
    except Exception:
        pass

def main():
    global root, dashboard, db_manager, counter_service
    global app_name_var
    global app_logo_var
    
    print("Starting School Cashier Queue System...")
    
    # Initialize database
    db_manager = DatabaseManager()
    counter_service = CounterService(db_manager)
    load_app_settings()
    
    # Load existing counters
    load_counters_from_db()
    
    root = tk.Tk()
    root.title(f"{app_name} Launcher")
    # Create a StringVar for the app name so UI labels can bind to it.
    try:
        app_name_var = tk.StringVar(value=app_name)
    except Exception:
        app_name_var = None
    try:
        app_logo_var = tk.StringVar(value=app_logo or "")
    except Exception:
        app_logo_var = None
    root.geometry("480x320")
    root.configure(bg=THEME["bg_dark"])

    class Launcher(tk.Frame):
        def __init__(self, master, open_ticket_window_cb, open_new_ticket_cb, open_admin_cb, **kwargs):
            super().__init__(master, bg=THEME["bg_dark"], **kwargs)
            self.open_ticket_window_cb = open_ticket_window_cb
            self.open_new_ticket_cb = open_new_ticket_cb
            self.open_admin_cb = open_admin_cb
            self._build()

        def _build(self):
            # Title label updates when `app_name_var` changes
            if app_name_var is not None:
                self._launcher_title_var = tk.StringVar(value=f"{app_name_var.get()} Launcher")
                # keep launcher title in sync with app_name_var
                try:
                    app_name_var.trace_add("write", lambda *a: self._launcher_title_var.set(f"{app_name_var.get()} Launcher"))
                except Exception:
                    pass
                title = tk.Label(
                    self,
                    textvariable=self._launcher_title_var,
                    font=("Segoe UI", 18, "bold"),
                    fg=THEME["accent"],
                    bg=THEME["bg_dark"],
                )
            else:
                title = tk.Label(
                    self,
                    text=f"{app_name} Launcher",
                    font=("Segoe UI", 18, "bold"),
                    fg=THEME["accent"],
                    bg=THEME["bg_dark"],
                )
            title.pack(pady=(24, 8))

            subtitle = tk.Label(
                self,
                text="Select a window to open. Multiple windows can stay open together.",
                font=("Segoe UI", 10),
                fg=THEME["text_dim"],
                bg=THEME["bg_dark"],
                wraplength=420,
                justify="center",
            )
            subtitle.pack(padx=24, pady=(0, 22))

            btn_frame = tk.Frame(self, bg=THEME["bg_dark"])
            btn_frame.pack(fill="x", padx=24)

            StyledButton(
                btn_frame,
                "Open Ticket Window",
                preset="primary",
                command=self.open_ticket_window_cb,
                width=24,
            ).pack(pady=8)
            StyledButton(
                btn_frame,
                "Add New Ticket",
                preset="success",
                command=self.open_new_ticket_cb,
                width=24,
            ).pack(pady=8)
            StyledButton(
                btn_frame,
                "Open Admin Panel",
                preset="muted",
                command=self.open_admin_cb,
                width=24,
            ).pack(pady=8)

    Launcher(
        root,
        open_ticket_window_cb=open_ticket_window,
        open_new_ticket_cb=open_queue_window,
        open_admin_cb=open_admin_panel,
    ).pack(fill="both", expand=True)

    print(f"Loaded {len(counters_data)} counters from database")
    print("Application ready. Use the launcher to open ticket and admin windows.")

    root.mainloop()

if __name__ == "__main__":
    main()
