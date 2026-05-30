# Date/time and ticket formatting utilities
from datetime import datetime, timedelta
import time

def get_current_time() -> str:
    """Get current time formatted as HH:MM:SS."""
    return datetime.now().strftime("%H:%M:%S")

def get_current_date() -> str:
    """Get current date formatted as DD/MM/YYYY."""
    return datetime.now().strftime("%d/%m/%Y")

def get_current_datetime() -> str:
    """Get current date and time."""
    return datetime.now().strftime("%d/%m/%Y %H:%M:%S")

def format_time_for_display(dt: datetime) -> str:
    """Format datetime for display."""
    return dt.strftime("%H:%M:%S")

def format_date_for_display(dt: datetime) -> str:
    """Format date for display."""
    return dt.strftime("%d/%m/%Y")

def get_elapsed_time(start_time: datetime) -> str:
    """Get elapsed time between start and current time."""
    elapsed = datetime.now() - start_time
    minutes, seconds = divmod(int(elapsed.total_seconds()), 60)
    return f"{minutes:02d}:{seconds:02d}"

def format_ticket_number(prefix: str, number: int) -> str:
    """Format ticket number with prefix."""
    return f"{prefix}-{number:04d}"

def parse_ticket_number(ticket_str: str) -> tuple[str, int]:
    """Parse ticket number to extract prefix and number."""
    parts = ticket_str.split('-')
    if len(parts) == 2:
        return parts[0], int(parts[1])
    return '', 0

def is_ticket_expired(issued_time: datetime, expiry_minutes: int = 120) -> bool:
    """Check if ticket has expired."""
    expiry_time = issued_time + timedelta(minutes=expiry_minutes)
    return datetime.now() > expiry_time

def get_time_until_expiry(issued_time: datetime, expiry_minutes: int = 120) -> str:
    """Get remaining time until ticket expires."""
    expiry_time = issued_time + timedelta(minutes=expiry_minutes)
    remaining = expiry_time - datetime.now()
    
    if remaining.total_seconds() <= 0:
        return "EXPIRED"
    
    minutes, seconds = divmod(int(remaining.total_seconds()), 60)
    return f"{minutes:02d}:{seconds:02d}"

def get_priority_label(priority: int) -> str:
    """Get human-readable priority label."""
    priority_map = {
        1: "High Priority",
        2: "Senior Citizen",
        3: "PWD",
        4: "Pregnant",
        5: "Normal"
    }
    return priority_map.get(priority, "Normal")

def estimate_wait_time(queue_position: int, avg_service_time: int = 5) -> str:
    """Estimate wait time based on position in queue."""
    minutes = queue_position * avg_service_time
    hours = minutes // 60
    minutes = minutes % 60
    
    if hours > 0:
        return f"{hours}h {minutes}m"
    return f"{minutes}m"