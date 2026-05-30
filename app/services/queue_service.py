"""
app/services/queue_service.py
────────────────────────────
Service layer for queue management.
Handles queue operations, ticket flow, and queue statistics.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class QueueService:
    """Service for managing queue operations."""

    # Queue state storage
    _queue: List[int] = []  # List of ticket IDs in queue order
    _current_counter: Optional[int] = None  # Currently being served ticket ID
    _counters: Dict[str, Dict[str, Any]] = {}  # Counter information

    @classmethod
    def initialize_counters(cls, counter_names: List[str]) -> None:
        """
        Initialize service counters.

        Args:
            counter_names: List of counter names/identifiers
        """
        cls._counters = {
            name: {
                "name": name,
                "is_active": True,
                "current_ticket": None,
                "tickets_served": 0,
                "average_service_time": 0,
            }
            for name in counter_names
        }
        logger.info(f"Initialized {len(counter_names)} counters")

    @classmethod
    def add_ticket_to_queue(cls, ticket_id: int) -> bool:
        """
        Add a ticket to the queue.

        Args:
            ticket_id: ID of ticket to add

        Returns:
            True if successful, False otherwise
        """
        if ticket_id not in cls._queue:
            cls._queue.append(ticket_id)
            logger.info(f"Ticket {ticket_id} added to queue")
            return True
        logger.warning(f"Ticket {ticket_id} already in queue")
        return False

    @classmethod
    def remove_ticket_from_queue(cls, ticket_id: int) -> bool:
        """
        Remove a ticket from the queue.

        Args:
            ticket_id: ID of ticket to remove

        Returns:
            True if successful, False otherwise
        """
        if ticket_id in cls._queue:
            cls._queue.remove(ticket_id)
            logger.info(f"Ticket {ticket_id} removed from queue")
            return True
        logger.warning(f"Ticket {ticket_id} not in queue")
        return False

    @classmethod
    def get_queue(cls) -> List[int]:
        """
        Get the current queue of ticket IDs.

        Returns:
            List of ticket IDs in queue order
        """
        return cls._queue.copy()

    @classmethod
    def get_queue_length(cls) -> int:
        """
        Get the number of tickets in queue.

        Returns:
            Queue length
        """
        return len(cls._queue)

    @classmethod
    def get_queue_position(cls, ticket_id: int) -> Optional[int]:
        """
        Get the position of a ticket in the queue (1-indexed).

        Args:
            ticket_id: ID of ticket

        Returns:
            Position (1-indexed) or None if not in queue
        """
        try:
            return cls._queue.index(ticket_id) + 1
        except ValueError:
            return None

    @classmethod
    def get_next_in_queue(cls) -> Optional[int]:
        """
        Get the next ticket ID in queue without removing it.

        Returns:
            Next ticket ID or None if queue is empty
        """
        return cls._queue[0] if cls._queue else None

    @classmethod
    def call_next_ticket(cls, counter: Optional[str] = None) -> Optional[int]:
        """
        Call the next ticket in queue and assign to counter.

        Args:
            counter: Optional counter name

        Returns:
            Ticket ID of called ticket or None if queue is empty
        """
        if not cls._queue:
            logger.warning("Cannot call next ticket: queue is empty")
            return None

        ticket_id = cls._queue.pop(0)
        cls._current_counter = ticket_id

        if counter and counter in cls._counters:
            cls._counters[counter]["current_ticket"] = ticket_id

        logger.info(f"Called ticket {ticket_id} at counter {counter}")
        return ticket_id

    @classmethod
    def clear_current_counter(cls, counter: Optional[str] = None) -> None:
        """
        Clear the current ticket from a counter.

        Args:
            counter: Counter name to clear
        """
        cls._current_counter = None
        if counter and counter in cls._counters:
            cls._counters[counter]["current_ticket"] = None

    @classmethod
    def activate_counter(cls, counter: str) -> bool:
        """
        Activate a counter.

        Args:
            counter: Counter name

        Returns:
            True if successful
        """
        if counter in cls._counters:
            cls._counters[counter]["is_active"] = True
            logger.info(f"Counter {counter} activated")
            return True
        return False

    @classmethod
    def deactivate_counter(cls, counter: str) -> bool:
        """
        Deactivate a counter.

        Args:
            counter: Counter name

        Returns:
            True if successful
        """
        if counter in cls._counters:
            cls._counters[counter]["is_active"] = False
            logger.info(f"Counter {counter} deactivated")
            return True
        return False

    @classmethod
    def get_active_counters(cls) -> List[str]:
        """
        Get list of active counters.

        Returns:
            List of active counter names
        """
        return [name for name, info in cls._counters.items() if info["is_active"]]

    @classmethod
    def get_counter_info(cls, counter: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific counter.

        Args:
            counter: Counter name

        Returns:
            Counter info dict or None
        """
        return cls._counters.get(counter)

    @classmethod
    def get_all_counters(cls) -> Dict[str, Dict[str, Any]]:
        """
        Get information about all counters.

        Returns:
            Dict of all counter information
        """
        return cls._counters.copy()

    @classmethod
    def increment_counter_service_count(cls, counter: str) -> None:
        """
        Increment the number of tickets served at a counter.

        Args:
            counter: Counter name
        """
        if counter in cls._counters:
            cls._counters[counter]["tickets_served"] += 1

    @classmethod
    def reset_queue(cls) -> None:
        """
        Reset the queue (clear all tickets).
        """
        cls._queue.clear()
        cls._current_counter = None
        logger.info("Queue reset")

    @classmethod
    def get_queue_statistics(cls) -> Dict[str, Any]:
        """
        Get statistics about the current queue state.

        Returns:
            Dict containing queue statistics
        """
        active_counters = cls.get_active_counters()
        return {
            "total_in_queue": len(cls._queue),
            "currently_served": cls._current_counter,
            "active_counters": len(active_counters),
            "total_counters": len(cls._counters),
            "counter_details": {
                name: {
                    "is_active": info["is_active"],
                    "current_ticket": info["current_ticket"],
                    "tickets_served": info["tickets_served"],
                }
                for name, info in cls._counters.items()
            },
        }
