from dataclasses import dataclass, asdict
from typing import Optional


class UserRole:
    STUDENT = "student"
    CASHIER = "cashier"
    ADMIN = "admin"


class PriorityType:
    NONE = "none"      # Regular users
    PWD = "pwd"        
    SENIOR = "senior" 


@dataclass
class User:
    user_id: str                   
    name: str                      
    role: str                      
    priority_type: str = PriorityType.NONE  
    email: Optional[str] = None    

    def __post_init__(self):
        valid_roles = [UserRole.STUDENT, UserRole.CASHIER, UserRole.ADMIN]
        if self.role not in valid_roles:
            raise ValueError(f"Invalid role. Choose from: {valid_roles}")

        valid_priorities = [PriorityType.NONE, PriorityType.PWD, PriorityType.SENIOR]
        if self.priority_type not in valid_priorities:
            raise ValueError(f"Invalid priority type. Choose from: {valid_priorities}")

    @property
    def has_priority(self) -> bool:
        return self.priority_type in [PriorityType.PWD, PriorityType.SENIOR]

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'User':
        return cls(
            user_id=data.get("user_id"),
            name=data.get("name"),
            role=data.get("role"),
            priority_type=data.get("priority_type", PriorityType.NONE),
            email=data.get("email")
        )
