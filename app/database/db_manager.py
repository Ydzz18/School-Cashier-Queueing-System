import json
import os
from uuid import uuid4
from datetime import datetime
from typing import Optional, List, Dict, Any
from app.models.queue import Queue, Ticket
from app.models.user import User
from app.utils.constants import DATABASE_PATH

class DatabaseManager:
    """A clean JSON database manager handling users, queues, and tickets."""
    
    def __init__(self, db_path: str = DATABASE_PATH):
        self.db_path = db_path
        self.data = self._load_database()
    
    def _load_database(self) -> dict:
        """Loads the database file safely, returning a default schema upon failure."""
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass 
        return {
            'queues': {},
            'users': {},
            'sessions': {},
            'tickets_history': [],
            'settings': {}
        }
    
    def save_database(self) -> bool:
        """Commits the current memory state to the JSON file system securely."""
        try:
            directory = os.path.dirname(self.db_path)
            if directory:
                os.makedirs(directory, exist_ok=True)
            with open(self.db_path, 'w') as f:
                json.dump(self.data, f, indent=2)
            return True
        except IOError as e:
            print(f"Database write error: {e}")
            return False

    # --- QUEUE OPERATIONS ---
    
    def create_queue(self, department: str) -> Queue:
        """Generates and registers a new active queue for a specific department."""
        queue_id = str(uuid4())
        queue = Queue(
            queue_id=queue_id,
            department=department,
            created_at=datetime.now().isoformat()
        )
        self.data['queues'][queue_id] = queue.to_dict()
        self.save_database()
        return queue
    
    def get_queue(self, queue_id: str) -> Optional[Queue]:
        """Fetches a specific queue object by its unique ID."""
        queue_data = self.data['queues'].get(queue_id)
        return Queue.from_dict(queue_data) if queue_data else None
    
    def get_queue_by_department(self, department: str) -> Optional[Queue]:
        """Finds the running/active queue associated with an operational department."""
        for q in self.data['queues'].values():
            if q.get('department') == department and q.get('is_active', True):
                return Queue.from_dict(q)
        return None
    
    def get_all_queues(self) -> List[Queue]:
        """Provides a complete collection of all currently active queues."""
        return [Queue.from_dict(q) for q in self.data['queues'].values() if q.get('is_active', True)]
    
    def update_queue(self, queue: Queue) -> bool:
        """Overwrites an existing queue structure with updated structural values."""
        if queue.queue_id in self.data['queues']:
            self.data['queues'][queue.queue_id] = queue.to_dict()
            return self.save_database()
        return False
    
    def delete_queue(self, queue_id: str) -> bool:
        """Applies a soft-delete behavior by changing queue visibility flags."""
        queue = self.data['queues'].get(queue_id)
        if queue:
            queue['is_active'] = False
            return self.save_database()
        return False

    # --- TICKET OPERATIONS ---
    
    def add_ticket_to_queue(self, queue_id: str, ticket: Ticket) -> bool:
        """Pushes a new customer/user ticket directly into a queue."""
        queue = self.get_queue(queue_id)
        if queue:
            queue.add_ticket(ticket)
            self.data['queues'][queue_id] = queue.to_dict()
            return self.save_database()
        return False
    
    def get_ticket(self, ticket_id: str) -> Optional[Ticket]:
        """Traverses collections to find a ticket matching the ID target."""
        for queue in self.data['queues'].values():
            for t in queue.get('tickets', []):
                if t.get('ticket_id') == ticket_id:
                    return Ticket.from_dict(t)
        return None
    
    def update_ticket(self, queue_id: str, ticket: Ticket) -> bool:
        """Locates and changes states inside specific nested ticket rows inside a queue."""
        queue = self.get_queue(queue_id)
        if queue:
            for i, t in enumerate(queue.tickets):
                if t.ticket_id == ticket.ticket_id:
                    queue.tickets[i] = ticket
                    self.data['queues'][queue_id] = queue.to_dict()
                    return self.save_database()
        return False
    
    def save_ticket_history(self, ticket: Ticket) -> bool:
        """Appends closed, completed, or dropped queuing tickets into historical logs."""
        self.data['tickets_history'].append(ticket.to_dict())
        return self.save_database()
    
    def get_tickets_history(self, limit: int = 100) -> List[Ticke
