import hashlib
import uuid
from datetime import datetime, timedelta
from typing import Optional, Tuple
from app.models.user import User, AdminSession
from app.database.db_manager import DatabaseManager
from app.utils.validators import validate_email, validate_password, validate_username

class AuthService:
    """Service handling clean admin authentication and session management."""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
        self._ensure_default_admin()
    
    def _ensure_default_admin(self):
        """Seeds a default administrator account if the system has none."""
        if not self.db.get_user_by_username('admin'):
            default_admin = User(
                user_id=str(uuid.uuid4()),
                username='admin',
                password_hash=self._hash('Admin123'),
                email='admin@example.com',
                full_name='Administrator',
                role='admin',
                department='General'
            )
            self.db.create_user(default_admin)
    
    @staticmethod
    def _hash(text: str) -> str:
        """Utility to securely hash text with SHA-256."""
        return hashlib.sha256(text.encode()).hexdigest()

    def register_user(self, username: str, password: str, email: str, full_name: str, role: str, department: str) -> Tuple[bool, str]:
        """Validates inputs and registers a unique user into the database."""
        is_valid, msg = validate_username(username)
        if not is_valid:
            return False, msg

        is_valid, msg = validate_password(password)
        if not is_valid:
            return False, msg

        is_valid, msg = validate_email(email)
        if not is_valid:
            return False, msg

        if self.db.get_user_by_username(username):
            return False, "Username already taken"

        if role not in {"admin", "manager", "cashier"}:
            return False, "Role must be admin, manager, or cashier"
        
        new_user = User(
            user_id=str(uuid.uuid4()),
            username=username,
            password_hash=self._hash(password),
            email=email,
            full_name=full_name,
            role=role,
            department=department
        )
        
        if self.db.create_user(new_user):
            return True, "User registered successfully"
        return False, "Database error during registration"

    def login(self, username: str, password: str) -> Tuple[bool, Optional[AdminSession], str]:
        """Authenticates an active user and registers a new login session."""
        user = self.db.get_user_by_username(username)
        
        if not user or not user.is_active or user.password_hash != self._hash(password):
            return False, None, "Invalid username or password"
        
        user.update_last_login()
        self.db.update_user(user)
        
        session = AdminSession(
            session_id=str(uuid.uuid4()),
            user_id=user.user_id,
            username=user.username,
            login_time=datetime.now().isoformat()
        )
        
        self.db.data['sessions'][session.session_id] = session.to_dict()
        self.db.save_database()
        
        return True, session, "Login successful"

    def logout(self, session_id: str) -> bool:
        """Explicitly deactivates an active session token."""
        session = self.db.data['sessions'].get(session_id)
        if session:
            session['is_active'] = False
            self.db.save_database()
            return True
        return False

    def _is_expired(self, login_time_str: str) -> bool:
        """Helper to compute if a session has passed its 24-hour validity window."""
        login_time = datetime.fromisoformat(login_time_str)
        return datetime.now() - login_time > timedelta(hours=24)

    def verify_session(self, session_id: str) -> Tuple[bool, Optional[User]]:
        """Validates a session's existence, structural status, and age."""
        session = self.db.data['sessions'].get(session_id)
        if not session or not session.get('is_active', False):
            return False, None
        
        if self._is_expired(session['login_time']):
            session['is_active'] = False
            self.db.save_database()
            return False, None
        
        return True, self.db.get_user(session['user_id'])

    def change_password(self, user_id: str, old_password: str, new_password: str) -> Tuple[bool, str]:
        """Allows a user to securely rotate their password after verification."""
        user = self.db.get_user(user_id)
        if not user or user.password_hash != self._hash(old_password):
            return False, "Verification failed: Incorrect user or password"
        
        is_valid, msg = validate_password(new_password)
        if not is_valid:
            return False, msg
        
        user.password_hash = self._hash(new_password)
        self.db.update_user(user)
        return True,
