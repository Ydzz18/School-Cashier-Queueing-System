"""Counter management service for multi-counter queue operations."""

import logging
from datetime import datetime
from typing import List, Optional
from app.models.counter import Counter
from app.database.db_manager import DatabaseManager

logger = logging.getLogger(__name__)


class CounterService:
    """Manages counter operations including creation, updates, and assignments."""
    
    def __init__(self, db_manager: DatabaseManager):
        """Initialize with database manager.
        
        Args:
            db_manager: DatabaseManager instance for persistence
        """
        self.db = db_manager
        self._load_counters()
    
    def _load_counters(self) -> None:
        """Load counters from database."""
        if 'counters' not in self.db.data:
            self.db.data['counters'] = {}
    
    def create_counter(self, counter_name: str, department: str = "", operator_name: str = "") -> Counter:
        """Create a new counter.
        
        Args:
            counter_name: Display name for the counter
            department: Associated department
            operator_name: Staff member name (optional)
        
        Returns:
            Created Counter object
        """
        counter = Counter(
            counter_name=counter_name,
            department=department,
            operator_name=operator_name
        )
        self.db.data['counters'][counter.counter_id] = counter.to_dict()
        self.db.save_database()
        logger.info(f"Created counter: {counter.counter_name} (ID: {counter.counter_id})")
        return counter
    
    def get_counter(self, counter_id: str) -> Optional[Counter]:
        """Get a specific counter by ID.
        
        Args:
            counter_id: Counter UUID
        
        Returns:
            Counter object or None if not found
        """
        counter_data = self.db.data.get('counters', {}).get(counter_id)
        return Counter.from_dict(counter_data) if counter_data else None
    
    def get_all_counters(self, active_only: bool = False) -> List[Counter]:
        """Get all counters.
        
        Args:
            active_only: If True, return only active counters
        
        Returns:
            List of Counter objects
        """
        counters = self.db.data.get('counters', {}).values()
        result = [Counter.from_dict(c) for c in counters]
        
        if active_only:
            result = [c for c in result if c.is_active]
        
        return result
    
    def update_counter(self, counter_id: str, **updates) -> bool:
        """Update counter properties.
        
        Args:
            counter_id: Counter UUID
            **updates: Fields to update (counter_name, department, operator_name, etc.)
        
        Returns:
            True if successful, False if counter not found
        """
        if counter_id not in self.db.data.get('counters', {}):
            logger.warning(f"Counter not found: {counter_id}")
            return False
        
        counter_data = self.db.data['counters'][counter_id]
        updates["last_activity"] = datetime.now().isoformat()
        counter_data.update(updates)
        self.db.save_database()
        logger.info(f"Updated counter: {counter_id}")
        return True
    
    def assign_ticket_to_counter(self, counter_id: str, ticket_id: str) -> bool:
        """Assign a ticket to a counter for service.
        
        Args:
            counter_id: Target counter ID
            ticket_id: Ticket ID to serve
        
        Returns:
            True if successful
        """
        if counter_id not in self.db.data.get('counters', {}):
            return False
        
        counter_data = self.db.data['counters'][counter_id]
        counter_data['current_ticket_id'] = ticket_id
        counter_data['last_activity'] = datetime.now().isoformat()
        self.db.save_database()
        logger.info(f"Assigned ticket {ticket_id} to counter {counter_id}")
        return True
    
    def clear_ticket_from_counter(self, counter_id: str) -> bool:
        """Clear the current ticket from a counter.
        
        Args:
            counter_id: Target counter ID
        
        Returns:
            True if successful
        """
        if counter_id not in self.db.data.get('counters', {}):
            return False
        
        counter_data = self.db.data['counters'][counter_id]
        counter_data['current_ticket_id'] = None
        counter_data['last_activity'] = datetime.now().isoformat()
        self.db.save_database()
        logger.info(f"Cleared ticket from counter {counter_id}")
        return True
    
    def get_least_busy_counter(self) -> Optional[Counter]:
        """Get the counter that has served the least tickets today.
        
        Returns:
            Counter with lowest ticket count, or None if no active counters
        """
        active_counters = self.get_all_counters(active_only=True)
        if not active_counters:
            return None
        
        return min(active_counters, key=lambda c: c.tickets_served_today)
    
    def deactivate_counter(self, counter_id: str) -> bool:
        """Deactivate a counter.
        
        Args:
            counter_id: Counter UUID
        
        Returns:
            True if successful
        """
        return self.update_counter(counter_id, is_active=False, status="inactive")
    
    def activate_counter(self, counter_id: str) -> bool:
        """Activate a counter.
        
        Args:
            counter_id: Counter UUID
        
        Returns:
            True if successful
        """
        return self.update_counter(counter_id, is_active=True, status="active")
    
    def delete_counter(self, counter_id: str) -> bool:
        """Delete a counter.
        
        Args:
            counter_id: Counter UUID
        
        Returns:
            True if successful
        """
        if counter_id not in self.db.data.get('counters', {}):
            return False
        
        del self.db.data['counters'][counter_id]
        self.db.save_database()
        logger.info(f"Deleted counter: {counter_id}")
        return True
    
    def increment_counter_tickets(self, counter_id: str) -> bool:
        """Increment the ticket count for a counter.
        
        Args:
            counter_id: Counter UUID
        
        Returns:
            True if successful
        """
        if counter_id not in self.db.data.get('counters', {}):
            return False
        
        counter_data = self.db.data['counters'][counter_id]
        counter_data['tickets_served_today'] = counter_data.get('tickets_served_today', 0) + 1
        counter_data['last_activity'] = datetime.now().isoformat()
        self.db.save_database()
        return True
