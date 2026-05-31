import sys
import os
import tkinter as tk
from datetime import date
from tkinter import messagebox

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.ui.dashboard import Dashboard
from app.ui.components import THEME
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

def reset_daily_ticket_state_if_needed():
    """Reset in-memory tickets and sequence counters when a new day starts."""
    global tickets_data, ticket_counter_date
    today = date.today().isoformat()
    if ticket_counter_date == today:
        return

    tickets_data = []
    ticket_counter_date = today
    sync_ticket_counters()
    if dashboard:
        dashboard.refresh(tickets=tickets_data)
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
    if tickets_issued_today() >= DAILY_TICKET_LIMIT:
        messagebox.showwarning(
            "Daily Ticket Limit Reached",
            f"The daily ticket limit of {DAILY_TICKET_LIMIT} has already been reached.",
            parent=root,
        )
        return

    tickets_data.append(ticket_info)
    sync_ticket_counters()
    # Refresh the dashboard with new ticket data
    dashboard.refresh(tickets=tickets_data)
    print(f"New ticket created: {ticket_info}")

def open_queue_window():
    """Open the queue/ticket creation window."""
    reset_daily_ticket_state_if_needed()
    issued_today = tickets_issued_today()
    if issued_today >= DAILY_TICKET_LIMIT:
        messagebox.showwarning(
            "Daily Ticket Limit Reached",
            f"The daily ticket limit of {DAILY_TICKET_LIMIT} has already been reached.",
            parent=root,
        )
        return

    sync_ticket_counters()
    QueueWindow(
        root,
        on_ticket_created=on_ticket_created,
        counter=ticket_counters,
        daily_limit=DAILY_TICKET_LIMIT,
        tickets_issued_today=issued_today,
    )

def open_admin_panel():
    """Open the admin panel for staff."""
    AdminPanel(
        root,
        tickets=tickets_data,
        counter_service=counter_service,
        on_change=on_tickets_updated,
        on_counters_change=on_counters_updated,
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
    dashboard.refresh(counters=counters_data)
    print(f"Counters updated: {len(counters_data)} active")

def on_tickets_updated(updated_tickets: list):
    """Callback when admin updates tickets."""
    global tickets_data
    tickets_data = updated_tickets
    sync_ticket_counters()
    dashboard.refresh(tickets=tickets_data, counters=counter_service.get_all_counters(active_only=True))
    print("Tickets updated from admin panel")

def load_counters_from_db():
    """Load counters from database."""
    global counters_data
    counters = counter_service.get_all_counters(active_only=True)
    counters_data = counters
    return counters_data

def main():
    global root, dashboard, db_manager, counter_service
    
    print("Starting School Cashier Queue System...")
    
    # Initialize database
    db_manager = DatabaseManager()
    counter_service = CounterService(db_manager)
    
    # Load existing counters
    load_counters_from_db()
    
    root = tk.Tk()
    root.title("QueueFlow – School Cashier Queue Management System")
    root.geometry("1000x650")
    root.configure(bg=THEME["bg_dark"])
    
    dashboard = Dashboard(
        root,
        tickets=tickets_data,
        counters=counters_data,
        open_queue_cb=open_queue_window,
        open_admin_cb=open_admin_panel,
        open_counters_cb=open_counter_management
    )
    dashboard.pack(fill="both", expand=True)
    
    print(f"Loaded {len(counters_data)} counters from database")
    print("Application ready. Click buttons to manage queue and counters.")
    
    root.mainloop()

if __name__ == "__main__":
    main()
