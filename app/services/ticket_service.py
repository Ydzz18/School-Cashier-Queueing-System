"""
app/services/ticket_service.py
─────────────────────────────
Service layer for ticket management in the queue system.
Handles ticket creation, retrieval, status updates, and business logic.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class TicketService:
    """Service for managing ticket operations."""

    # Class-level storage (in production, this would use a database)
    _tickets: Dict[int, Dict[str, Any]] = {}
    _ticket_counter: int = 0
    _priority_counters: Dict[str, int] = {
        "PWD": 0,
        "Senior Citizen": 0,
        "Pregnant": 0,
        "Regular": 0,
    }

    # Priority order for queue display
    PRIORITY_ORDER = {
        "PWD": 0,
        "Senior Citizen": 1,
        "Pregnant": 2,
        "Regular": 3,
    }

    @classmethod
    def create_ticket(
        cls,
        service_type: str,
        priority: str = "Regular",
        customer_name: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a new ticket for a customer.

        Args:
            service_type: Type of service (e.g., "Enrollment Payment")
            priority: Priority category (PWD, Senior Citizen, Pregnant, Regular)
            customer_name: Optional customer name
            notes: Optional additional notes

        Returns:
            Dict containing ticket information including ticket_number, timestamp, etc.

        Raises:
            ValueError: If priority is invalid
        """
        if priority not in cls.PRIORITY_ORDER:
            raise ValueError(f"Invalid priority: {priority}")

        # Generate ticket number based on priority
        priority_code = cls._get_priority_code(priority)
        cls._priority_counters[priority] += 1
        ticket_number = f"{priority_code}{str(cls._priority_counters[priority]).zfill(4)}"

        cls._ticket_counter += 1
        ticket_id = cls._ticket_counter

        ticket = {
            "id": ticket_id,
            "ticket_number": ticket_number,
            "service_type": service_type,
            "priority": priority,
            "customer_name": customer_name or "Customer",
            "status": "waiting",  # waiting, called, completed, cancelled
            "created_at": datetime.now().isoformat(),
            "called_at": None,
            "completed_at": None,
            "counter": None,
            "notes": notes,
        }

        cls._tickets[ticket_id] = ticket
        logger.info(f"Ticket created: {ticket_number} (ID: {ticket_id})")
        return ticket

    @classmethod
    def get_ticket(cls, ticket_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve a ticket by ID.

        Args:
            ticket_id: The ticket ID

        Returns:
            Ticket dict or None if not found
        """
        return cls._tickets.get(ticket_id)

    @classmethod
    def get_ticket_by_number(cls, ticket_number: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a ticket by ticket number.

        Args:
            ticket_number: The ticket number (e.g., "P0001")

        Returns:
            Ticket dict or None if not found
        """
        for ticket in cls._tickets.values():
            if ticket["ticket_number"] == ticket_number:
                return ticket
        return None

    @classmethod
    def get_all_tickets(cls) -> List[Dict[str, Any]]:
        """
        Get all tickets sorted by priority and creation time.

        Returns:
            List of all tickets sorted by priority order and creation time
        """
        sorted_tickets = sorted(
            cls._tickets.values(),
            key=lambda t: (cls.PRIORITY_ORDER.get(t["priority"], 99), t["created_at"]),
        )
        return sorted_tickets

    @classmethod
    def get_waiting_tickets(cls) -> List[Dict[str, Any]]:
        """
        Get all tickets with 'waiting' status, sorted by priority.

        Returns:
            List of waiting tickets
        """
        waiting = [t for t in cls._tickets.values() if t["status"] == "waiting"]
        return sorted(
            waiting,
            key=lambda t: (cls.PRIORITY_ORDER.get(t["priority"], 99), t["created_at"]),
        )

    @classmethod
    def call_ticket(
        cls, ticket_id: int, counter: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Call a ticket (transition from waiting to called status).

        Args:
            ticket_id: The ticket ID to call
            counter: Optional counter name/number where ticket is being called

        Returns:
            Updated ticket dict or None if not found
        """
        ticket = cls._tickets.get(ticket_id)
        if not ticket:
            logger.warning(f"Cannot call ticket {ticket_id}: ticket not found")
            return None

        ticket["status"] = "called"
        ticket["called_at"] = datetime.now().isoformat()
        ticket["counter"] = counter
        logger.info(f"Ticket called: {ticket['ticket_number']} at counter {counter}")
        return ticket

    @classmethod
    def complete_ticket(cls, ticket_id: int) -> Optional[Dict[str, Any]]:
        """
        Mark a ticket as completed.

        Args:
            ticket_id: The ticket ID to complete

        Returns:
            Updated ticket dict or None if not found
        """
        ticket = cls._tickets.get(ticket_id)
        if not ticket:
            logger.warning(f"Cannot complete ticket {ticket_id}: ticket not found")
            return None

        ticket["status"] = "completed"
        ticket["completed_at"] = datetime.now().isoformat()
        logger.info(f"Ticket completed: {ticket['ticket_number']}")
        return ticket

    @classmethod
    def cancel_ticket(cls, ticket_id: int, reason: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Cancel a ticket.

        Args:
            ticket_id: The ticket ID to cancel
            reason: Optional reason for cancellation

        Returns:
            Updated ticket dict or None if not found
        """
        ticket = cls._tickets.get(ticket_id)
        if not ticket:
            logger.warning(f"Cannot cancel ticket {ticket_id}: ticket not found")
            return None

        ticket["status"] = "cancelled"
        ticket["notes"] = reason or ticket.get("notes", "")
        logger.info(f"Ticket cancelled: {ticket['ticket_number']} - {reason}")
        return ticket

    @classmethod
    def update_ticket_notes(cls, ticket_id: int, notes: str) -> Optional[Dict[str, Any]]:
        """
        Update the notes for a ticket.

        Args:
            ticket_id: The ticket ID
            notes: New notes

        Returns:
            Updated ticket dict or None if not found
        """
        ticket = cls._tickets.get(ticket_id)
        if not ticket:
            return None

        ticket["notes"] = notes
        return ticket

    @classmethod
    def get_statistics(cls) -> Dict[str, Any]:
        """
        Get statistics about the current queue.

        Returns:
            Dict containing counts and statistics
        """
        tickets = cls._tickets.values()
        return {
            "total_tickets": len(tickets),
            "waiting_count": len([t for t in tickets if t["status"] == "waiting"]),
            "called_count": len([t for t in tickets if t["status"] == "called"]),
            "completed_count": len([t for t in tickets if t["status"] == "completed"]),
            "cancelled_count": len([t for t in tickets if t["status"] == "cancelled"]),
            "priority_breakdown": dict(cls._priority_counters),
        }

    @classmethod
    def get_next_ticket(cls) -> Optional[Dict[str, Any]]:
        """
        Get the next ticket to be called (highest priority, earliest creation).

        Returns:
            Next ticket dict or None if no waiting tickets
        """
        waiting_tickets = cls.get_waiting_tickets()
        return waiting_tickets[0] if waiting_tickets else None

    @classmethod
    def reset_daily(cls) -> None:
        """
        Reset ticket counters for a new day (call at midnight).
        Clears all tickets and resets counters.
        """
        cls._tickets.clear()
        cls._ticket_counter = 0
        cls._priority_counters = {
            "PWD": 0,
            "Senior Citizen": 0,
            "Pregnant": 0,
            "Regular": 0,
        }
        logger.info("Daily ticket reset completed")

    @classmethod
    def _get_priority_code(cls, priority: str) -> str:
        """
        Get the single-letter priority code for a priority level.

        Args:
            priority: Priority name

        Returns:
            Single-letter code
        """
        priority_codes = {
            "PWD": "P",
            "Senior Citizen": "S",
            "Pregnant": "M",
            "Regular": "R",
        }
        return priority_codes.get(priority, "R")

    @classmethod
    def export_tickets(cls, status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Export tickets for reporting (optionally filtered by status).

        Args:
            status_filter: Optional status to filter by

        Returns:
            List of tickets matching the filter
        """
        if status_filter:
            return [t for t in cls._tickets.values() if t["status"] == status_filter]
        return cls.get_all_tickets()
