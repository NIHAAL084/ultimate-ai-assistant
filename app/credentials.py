"""
Simple credentials manager that gets credentials directly from the database
Replaces the user-specific env file functionality
"""

import os
import subprocess
import shutil
from typing import Dict, Optional, Union
from pathlib import Path
import logging

from .database import get_database
from .config import USER_DATA_LOCATION

logger = logging.getLogger(__name__)


def ensure_user_data_directories():
    """Ensure all necessary user data directories exist"""
    user_data_path = Path(USER_DATA_LOCATION)
    
    # Create main user_data directory
    user_data_path.mkdir(parents=True, exist_ok=True)
    
    # Create subdirectories for different credential types
    subdirs = ["credentials", "gmail_credentials", "calendar_credentials"]
    for subdir in subdirs:
        (user_data_path / subdir).mkdir(parents=True, exist_ok=True)
    
    logger.info("User data directories ensured at: %s", user_data_path)


class DatabaseCredentialsManager:
    """Manages user credentials directly from the database"""
    
    def __init__(self, user_id: str):
        """Initialize credentials manager for a specific user"""
        self.user_id = user_id.lower().strip()
        self.db = get_database()
    
    def get_todoist_token(self) -> Optional[str]:
        """Get Todoist API token for user"""
        user_data = self.db.get_user(self.user_id)
        if not user_data:
            return None
        return user_data.get('todoist_api_token')
    
    def get_google_oauth_credentials_file(self) -> Optional[str]:
        """
        Get the path to OAuth credentials file, ensuring it exists and is absolute
        Returns the absolute path to the credentials file, or None if not available
        """
        # Get the path from database
        user_data = self.db.get_user(self.user_id)
        if not user_data:
            return None
            
        oauth_path = user_data.get('google_oauth_credentials_path')
        if not oauth_path:
            logger.warning("No Google OAuth credentials path found for user %s", self.user_id)
            return None
        
        # Convert to absolute path if it's relative
        if not os.path.isabs(oauth_path):
            # Use centralized user data location
            oauth_path = os.path.join(USER_DATA_LOCATION, oauth_path)
        
        # Check if file exists
        if not os.path.exists(oauth_path):
            logger.warning("OAuth credentials file not found: %s", oauth_path)
            return None
        
        return oauth_path
    
    def get_gmail_credentials_file(self) -> Optional[str]:
        """Get Gmail credentials file path from database"""
        user_data = self.db.get_user(self.user_id)
        if not user_data:
            return None
        return user_data.get('gmail_credentials_file')
    
    def get_calendar_credentials_file(self) -> Optional[str]:
        """Get Calendar credentials file path from database"""
        user_data = self.db.get_user(self.user_id)
        if not user_data:
            return None
        return user_data.get('calendar_credentials_file')
    
    def verify_credentials_setup(self) -> Dict[str, bool]:
        """Verify that all credentials are properly set up for the user"""
        oauth_credentials = self.get_google_oauth_credentials_file()
        gmail_credentials = self.get_gmail_credentials_file()
        calendar_credentials = self.get_calendar_credentials_file()
        todoist_token = self.get_todoist_token()
        
        return {
            "oauth_credentials": oauth_credentials is not None and os.path.exists(oauth_credentials),
            "gmail_credentials": gmail_credentials is not None and os.path.exists(gmail_credentials),
            "calendar_credentials": calendar_credentials is not None and os.path.exists(calendar_credentials),
            "todoist_token": todoist_token is not None and len(todoist_token.strip()) > 0
        }
    
    def setup_gmail_authentication(self) -> Dict[str, Union[bool, str]]:
        """Set up Gmail authentication for this user"""
        try:
            # Get OAuth credentials path
            oauth_credentials = self.get_google_oauth_credentials_file()
            if not oauth_credentials:
                return {
                    "success": False,
                    "message": "No Google OAuth credentials found for user"
                }
            
            print(f"🔑 Using OAuth credentials: {oauth_credentials}")
            
            # Create Gmail MCP directory
            gmail_mcp_dir = Path.home() / ".gmail-mcp"
            gmail_mcp_dir.mkdir(exist_ok=True)
            print(f"📁 Gmail MCP directory: {gmail_mcp_dir}")
            
            # Copy OAuth credentials to Gmail MCP directory as gcp-oauth.keys.json
            gcp_oauth_keys_path = gmail_mcp_dir / "gcp-oauth.keys.json"
            shutil.copy2(oauth_credentials, gcp_oauth_keys_path)
            print(f"📋 Copied OAuth credentials to: {gcp_oauth_keys_path}")
            
            # Remove any existing credentials.json (force fresh authentication)
            global_credentials_path = gmail_mcp_dir / "credentials.json"
            if global_credentials_path.exists():
                global_credentials_path.unlink()
                print(f"🗑️ Removed existing credentials: {global_credentials_path}")
            
            print(f"🚀 Starting Gmail authentication for user {self.user_id}...")
            
            # Run Gmail authentication
            auth_process = subprocess.run(
                ["npx", "@gongrzhe/server-gmail-autoauth-mcp", "auth"],
                cwd=str(gmail_mcp_dir),
                capture_output=True,
                text=True,
                timeout=120,
                check=False
            )
            
            print("📤 Gmail auth command output:")
            print(f"   Return code: {auth_process.returncode}")
            print(f"   STDOUT: {auth_process.stdout}")
            print(f"   STDERR: {auth_process.stderr}")
            
            if auth_process.returncode != 0:
                return {
                    "success": False,
                    "message": f"Gmail authentication failed: {auth_process.stderr}"
                }
            
            # Check if credentials.json was generated
            if not global_credentials_path.exists():
                return {
                    "success": False,
                    "message": "Gmail authentication completed but credentials file not found"
                }
            
            # Create user-specific gmail_credentials directory
            user_data_path = Path(USER_DATA_LOCATION)
            gmail_credentials_dir = user_data_path / "gmail_credentials"
            gmail_credentials_dir.mkdir(parents=True, exist_ok=True)
            print(f"📁 Gmail credentials directory: {gmail_credentials_dir}")
            
            # Move credentials to user-specific location
            user_credentials_path = gmail_credentials_dir / f"credentials_{self.user_id}.json"
            
            # Remove existing user credentials if they exist
            if user_credentials_path.exists():
                user_credentials_path.unlink()
                print(f"🗑️ Removed existing user credentials: {user_credentials_path}")

            # Move the global credentials to user-specific location
            shutil.move(str(global_credentials_path), str(user_credentials_path))
            print(f"📦 Moved credentials to user-specific location: {user_credentials_path}")
            
            # Save Gmail credentials path to database
            try:
                self.db.update_user(
                    user_id=self.user_id,
                    gmail_credentials_file=str(user_credentials_path)
                )
                print(f"💾 Saved Gmail credentials path to database: {user_credentials_path}")
            except Exception as db_error:
                logger.warning("Failed to save Gmail credentials path to database: %s", str(db_error))
            
            # Clean up global Gmail MCP directory for next user
            try:
                # Remove the OAuth keys file
                if gcp_oauth_keys_path.exists():
                    gcp_oauth_keys_path.unlink()
                    
                # Remove the .gmail-mcp directory if it's empty
                if gmail_mcp_dir.exists() and not any(gmail_mcp_dir.iterdir()):
                    gmail_mcp_dir.rmdir()
                    
                print(f"🧹 Cleaned up global Gmail MCP directory for user {self.user_id}")
            except Exception as cleanup_error:
                # Don't fail the whole process if cleanup fails, just log it
                logger.warning("Failed to clean up Gmail MCP directory: %s", str(cleanup_error))
            
            return {
                "success": True,
                "message": f"Gmail authentication completed successfully for user {self.user_id}",
                "credentials_path": str(user_credentials_path)
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "message": "Gmail authentication timed out. Please try again."
            }
        except Exception as e:
            logger.error("Error setting up Gmail authentication for %s: %s", self.user_id, str(e))
            return {
                "success": False,
                "message": f"Gmail authentication failed: {str(e)}"
            }

    def setup_calendar_authentication(self) -> Dict[str, Union[bool, str]]:
        """Set up Google Calendar authentication for this user"""
        try:
            # Get OAuth credentials path
            oauth_credentials = self.get_google_oauth_credentials_file()
            if not oauth_credentials:
                return {
                    "success": False,
                    "message": "No Google OAuth credentials found for user"
                }
            
            print(f"🔑 Using OAuth credentials for Calendar: {oauth_credentials}")
            
            # Create user-specific calendar_credentials directory
            user_data_path = Path(USER_DATA_LOCATION)
            calendar_credentials_dir = user_data_path / "calendar_credentials"
            calendar_credentials_dir.mkdir(parents=True, exist_ok=True)
            print(f"📁 Calendar credentials directory: {calendar_credentials_dir}")
            
            # Set up user-specific token path for Calendar
            user_token_path = calendar_credentials_dir / f"credentials_{self.user_id}.json"
            print(f"📝 Target token path: {user_token_path}")
            
            # Remove existing token file if it exists (force fresh authentication)
            if user_token_path.exists():
                user_token_path.unlink()
                print(f"�️ Removed existing token file for fresh authentication")
            
            # Set up environment variables for calendar authentication
            calendar_env = os.environ.copy()
            calendar_env["GOOGLE_OAUTH_CREDENTIALS"] = oauth_credentials
            calendar_env["GOOGLE_CALENDAR_MCP_TOKEN_PATH"] = str(user_token_path)
            
            print(f"🚀 Starting Calendar authentication for user {self.user_id}...")
            print(f"📍 Working directory: {Path(__file__).parent.parent}")
            print("🔧 Environment variables set:")
            print(f"   GOOGLE_OAUTH_CREDENTIALS={oauth_credentials}")
            print(f"   GOOGLE_CALENDAR_MCP_TOKEN_PATH={user_token_path}")
            
            # Run Calendar authentication using published MCP server
            auth_process = subprocess.run(
                ["uv", "run", "npx", "-y", "@nihaal084/google-calendar-mcp", "auth"],
                cwd=str(Path(__file__).parent.parent),
                capture_output=True,
                text=True,
                env=calendar_env,
                timeout=120,  # 2 minute timeout
                check=False
            )
            
            print("📤 Calendar auth command output:")
            print(f"   Return code: {auth_process.returncode}")
            print(f"   STDOUT: {auth_process.stdout}")
            print(f"   STDERR: {auth_process.stderr}")
            
            if auth_process.returncode != 0:
                return {
                    "success": False,
                    "message": f"Calendar authentication failed: {auth_process.stderr}"
                }
            
            # Check if tokens were generated at the specified location
            if not user_token_path.exists():
                # Check if tokens were generated in the default location and move them
                default_tokens_path = Path.home() / ".config" / "google-calendar-mcp" / "tokens.json"
                print(f"🔍 Checking default token location: {default_tokens_path}")
                
                if default_tokens_path.exists():
                    print("📦 Found tokens in default location, moving to user-specific location")
                    shutil.move(str(default_tokens_path), str(user_token_path))
                    
                    # Save Calendar credentials path to database
                    try:
                        self.db.update_user(
                            user_id=self.user_id,
                            calendar_credentials_file=str(user_token_path)
                        )
                        print(f"💾 Saved Calendar credentials path to database: {user_token_path}")
                    except Exception as db_error:
                        logger.warning("Failed to save Calendar credentials path to database: %s", str(db_error))
                    
                    # Clean up the default config directory if it's empty
                    try:
                        default_config_dir = Path.home() / ".config" / "google-calendar-mcp"
                        if default_config_dir.exists() and not any(default_config_dir.iterdir()):
                            default_config_dir.rmdir()
                            print("🧹 Cleaned up empty default config directory")
                    except Exception as cleanup_error:
                        logger.warning("Failed to clean up Calendar config directory: %s", str(cleanup_error))
                else:
                    return {
                        "success": False,
                        "message": "Calendar tokens were not generated in any expected location"
                    }
            
            print(f"✅ Calendar authentication completed successfully for user {self.user_id}")
            print(f"📋 Token file created at: {user_token_path}")
            
            # Save Calendar credentials path to database
            try:
                self.db.update_user(
                    user_id=self.user_id,
                    calendar_credentials_file=str(user_token_path)
                )
                print(f"💾 Saved Calendar credentials path to database: {user_token_path}")
            except Exception as db_error:
                logger.warning("Failed to save Calendar credentials path to database: %s", str(db_error))
            
            return {
                "success": True,
                "message": f"Calendar authentication completed successfully for user {self.user_id}",
                "credentials_path": str(user_token_path)
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "message": "Calendar authentication timed out. Please try again."
            }
        except Exception as e:
            logger.error("Error setting up Calendar authentication for %s: %s", self.user_id, str(e))
            return {
                "success": False,
                "message": f"Calendar authentication failed: {str(e)}"
            }


def get_user_env_for_agent(user_id: Optional[str], service: str) -> Dict[str, str]:
    """
    Get environment variables for a specific user and service
    
    Args:
        user_id: User identifier
        service: Service name ('gmail', 'calendar', 'todoist')
    
    Returns:
        Dictionary of environment variables for the service
    """
    if not user_id:
        logger.warning("No user_id provided for %s service", service)
        return {}

    credentials_manager = DatabaseCredentialsManager(user_id)
    env_vars: Dict[str, str] = {}
    
    if service in ['gmail', 'calendar']:
        # For Google services, get the OAuth credentials file path
        oauth_file_path = credentials_manager.get_google_oauth_credentials_file()
        if oauth_file_path:
            if service == 'gmail':
                env_vars["GMAIL_OAUTH_PATH"] = oauth_file_path
                # Get Gmail credentials path from database (no fallback)
                gmail_credentials_path = credentials_manager.get_gmail_credentials_file()
                if gmail_credentials_path and os.path.exists(gmail_credentials_path):
                    env_vars["GMAIL_CREDENTIALS_PATH"] = gmail_credentials_path
            
            elif service == 'calendar':
                env_vars["GOOGLE_OAUTH_CREDENTIALS"] = oauth_file_path
                # Get Calendar credentials path from database (no fallback)
                calendar_credentials_path = credentials_manager.get_calendar_credentials_file()
                if calendar_credentials_path and os.path.exists(calendar_credentials_path):
                    env_vars["GOOGLE_CALENDAR_MCP_TOKEN_PATH"] = calendar_credentials_path
    
    elif service == 'todoist':
        # For Todoist, get the API token directly
        todoist_token = credentials_manager.get_todoist_token()
        if todoist_token:
            env_vars["TODOIST_API_TOKEN"] = todoist_token
    
    if not env_vars:
        logger.warning("No credentials found for user %s and service %s", user_id, service)
    
    return env_vars