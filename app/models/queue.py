# Queue and Ticket data structures
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional
import uuid

@dataclass
class Ticket:
    """Represents a ticket in the queue."""
    ticket_id: str
    ticket_number: str
    customer_name: str
    department: str
    issued_at: str
    called_at: Optional[str] = None
    completed_at: Optional[str] = None
    status: str = 'waiting'  # waiting, called, completed, skipped, expired
    priority: int = 5  # 1=High, 2=Senior, 3=PWD, 4=Pregnant, 5=Normal
    notes: str = ""
    
    def to_dict(self) -> dict:
        """Convert ticket to dictionary."""
        return asdict(self)
    
    @staticmethod
    def from_dict(data: dict) -> 'Ticket':
        """Create ticket from dictionary."""
        return Ticket(**data)
    
    def get_wait_time(self) -> str:
        """Get time spent waiting or total time if completed."""
        from app.utils.helpers import get_elapsed_time
        from datetime import datetime as dt
        
        issued = dt.fromisoformat(self.issued_at)
        
        if self.completed_at:
            completed = dt.fromisoformat(self.completed_at)
            return get_elapsed_time(issued, completed)
        
        return get_elapsed_time(issued)

@dataclass
class Queue:
    """Represents a queue for a specific department."""
    queue_id: str
    department: str
    created_at: str
    tickets: list = None
    is_active: bool = True
    
    def __post_init__(self):
        if self.tickets is None:
            self.tickets = []
    
    def to_dict(self) -> dict:
        """Convert queue to dictionary."""
        return {
            'queue_id': self.queue_id,
            'department': self.department,
            'created_at': self.created_at,
            'tickets': [t.to_dict() if isinstance(t, Ticket) else t for t in self.tickets],
            'is_active': self.is_active
        }
    
    @staticmethod
    def from_dict(data: dict) -> 'Queue':
        """Create queue from dictionary."""
        tickets = [Ticket.from_dict(t) if isinstance(t, dict) else t for t in data.get('tickets', [])]
        return Queue(
            queue_id=data['queue_id'],
            department=data['department'],
            created_at=data['created_at'],
            tickets=tickets,
            is_active=data.get('is_active', True)
        )
    
    def add_ticket(self, ticket: Ticket) -> None:
        """Add ticket to queue."""
        self.tickets.append(ticket)
    
    def get_next_ticket(self) -> Optional[Ticket]:
        """Get next ticket to be served."""
        for ticket in self.tickets:
            if ticket.status == 'waiting':
                return ticket
        return None
    
    def get_current_ticket(self) -> Optional[Ticket]:
        """Get currently served ticket."""
        for ticket in self.tickets:
            if ticket.status == 'called':
                return ticket
        return None
    
    def get_queue_count(self, status: str = 'waiting') -> int:
        """Get number of tickets with given status."""
        return sum(1 for t in self.tickets if t.status == status)
    
    def get_tickets_by_status(self, status: str) -> list:
        """Get all tickets with given status."""
        return [t for t in self.tickets if t.status == status]
