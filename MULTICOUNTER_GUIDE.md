# Multi-Counter Queue Management System

## Overview
The School Cashier Queueing System now supports **multiple service counters** with centralized management and network capability for multi-computer setups.

## Features

### 1. Counter Management
- **Add Counters**: Create multiple service counters (windows/booths)
- **Edit Counters**: Update counter names, departments, and operator assignments
- **Delete Counters**: Remove inactive or unnecessary counters
- **Counter Properties**:
  - Counter name (e.g., "Cashier 1", "Enrollment Window")
  - Department (e.g., "Billing", "Enrollment", "Records")
  - Operator name (staff member assigned)
  - Service count tracking (tickets served per day)
  - Status tracking (active/inactive/offline)

### 2. Dashboard with Multiple Counters
The main dashboard now displays:
- **Counter Cards**: Shows all active counters with:
  - Current ticket being served
  - Operator information
  - Daily service count
  - Counter status
  - Department

- **Queue Display**: Full queue view with all pending tickets
- **Quick Stats**: Waiting, completed, and skipped ticket counts

### 3. Database Persistence
- All counter configurations saved to `data/queue_data.json`
- Counters persist across application restarts
- Service counts tracked and stored

### 4. Multi-Computer Support (Ready for Implementation)
The system is architected to support:
- **Shared Database**: Multiple computers accessing the same counter configuration
- **Ticket Routing**: Smart assignment of tickets to least-busy counters
- **State Sync**: All counter and ticket state changes persisted to database

## How to Use

### Adding a Counter
1. Click the **⚙ Counters** button in the dashboard header
2. Click **+ Add Counter**
3. Enter:
   - Counter Name (e.g., "Cashier 1")
   - Department (optional, e.g., "Billing")
   - Operator Name (staff member name)
4. Click **Save**

### Managing Counters
1. Open **⚙ Counters** dialog
2. Select a counter from the list
3. Click:
   - **📝 Edit** to modify counter details
   - **🗑 Delete** to remove the counter

### Viewing Counter Status
The dashboard's left panel shows all active counters with:
- Counter name and department
- Current ticket being served (if any)
- Operator name
- Tickets served today

## Architecture

### Counter Model (`app/models/counter.py`)
```python
Counter:
  - counter_id: Unique identifier (UUID)
  - counter_name: Display name
  - department: Associated department
  - status: active | inactive | offline
  - current_ticket_id: ID of ticket currently served
  - tickets_served_today: Daily count
  - operator_name: Staff member name
  - is_active: Boolean flag
  - created_at: Creation timestamp
  - last_activity: Last update timestamp
```

### Counter Service (`app/services/counter_service.py`)
Provides methods for:
- Creating and deleting counters
- Assigning tickets to counters
- Getting least-busy counter
- Tracking service counts
- Updating operator assignments

### Counter Configuration UI (`app/ui/queues/counter_config.py`)
Graphical interface for:
- Viewing all counters
- Adding new counters
- Editing counter properties
- Deleting counters
- Real-time display of service counts

## Multi-Computer Implementation Guide

### Option 1: Shared Database (Network Share)
**Best for**: Single location with multiple staff computers

```
┌─────────────────────────────┐
│ Network Shared Directory    │
│ (data/queue_data.json)      │
└─────────────────────────────┘
         ↑         ↑         ↑
      Mount   Mount   Mount
         │         │         │
  [Computer 1][Computer 2][Computer 3]
  (Dashboard) (Counter 1) (Counter 2)
```

**Implementation**:
1. Place `data/` folder on network share (NFS/Samba/SMB)
2. Mount on all computers
3. Each app connects to same database
4. Use file locking to prevent concurrent write conflicts

### Option 2: REST API Server (Recommended for Multiple Locations)
**Best for**: Multiple schools or branches

```
┌─────────────────────────────┐
│ Central Server              │
│ (Flask/FastAPI)             │
│ + SQLite Database           │
└─────────────────────────────┘
         ↑         ↑         ↑
    REST API  REST API  REST API
         │         │         │
  [Counter 1][Counter 2][Kiosk]
```

**Implementation steps** (TODO):
1. Create Flask server with REST endpoints
2. Add HTTP client to Dashboard
3. Implement token-based authentication
4. Add WebSocket for real-time updates

### Option 3: Message Queue (Enterprise Setup)
**Best for**: Large-scale multi-location deployments

Uses Redis/RabbitMQ for:
- Pub/Sub ticket updates
- Counter state synchronization
- Event-driven architecture

## Configuration Files

### Database Structure
```json
{
  "queues": { ... },
  "users": { ... },
  "sessions": { ... },
  "tickets_history": [ ... ],
  "settings": { ... },
  "counters": {
    "uuid-1": { Counter object },
    "uuid-2": { Counter object }
  }
}
```

## API Methods (Counter Service)

```python
# Create counter
counter = counter_service.create_counter(
    counter_name="Cashier 1",
    department="Billing",
    operator_name="John Doe"
)

# Get all active counters
counters = counter_service.get_all_counters(active_only=True)

# Assign ticket to counter
counter_service.assign_ticket_to_counter(counter_id, ticket_id)

# Get least-busy counter
best_counter = counter_service.get_least_busy_counter()

# Update counter
counter_service.update_counter(
    counter_id,
    operator_name="Jane Smith"
)

# Deactivate/Activate
counter_service.deactivate_counter(counter_id)
counter_service.activate_counter(counter_id)
```

## Next Steps / TODO

1. **Network Sync**
   - [ ] Implement Flask API server for multi-computer support
   - [ ] Add WebSocket for real-time counter updates
   - [ ] Create API authentication/authorization

2. **Enhanced Features**
   - [ ] Queue priority routing to counters
   - [ ] Service time prediction per counter
   - [ ] Counter performance analytics
   - [ ] Automatic load balancing

3. **Integration**
   - [ ] Link ticket assignment to counter automation
   - [ ] SMS notifications for queue status
   - [ ] Mobile app for counter operators
   - [ ] Admin dashboard with metrics

4. **Testing**
   - [ ] Multi-counter stress testing
   - [ ] Network sync reliability testing
   - [ ] Database concurrent access testing

## System Requirements

- Python 3.8+
- Tkinter (included with Python)
- For network setup: Network share or Flask server

## File Structure
```
app/
├── models/
│   ├── counter.py (new)
│   ├── queue.py
│   └── user.py
├── services/
│   ├── counter_service.py (new)
│   ├── queue_service.py
│   ├── ticket_service.py
│   └── auth_service.py
├── ui/
│   ├── dashboard.py (updated)
│   ├── components/
│   │   ├── theme.py
│   │   └── widgets.py
│   └── queues/
│       ├── counter_config.py (new)
│       ├── queue_window.py
│       └── admin_panel.py
└── database/
    └── db_manager.py

main.py (updated)
```

## Testing

Run the test suite:
```bash
python -c "
import sys; sys.path.insert(0, '.')
from app.services.counter_service import CounterService
from app.database.db_manager import DatabaseManager

db = DatabaseManager()
cs = CounterService(db)
c1 = cs.create_counter('Test Counter', 'Test')
print(f'Created: {c1.counter_name}')
print(f'Total counters: {len(cs.get_all_counters())}')
"
```

## Support

For issues or questions, refer to the main README.md or contact your system administrator.
