"""Counter model for multi-counter queue management."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from uuid import uuid4


@dataclass
class Counter:
    """Represents a physical service counter/window.
    
    Attributes:
        counter_id: Unique identifier for the counter
        counter_name: Display name (e.g., "Cashier 1", "Counter 2")
        department: Associated department (e.g., "Cashier", "Enrollment")
        status: active | inactive | offline
        current_ticket_id: ID of ticket currently being served
        tickets_served_today: Count of completed tickets today
        operator_name: Name of staff member operating this counter
        is_active: Whether counter is currently available
        created_at: When counter was registered
        last_activity: Last time activity occurred
    """
    
    counter_id: str = field(default_factory=lambda: str(uuid4()))
    counter_name: str = "Counter"
    department: str = ""
    status: str = "active"  # active | inactive | offline
    current_ticket_id: Optional[str] = None
    tickets_served_today: int = 0
    operator_name: str = ""
    is_active: bool = True
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_activity: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "counter_id": self.counter_id,
            "counter_name": self.counter_name,
            "department": self.department,
            "status": self.status,
            "current_ticket_id": self.current_ticket_id,
            "tickets_served_today": self.tickets_served_today,
            "operator_name": self.operator_name,
            "is_active": self.is_active,
            "created_at": self.created_at,
            "last_activity": self.last_activity,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Counter":
        """Create Counter from dictionary."""
        return cls(
            counter_id=data.get("counter_id", str(uuid4())),
            counter_name=data.get("counter_name", "Counter"),
            department=data.get("department", ""),
            status=data.get("status", "active"),
            current_ticket_id=data.get("current_ticket_id"),
            tickets_served_today=data.get("tickets_served_today", 0),
            operator_name=data.get("operator_name", ""),
            is_active=data.get("is_active", True),
            created_at=data.get("created_at", datetime.now().isoformat()),
            last_activity=data.get("last_activity", datetime.now().isoformat()),
        )
    
    def __str__(self) -> str:
        return f"{self.counter_name} ({self.department})" if self.department else self.counter_name
