# Colors, fonts, file paths configuration
import os

# Color scheme
COLORS = {
    'primary': '#2C3E50',
    'secondary': '#3498DB',
    'success': '#27AE60',
    'warning': '#F39C12',
    'danger': '#E74C3C',
    'info': '#16A085',
    'light': '#ECF0F1',
    'dark': '#2C3E50',
    'text': '#2C3E50',
    'border': '#BDC3C7',
}

# Font configuration
FONTS = {
    'header': ('Segoe UI', 24, 'bold'),
    'title': ('Segoe UI', 18, 'bold'),
    'subtitle': ('Segoe UI', 14, 'bold'),
    'normal': ('Segoe UI', 11),
    'small': ('Segoe UI', 9),
    'ticket_large': ('Arial', 48, 'bold'),
    'ticket_medium': ('Arial', 24, 'bold'),
    'ticket_small': ('Arial', 12),
}

# File paths
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATABASE_PATH = os.path.join(PROJECT_ROOT, 'data', 'queue_data.json')
ASSETS_PATH = os.path.join(PROJECT_ROOT, 'assets')
LOG_PATH = os.path.join(PROJECT_ROOT, 'logs')

# Create directories if they don't exist
os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
os.makedirs(LOG_PATH, exist_ok=True)

# Queue configuration
MAX_QUEUE_SIZE = 200
DAILY_TICKET_LIMIT = MAX_QUEUE_SIZE
TICKET_EXPIRY_MINUTES = 120  # 2 hours before ticket expires
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 700

# Admin credentials - use environment variables in production
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', '')

# Departments/Counters
DEPARTMENTS = ['Counter 1', 'Counter 2', 'Counter 3', 'General Service']
