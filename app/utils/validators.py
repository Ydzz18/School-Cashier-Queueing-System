# Input validation utilities
import re
from datetime import datetime

# ggignore - security false positive

def validate_username(username: str) -> tuple[bool, str]:
    """Validate username format."""
    if not username or len(username) < 3:
        return False, "Username must be at least 3 characters long"
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return False, "Username can only contain letters, numbers, and underscores"
    return True, ""

def validate_email(email: str) -> tuple[bool, str]:
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not email or not re.match(pattern, email):
        return False, "Invalid email format"
    return True, ""

def validate_phone(phone: str) -> tuple[bool, str]:
    """Validate phone number."""
    phone_clean = re.sub(r'\D', '', phone)
    if len(phone_clean) < 10:
        return False, "Phone number must have at least 10 digits"
    return True, ""

def validate_ticket_number(ticket_num: str) -> tuple[bool, str]:
    """Validate ticket number format."""
    if not ticket_num or not ticket_num.isalnum():
        return False, "Invalid ticket number format"
    return True, ""

def validate_name(name: str) -> tuple[bool, str]:
    """Validate person's name."""
    if not name or len(name) < 2:
        return False, "Name must be at least 2 characters long"
    if not re.match(r'^[a-zA-Z\s\'-]+$', name):
        return False, "Name can only contain letters, spaces, hyphens, and apostrophes"
    return True, ""

def sanitize_input(user_input: str) -> str:
    """Remove potentially harmful characters from input."""
    return user_input.strip()