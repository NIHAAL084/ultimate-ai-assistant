"""
User-specific environment configuration system for Ultimate AI Assistant

This module provides a way to load different API tokens and environment variables
based on the USER_ID specified in config.py. Each user can have their own .env file
with their specific API keys and configurations.
"""

import os
from pathlib import Path
from typing import Dict, Optional, Union, List
import logging
from dotenv import load_dotenv

from .config import USER_ID

logger = logging.getLogger(__name__)

class UserEnvironmentManager:
    """Manages user-specific environment variables and API tokens"""
    
    def __init__(self, user_id: Optional[str] = None):
        self.user_id = user_id or USER_ID
        self.base_dir = Path(__file__).parent.parent  # ultimate-ai-assistant directory
        self.env_dir = self.base_dir / "environments"
        
        # Ensure environments directory exists
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
            self.create_user_env_template()
        
        if env_files_loaded:
            logger.info(f"Environment files loaded: {', '.join(env_files_loaded)}")
        else:
            logger.warning("No environment files found")
    
    def create_user_env_template(self):
        """Create a template environment file for the user"""
        template_content = f"""# User-specific Environment Variables for: {self.user_id}
# Copy this file to .env.{self.user_id.lower()} and fill in your API keys
# GOOGLE_API_KEY and ZEP_API_KEY are already in the main .env file

# Google Calendar MCP Server
GOOGLE_OAUTH_CREDENTIALS=/path/to/your/gcp-oauth.keys.json
GOOGLE_CALENDAR_MCP_TOKEN_PATH=/custom/token/path

# Todoist Task Management Agent  
TODOIST_API_TOKEN=your-todoist-api-token-here

# Other user-specific configurations
# Add any additional environment variables below
"""
        
        # Create user-specific template (only if it doesn't exist)
        user_template = self.env_dir / f".env.{self.user_id.lower()}.template"
        if not user_template.exists():
            with open(user_template, 'w', encoding='utf-8') as f:
                f.write(template_content)
            
            logger.info(f"Created environment template at: {user_template}")
            print(f"🔧 Created environment template for user '{self.user_id}' at:")
            print(f"   {user_template}")
            print(f"📝 Please copy this file to '.env.{self.user_id.lower()}' and fill in your API keys")
    
    def get_env_var(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get environment variable with user-specific priority"""
        return os.getenv(key, default)
    
    def set_env_var(self, key: str, value: str, persist: bool = False):
        """Set environment variable, optionally persisting to user file"""
        os.environ[key] = value
        
        if persist:
            self.update_user_env_file(key, value)
    
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

    def update_user_env_file(self, key: str, value: str) -> None:
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


# Global instance for easy access
user_env_manager = UserEnvironmentManager()

def get_user_env_var(key: str, default: Optional[str] = None) -> Optional[str]:
    """Convenience function to get user-specific environment variable"""
    return user_env_manager.get_env_var(key, default)

def set_user_env_var(key: str, value: str, persist: bool = False):
    """Convenience function to set user-specific environment variable"""
    return user_env_manager.set_env_var(key, value, persist)

def get_user_info() -> Dict[str, Union[str, bool]]:
    """Convenience function to get user environment information"""
    return user_env_manager.get_user_info()
