#!/usr/bin/env python3
"""
User Environment Managemen        print(f"🔑 After copying, edit {user_env_file} and add your API keys:")
        print("   - GOOGLE_OAUTH_CREDENTIALS (path to your Google OAuth JSON file)")
        print("   - TODOIST_API_TOKEN (your Todoist API token)")
        print("   Note: GOOGLE_API_KEY and ZEP_API_KEY are already in the main .env file")ipt for Ultimate AI Assistant

This script helps manage user-specific environment configurations.
It allows users to set up their API keys and tokens for their specific user profile.
"""

import sys
import argparse
from pathlib import Path
from typing import Optional

# Add the app directory to the path
app_dir = Path(__file__).parent / "app"
sys.path.append(str(app_dir))

from app.user_env import UserEnvironmentManager
from app.config import USER_ID

def setup_user_environment(user_id: Optional[str] = None):
    """Set up environment for a specific user"""
    user_id = user_id or USER_ID
    env_manager = UserEnvironmentManager(user_id)
    
    print(f"🔧 Setting up environment for user: {user_id}")
    print(f"📁 Environment directory: {env_manager.env_dir}")
    
    user_env_file = env_manager.env_dir / f".env.{user_id.lower()}"
    template_file = env_manager.env_dir / f".env.{user_id.lower()}.template"
    
    if user_env_file.exists():
        print(f"✅ User environment file already exists: {user_env_file}")
        
        # Show current values (without revealing full API keys)
        user_vars = env_manager.list_user_env_vars()
        if user_vars:
            print("\n📋 Current environment variables:")
            for key, value in user_vars.items():
                if any(secret in key.lower() for secret in ['key', 'token', 'secret', 'password']):
                    masked_value = value[:8] + "*" * (len(value) - 8) if len(value) > 8 else "*" * len(value)
                    print(f"   {key}={masked_value}")
                else:
                    print(f"   {key}={value}")
    else:
        if template_file.exists():
            print(f"📄 Template file found: {template_file}")
            print(f"📝 Copy this template to create your environment file:")
            print(f"   cp {template_file} {user_env_file}")
        else:
            print(f"📄 Creating template file: {template_file}")
            env_manager.create_user_env_template()
        
        print(f"\n🔑 After copying, edit {user_env_file} and add your API keys:")
        print("   - GOOGLE_OAUTH_CREDENTIALS (path to your Google OAuth JSON file)")
        print("   - TODOIST_API_TOKEN (your Todoist API token)")
        print("   - ZEP_API_KEY (your Zep memory service API key)")
        print("   - GOOGLE_AI_API_KEY (your Google AI API key, if using)")

def list_users():
    """List all users with environment files"""
    env_dir = Path(__file__).parent / "environments"
    
    print("👥 Users with environment configurations:")
    
    if not env_dir.exists():
        print("   No environment directory found.")
        return
    
    env_files = list(env_dir.glob(".env.*"))
    template_files = [f for f in env_files if f.name.endswith('.template')]
    actual_env_files = [f for f in env_files if not f.name.endswith('.template')]
    
    if actual_env_files:
        print("\n✅ Active users:")
        for env_file in actual_env_files:
            username = env_file.name.replace('.env.', '').upper()
            print(f"   - {username} ({env_file})")
    
    if template_files:
        print("\n📋 Template files:")
        for template_file in template_files:
            username = template_file.name.replace('.env.', '').replace('.template', '').upper()
            print(f"   - {username} ({template_file})")
    
    if not env_files:
        print("   No environment files found.")

def validate_user_environment(user_id: Optional[str] = None):
    """Validate a user's environment configuration"""
    user_id = user_id or USER_ID
    env_manager = UserEnvironmentManager(user_id)
    
    print(f"🔍 Validating environment for user: {user_id}")
    
    info = env_manager.get_user_info()
    print(f"📁 Environment file: {info['user_env_file']}")
    print(f"✅ Environment file exists: {info['user_env_exists']}")
    
    if info['user_env_exists']:
        user_vars = env_manager.list_user_env_vars()
        
        required_vars = [
            'GOOGLE_OAUTH_CREDENTIALS',
            'TODOIST_API_TOKEN'
        ]
        
        print("\n🔑 Required API keys status:")
        for var in required_vars:
            value = env_manager.get_env_var(var)
            status = "✅ SET" if value else "❌ MISSING"
            print(f"   {var}: {status}")
        
        print("\n📋 All environment variables:")
        for key, value in user_vars.items():
            if any(secret in key.lower() for secret in ['key', 'token', 'secret', 'password']):
                masked_value = value[:8] + "*" * (len(value) - 8) if len(value) > 8 else "*" * len(value)
                print(f"   {key}={masked_value}")
            else:
                print(f"   {key}={value}")
    else:
        print("❌ Environment file not found. Run setup command first.")

def switch_user(new_user_id: str):
    """Help switch to a different user"""
    config_file = Path(__file__).parent / "app" / "config.py"
    
    print(f"🔄 Switching to user: {new_user_id}")
    
    # Read current config
    with open(config_file, 'r') as f:
        content = f.read()
    
    # Update USER_ID
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if line.strip().startswith('USER_ID ='):
            lines[i] = f'USER_ID = "{new_user_id.upper()}"'
            break
    
    # Write back
    with open(config_file, 'w') as f:
        f.write('\n'.join(lines))
    
    print(f"✅ Updated config.py with USER_ID = {new_user_id.upper()}")
    print(f"🔧 Setting up environment for new user...")
    
    # Setup environment for new user
    setup_user_environment(new_user_id.upper())

def main():
    parser = argparse.ArgumentParser(description="Manage user-specific environments for Ultimate AI Assistant")
    parser.add_argument('command', choices=['setup', 'list', 'validate', 'switch'], 
                       help='Command to execute')
    parser.add_argument('--user', '-u', help='User ID (defaults to current user from config)')
    
    args = parser.parse_args()
    
    try:
        if args.command == 'setup':
            setup_user_environment(args.user)
        elif args.command == 'list':
            list_users()
        elif args.command == 'validate':
            validate_user_environment(args.user)
        elif args.command == 'switch':
            if not args.user:
                print("❌ --user parameter required for switch command")
                sys.exit(1)
            switch_user(args.user)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
