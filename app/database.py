"""
Database management for Ultimate AI Assistant
Handles SQLite database operations for user management
"""

import sqlite3
import logging
from pathlib import Path
from typing import Dict, Optional, List, Any
from contextlib import contextmanager
import bcrypt

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages SQLite database operations for user data"""
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize database manager"""
        if db_path is None:
            # Default database location in user_data directory
            base_dir = Path(__file__).parent.parent
            db_dir = base_dir / "user_data"
            db_dir.mkdir(exist_ok=True)
            db_path = str(db_dir / "users.db")
        
        self.db_path = str(db_path)
        self.init_database()
    
    def init_database(self):
        """Initialize database with required tables"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Create users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    password_hash TEXT NOT NULL,
                    location TEXT,
                    todoist_api_token TEXT,
                    google_oauth_credentials_path TEXT,
                    gmail_credentials_file TEXT,
                    calendar_credentials_file TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Add google_oauth_credentials_path column if it doesn't exist (migration)
            cursor.execute("PRAGMA table_info(users)")
            columns = [column[1] for column in cursor.fetchall()]
            if 'google_oauth_credentials_path' not in columns:
                cursor.execute("ALTER TABLE users ADD COLUMN google_oauth_credentials_path TEXT")
                logger.info("Added google_oauth_credentials_path column to users table")
            
            # Create index on user_id for faster lookups
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_users_user_id ON users(user_id)
            """)
            
            conn.commit()
            logger.info(f"Database initialized at {self.db_path}")
    
    @contextmanager
    def get_connection(self):
        """Get database connection with proper error handling"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Enable column access by name
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    
    def create_user(
        self, 
        user_id: str, 
        password: str,
        location: Optional[str] = None,
        todoist_api_token: Optional[str] = None,
        google_oauth_credentials_path: Optional[str] = None,
        gmail_credentials_file: Optional[str] = None,
        calendar_credentials_file: Optional[str] = None
    ) -> bool:
        """
        Create a new user in the database
        
        Args:
            user_id: Unique user identifier
            password: Plain text password (will be hashed)
            location: User's location
            todoist_api_token: Todoist API token
            google_oauth_credentials_path: Path to Google OAuth credentials JSON file
            gmail_credentials_file: Gmail OAuth credentials filename
            calendar_credentials_file: Calendar OAuth credentials filename
            
        Returns:
            True if user created successfully, False if user already exists
        """
        try:
            password_hash = self.hash_password(password)
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO users (
                        user_id, password_hash, location, todoist_api_token,
                        google_oauth_credentials_path, gmail_credentials_file, calendar_credentials_file
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    user_id.lower().strip(),
                    password_hash,
                    location,
                    todoist_api_token,
                    google_oauth_credentials_path,
                    gmail_credentials_file,
                    calendar_credentials_file
                ))
                
                conn.commit()
                logger.info(f"User {user_id} created successfully")
                return True
                
        except sqlite3.IntegrityError:
            logger.warning(f"User {user_id} already exists")
            return False
        except Exception as e:
            logger.error(f"Error creating user {user_id}: {e}")
            raise
    
    def authenticate_user(self, user_id: str, password: str) -> bool:
        """
        Authenticate user with password
        
        Args:
            user_id: User identifier
            password: Plain text password
            
        Returns:
            True if authentication successful, False otherwise
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute(
                    "SELECT password_hash FROM users WHERE user_id = ?",
                    (user_id.lower().strip(),)
                )
                
                result = cursor.fetchone()
                if result is None:
                    logger.warning(f"User {user_id} not found")
                    return False
                
                return self.verify_password(password, result['password_hash'])
                
        except Exception as e:
            logger.error(f"Error authenticating user {user_id}: {e}")
            return False
    
    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user information (excluding password hash)
        
        Args:
            user_id: User identifier
            
        Returns:
            User data dictionary or None if not found
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT user_id, location, todoist_api_token,
                           google_oauth_credentials_path, gmail_credentials_file, calendar_credentials_file,
                           created_at, updated_at
                    FROM users WHERE user_id = ?
                """, (user_id.lower().strip(),))
                
                result = cursor.fetchone()
                if result is None:
                    return None
                
                return dict(result)
                
        except Exception as e:
            logger.error(f"Error getting user {user_id}: {e}")
            return None
    
    def update_user(
        self,
        user_id: str,
        password: Optional[str] = None,
        location: Optional[str] = None,
        todoist_api_token: Optional[str] = None,
        google_oauth_credentials_path: Optional[str] = None,
        gmail_credentials_file: Optional[str] = None,
        calendar_credentials_file: Optional[str] = None
    ) -> bool:
        """
        Update user information
        
        Args:
            user_id: User identifier
            password: New password (will be hashed)
            location: New location
            todoist_api_token: New Todoist API token
            gmail_credentials_file: New Gmail credentials filename
            calendar_credentials_file: New Calendar credentials filename
            
        Returns:
            True if update successful, False if user not found
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Build dynamic update query
                update_fields: List[str] = []
                values: List[Any] = []
                
                if password is not None:
                    update_fields.append("password_hash = ?")
                    values.append(self.hash_password(password))
                
                if location is not None:
                    update_fields.append("location = ?")
                    values.append(location)
                
                if todoist_api_token is not None:
                    update_fields.append("todoist_api_token = ?")
                    values.append(todoist_api_token)
                
                if google_oauth_credentials_path is not None:
                    update_fields.append("google_oauth_credentials_path = ?")
                    values.append(google_oauth_credentials_path)
                
                if gmail_credentials_file is not None:
                    update_fields.append("gmail_credentials_file = ?")
                    values.append(gmail_credentials_file)
                
                if calendar_credentials_file is not None:
                    update_fields.append("calendar_credentials_file = ?")
                    values.append(calendar_credentials_file)
                
                if not update_fields:
                    logger.warning("No fields to update")
                    return False
                
                # Always update the updated_at timestamp
                update_fields.append("updated_at = CURRENT_TIMESTAMP")
                values.append(user_id.lower().strip())
                
                query = f"""
                    UPDATE users 
                    SET {', '.join(update_fields)}
                    WHERE user_id = ?
                """
                
                cursor.execute(query, values)
                
                if cursor.rowcount == 0:
                    logger.warning(f"User {user_id} not found for update")
                    return False
                
                conn.commit()
                logger.info(f"User {user_id} updated successfully")
                return True
                
        except Exception as e:
            logger.error(f"Error updating user {user_id}: {e}")
            raise
    
    def user_exists(self, user_id: str) -> bool:
        """
        Check if user exists in database
        
        Args:
            user_id: User identifier
            
        Returns:
            True if user exists, False otherwise
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute(
                    "SELECT 1 FROM users WHERE user_id = ? LIMIT 1",
                    (user_id.lower().strip(),)
                )
                
                return cursor.fetchone() is not None
                
        except Exception as e:
            logger.error(f"Error checking if user {user_id} exists: {e}")
            return False
    
    def delete_user(self, user_id: str) -> bool:
        """
        Delete user from database
        
        Args:
            user_id: User identifier
            
        Returns:
            True if deletion successful, False if user not found
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id.lower().strip(),))
                
                if cursor.rowcount == 0:
                    logger.warning(f"User {user_id} not found for deletion")
                    return False
                
                conn.commit()
                logger.info(f"User {user_id} deleted successfully")
                return True
                
        except Exception as e:
            logger.error(f"Error deleting user {user_id}: {e}")
            raise


# Global database instance
_db_manager: Optional[DatabaseManager] = None

def get_database() -> DatabaseManager:
    """Get global database manager instance"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager
