"""
User-specific environment configuration system for Ultimate AI Assistant

This module provides a way to load different API tokens and environment variables
based on the USER_ID specified in config.py. Each user can have their own .env file
with their specific API keys and configurations.
"""

import os
import subprocess
import shutil
from pathlib import Path
from typing import Dict, Optional, Union, List
import logging
from dotenv import load_dotenv

from .config import APP_NAME

logger = logging.getLogger(__name__)

class UserEnvironmentManager:
    """Manages user-specific environment variables and API tokens"""
    
    def __init__(self, user_id: str):
        """Initialize UserEnvironmentManager for a specific user"""
        if not user_id:
            raise ValueError("user_id is required")
        # Normalize user_id to lowercase for consistency
        self.user_id = user_id.lower().strip()
        self.base_dir = Path(__file__).parent.parent  # ultimate-ai-assistant directory
        self.env_dir = self.base_dir / "user_data"
        
        # Ensure user_data directory exists
        self.env_dir.mkdir(exist_ok=True)
        
        # Define file paths
        self.user_env_file = self.env_dir / f".env.{self.user_id.lower()}"
        self.default_env_file = self.base_dir / ".env"
        self.template_file = self.env_dir / ".env.template"
        
        # Load environment variables
        self.load_user_environment()
    
    def load_user_environment(self):
        """Load environment variables in priority order: user-specific -> default -> system"""
        env_files_loaded: List[str] = []
        
        # 1. Load default .env file first (if exists)
        if self.default_env_file.exists():
            load_dotenv(self.default_env_file)
            env_files_loaded.append(str(self.default_env_file))
        
        # 2. Load user-specific .env file (overwrites defaults)
        if self.user_env_file.exists():
            load_dotenv(self.user_env_file, override=True)
            env_files_loaded.append(str(self.user_env_file))
            logger.info(f"Loaded user-specific environment for {self.user_id}")
        else:
            logger.warning(f"User-specific environment file not found: {self.user_env_file}")
            # Don't automatically create template for unregistered users
        
        if env_files_loaded:
            logger.info(f"Environment files loaded: {', '.join(env_files_loaded)}")
        else:
            logger.warning("No environment files found")
    
    def create_user_env_file(self, todoist_token: str, oauth_credentials_path: str):
        """Create a user environment file with the provided credentials"""
        env_content = f"""# User-specific Environment Variables for: {self.user_id.upper()}
# GOOGLE_API_KEY and ZEP_API_KEY are already in the main .env file

# Google Calendar MCP Server
GOOGLE_OAUTH_CREDENTIALS={oauth_credentials_path}

# Todoist Task Management Agent  
TODOIST_API_TOKEN={todoist_token}

# Other user-specific configurations
# Add any additional environment variables below
"""
        
        with open(self.user_env_file, 'w', encoding='utf-8') as f:
            f.write(env_content)
        
        logger.info(f"Created user environment file: {self.user_env_file}")
        return self.user_env_file
    
    def update_user_env_file(self, todoist_token: Optional[str] = None, oauth_credentials_path: Optional[str] = None):
        """Update existing user environment file with new values"""
        if not self.user_env_file.exists():
            raise FileNotFoundError(f"User environment file not found: {self.user_env_file}")
        
        # Read existing content
        with open(self.user_env_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Update lines
        updated_lines = []
        for line in lines:
            if todoist_token and line.startswith('TODOIST_API_TOKEN='):
                updated_lines.append(f'TODOIST_API_TOKEN={todoist_token}\n')
            elif oauth_credentials_path and line.startswith('GOOGLE_OAUTH_CREDENTIALS='):
                updated_lines.append(f'GOOGLE_OAUTH_CREDENTIALS={oauth_credentials_path}\n')
            else:
                updated_lines.append(line)
        
        # Write back to file
        with open(self.user_env_file, 'w', encoding='utf-8') as f:
            f.writelines(updated_lines)
        
        logger.info(f"Updated user environment file: {self.user_env_file}")
        return self.user_env_file
    
    def user_exists(self) -> bool:
        """Check if user environment file exists"""
        return self.user_env_file.exists()
    
    @classmethod
    def check_user_exists(cls, user_id: str) -> bool:
        """Static method to check if a user exists without creating UserEnvironmentManager instance"""
        base_dir = Path(__file__).parent.parent
        env_dir = base_dir / "user_data"
        user_env_file = env_dir / f".env.{user_id.lower().strip()}"
        return user_env_file.exists()
    
    def get_env_var(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get environment variable with user-specific priority"""
        return os.getenv(key, default)
    
    def set_env_var(self, key: str, value: str, persist: bool = False):
        """Set environment variable, optionally persisting to user file"""
        os.environ[key] = value
        
        if persist:
            self.update_env_var(key, value)
    
    def list_user_env_vars(self) -> Dict[str, str]:
        """List all environment variables from user's env file"""
        user_vars: Dict[str, str] = {}
        
        if self.user_env_file.exists():
            with open(self.user_env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        user_vars[key.strip()] = value.strip().strip('"').strip("'")
        
        return user_vars
    
    def get_user_info(self) -> Dict[str, Union[str, bool]]:
        """Get information about the current user's environment setup"""
        return {
            "user_id": self.user_id,
            "user_env_file": str(self.user_env_file),
            "user_env_exists": self.user_env_file.exists(),
            "default_env_exists": self.default_env_file.exists(),
            "template_file": str(self.template_file),
            "env_directory": str(self.env_dir)
        }

    def update_env_var(self, key: str, value: str) -> None:
        """Update or add a key-value pair in the user's env file"""
        env_lines: List[str] = []
        key_found = False
        
        # Read existing content
        if self.user_env_file.exists():
            with open(self.user_env_file, 'r') as f:
                env_lines = f.readlines()
        
        # Update existing key or prepare to add new one
        for i, line in enumerate(env_lines):
            if line.strip().startswith(f"{key}="):
                env_lines[i] = f"{key}={value}\n"
                key_found = True
                break
        
        # Add new key if not found
        if not key_found:
            env_lines.append(f"{key}={value}\n")
        
        # Write back to file
        with open(self.user_env_file, 'w') as f:
            f.writelines(env_lines)
        
        logger.info(f"Updated {key} in user environment file")

    def setup_gmail_authentication(self) -> Dict[str, Union[bool, str]]:
        """Set up Gmail authentication for this user"""
        import subprocess
        import shutil
        import tempfile
        
        try:
            # Get OAuth credentials path
            oauth_credentials = self.get_env_var("GOOGLE_OAUTH_CREDENTIALS")
            if not oauth_credentials:
                error_msg = "Google OAuth credentials not found for user"
                print(f"❌ Gmail auth error for {self.user_id}: {error_msg}")
                return {
                    "success": False,
                    "message": error_msg
                }
            
            # Resolve relative path to absolute
            if not os.path.isabs(oauth_credentials):
                oauth_credentials = os.path.join(self.base_dir, oauth_credentials)
            
            if not os.path.exists(oauth_credentials):
                error_msg = f"OAuth credentials file not found at: {oauth_credentials}"
                print(f"❌ Gmail auth error for {self.user_id}: {error_msg}")
                return {
                    "success": False,
                    "message": "OAuth credentials file not found"
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
                print(f"🗑️ Removed existing Gmail credentials for fresh authentication")
            
            print(f"🚀 Starting Gmail authentication for user {self.user_id}...")
            
            # Run Gmail authentication
            auth_process = subprocess.run(
                ["npx", "@gongrzhe/server-gmail-autoauth-mcp", "auth"],
                cwd=str(gmail_mcp_dir),
                capture_output=True,
                text=True,
                timeout=120  # 2 minute timeout
            )
            
            print(f"📤 Gmail auth command output:")
            print(f"   Return code: {auth_process.returncode}")
            print(f"   STDOUT: {auth_process.stdout}")
            print(f"   STDERR: {auth_process.stderr}")
            
            if auth_process.returncode != 0:
                error_msg = f"Gmail authentication failed: {auth_process.stderr}"
                print(f"❌ Gmail auth failed for {self.user_id}: {error_msg}")
                return {
                    "success": False,
                    "message": error_msg
                }
            
            # Check if credentials.json was generated
            if not global_credentials_path.exists():
                error_msg = "Gmail credentials were not generated"
                print(f"❌ Gmail auth error for {self.user_id}: {error_msg}")
                print(f"🔍 Expected credential file: {global_credentials_path}")
                return {
                    "success": False,
                    "message": error_msg
                }
            
            # Create user-specific gmail_credentials directory
            gmail_credentials_dir = self.env_dir / "gmail_credentials"
            gmail_credentials_dir.mkdir(exist_ok=True)
            print(f"📁 Gmail credentials directory: {gmail_credentials_dir}")
            
            # Move credentials to user-specific location
            user_credentials_path = gmail_credentials_dir / f"credentials_{self.user_id}.json"
            
            # Remove existing user credentials if they exist
            if user_credentials_path.exists():
                user_credentials_path.unlink()
                print(f"🗑️ Removed existing user-specific Gmail credentials")
            
            shutil.move(str(global_credentials_path), str(user_credentials_path))
            print(f"📦 Moved Gmail credentials to: {user_credentials_path}")
            
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
                logger.warning(f"Failed to clean up Gmail MCP directory: {cleanup_error}")
            
            print(f"✅ Gmail authentication completed successfully for user {self.user_id}")
            
            return {
                "success": True,
                "message": "Gmail authentication completed successfully",
                "credentials_path": str(user_credentials_path)
            }
            
        except subprocess.TimeoutExpired:
            error_msg = "Gmail authentication timed out. Please try again."
            print(f"⏰ Gmail auth timeout for {self.user_id}: {error_msg}")
            return {
                "success": False,
                "message": error_msg
            }
        except Exception as e:
            error_msg = f"Error setting up Gmail authentication: {str(e)}"
            logger.error(f"Error setting up Gmail authentication for user {self.user_id}: {e}")
            print(f"💥 Gmail auth exception for {self.user_id}: {error_msg}")
            return {
                "success": False,
                "message": error_msg
            }

    def setup_calendar_authentication(self) -> Dict[str, Union[bool, str]]:
        """Set up Google Calendar authentication for this user"""
        import subprocess
        import shutil
        
        try:
            # Get OAuth credentials path
            oauth_credentials = self.get_env_var("GOOGLE_OAUTH_CREDENTIALS")
            if not oauth_credentials:
                error_msg = "Google OAuth credentials not found for user"
                print(f"❌ Calendar auth error for {self.user_id}: {error_msg}")
                return {
                    "success": False,
                    "message": error_msg
                }
            
            # Resolve relative path to absolute
            if not os.path.isabs(oauth_credentials):
                oauth_credentials = os.path.join(self.base_dir, oauth_credentials)
            
            if not os.path.exists(oauth_credentials):
                error_msg = f"OAuth credentials file not found at: {oauth_credentials}"
                print(f"❌ Calendar auth error for {self.user_id}: {error_msg}")
                return {
                    "success": False,
                    "message": "OAuth credentials file not found"
                }
            
            print(f"🔑 Using OAuth credentials: {oauth_credentials}")
            
            # Create user-specific calendar_credentials directory
            calendar_credentials_dir = self.env_dir / "calendar_credentials"
            calendar_credentials_dir.mkdir(exist_ok=True)
            print(f"📁 Calendar credentials directory: {calendar_credentials_dir}")
            
            # Set the user-specific token path (this is where tokens will be stored)
            user_tokens_path = calendar_credentials_dir / f"credentials_{self.user_id}.json"
            print(f"📝 Target token path: {user_tokens_path}")
            
            # Remove existing token file if it exists (force fresh authentication)
            if user_tokens_path.exists():
                user_tokens_path.unlink()
                print(f"🗑️ Removed existing token file for fresh authentication")
            
            # Set up environment variables for calendar authentication
            calendar_env = os.environ.copy()
            calendar_env["GOOGLE_OAUTH_CREDENTIALS"] = oauth_credentials
            calendar_env["GOOGLE_CALENDAR_MCP_TOKEN_PATH"] = str(user_tokens_path)
            
            print(f"🚀 Starting Calendar authentication for user {self.user_id}...")
            print(f"📍 Working directory: {self.base_dir}")
            print(f"🔧 Environment variables set:")
            print(f"   GOOGLE_OAUTH_CREDENTIALS={oauth_credentials}")
            print(f"   GOOGLE_CALENDAR_MCP_TOKEN_PATH={user_tokens_path}")
            
            # Run Calendar authentication using published MCP server
            auth_process = subprocess.run(
                ["uv", "run", "npx", "-y", "@nihaal084/google-calendar-mcp", "auth"],
                cwd=str(self.base_dir),
                capture_output=True,
                text=True,
                env=calendar_env,
                timeout=120  # 2 minute timeout
            )
            
            print(f"📤 Calendar auth command output:")
            print(f"   Return code: {auth_process.returncode}")
            print(f"   STDOUT: {auth_process.stdout}")
            print(f"   STDERR: {auth_process.stderr}")
            
            if auth_process.returncode != 0:
                error_msg = f"Calendar authentication failed: {auth_process.stderr}"
                print(f"❌ Calendar auth failed for {self.user_id}: {error_msg}")
                return {
                    "success": False,
                    "message": error_msg
                }
            
            # Check if tokens were generated at the specified location
            if not user_tokens_path.exists():
                # Check if tokens were generated in the default location and move them
                default_tokens_path = Path.home() / ".config" / "google-calendar-mcp" / "tokens.json"
                print(f"🔍 Checking default token location: {default_tokens_path}")
                
                if default_tokens_path.exists():
                    print(f"📦 Found tokens in default location, moving to user-specific location")
                    shutil.move(str(default_tokens_path), str(user_tokens_path))
                    
                    # Clean up the default config directory if it's empty
                    try:
                        default_config_dir = Path.home() / ".config" / "google-calendar-mcp"
                        if default_config_dir.exists() and not any(default_config_dir.iterdir()):
                            default_config_dir.rmdir()
                            print(f"🧹 Cleaned up empty default config directory")
                    except Exception as cleanup_error:
                        logger.warning(f"Failed to clean up Calendar config directory: {cleanup_error}")
                else:
                    error_msg = "Calendar tokens were not generated in any expected location"
                    print(f"❌ Calendar auth error for {self.user_id}: {error_msg}")
                    print(f"🔍 Expected locations checked:")
                    print(f"   Primary: {user_tokens_path}")
                    print(f"   Fallback: {default_tokens_path}")
                    return {
                        "success": False,
                        "message": error_msg
                    }
            
            print(f"✅ Calendar authentication completed successfully for user {self.user_id}")
            print(f"📋 Token file created at: {user_tokens_path}")
            
            return {
                "success": True,
                "message": "Calendar authentication completed successfully",
                "credentials_path": str(user_tokens_path)
            }
            
        except subprocess.TimeoutExpired:
            error_msg = "Calendar authentication timed out. Please try again."
            print(f"⏰ Calendar auth timeout for {self.user_id}: {error_msg}")
            return {
                "success": False,
                "message": error_msg
            }
        except Exception as e:
            error_msg = f"Error setting up Calendar authentication: {str(e)}"
            logger.error(f"Error setting up Calendar authentication for user {self.user_id}: {e}")
            print(f"💥 Calendar auth exception for {self.user_id}: {error_msg}")
            return {
                "success": False,
                "message": error_msg
            }


def get_user_env_var(key: str, default: Optional[str] = None, user_id: Optional[str] = None) -> Optional[str]:
    """Convenience function to get user-specific environment variable"""
    if not user_id:
        raise ValueError("user_id is required for user-specific environment variables")
    user_env_manager = UserEnvironmentManager(user_id)
    return user_env_manager.get_env_var(key, default)

def set_user_env_var(key: str, value: str, user_id: Optional[str] = None, persist: bool = False):
    """Convenience function to set user-specific environment variable"""
    if not user_id:
        raise ValueError("user_id is required for user-specific environment variables")
    user_env_manager = UserEnvironmentManager(user_id)
    return user_env_manager.set_env_var(key, value, persist)

def get_user_info(user_id: str) -> Dict[str, Union[str, bool]]:
    """Convenience function to get user environment information"""
    if not user_id:
        raise ValueError("user_id is required")
    user_env_manager = UserEnvironmentManager(user_id)
    return user_env_manager.get_user_info()
