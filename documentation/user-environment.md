# User Environment Management

The Ultimate AI Assistant supports user-specific environment configurations, allowing multiple users to have their own API keys and settings for external services.

## Overview

While core services (Google AI API, Zep Memory) use the main `.env` file, user-specific services like Google Calendar and Todoist require individual API tokens. This system manages those user-specific configurations.

## Quick Setup

1. **Set your user ID** in `app/config.py`:

   ```python
   USER_ID = "NIHAAL"  # Your username
   ```

2. **Run the setup command**:

   ```bash
   python manage_users.py setup
   ```

3. **Copy and configure your environment file**:

   ```bash
   cp environments/.env.nihaal.template environments/.env.nihaal
   # Edit .env.nihaal with your actual API keys
   ```

## Environment File Structure

### Main Environment (`.env`)

Contains shared API keys:

- `GOOGLE_API_KEY`: Google AI API key
- `ZEP_API_KEY`: Zep memory service API key
- `ZEP_API_URL`: Zep service URL

### User-Specific Environment (`environments/.env.{username}`)

Contains user-specific API tokens:

- `GOOGLE_OAUTH_CREDENTIALS`: Path to Google OAuth JSON file
- `TODOIST_API_TOKEN`: User's Todoist API token
- `GOOGLE_CALENDAR_MCP_TOKEN_PATH`: Custom token storage path (optional)

## Management Commands

### Setup Environment

```bash
python manage_users.py setup [--user USERNAME]
```

### List All Users

```bash
python manage_users.py list
```

### Validate Configuration

```bash
python manage_users.py validate [--user USERNAME]
```

### Switch Active User

```bash
python manage_users.py switch --user USERNAME
```

## API Key Setup

### Google Calendar Integration

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Google Calendar API
4. Create OAuth 2.0 credentials (Desktop Application)
5. Download the JSON file
6. Set the file path in `GOOGLE_OAUTH_CREDENTIALS`

### Todoist Integration

1. Go to [Todoist App Console](https://developer.todoist.com/appconsole.html)
2. Create a new app
3. Copy the API token
4. Set `TODOIST_API_TOKEN` in your user environment file

## File Structure

```
ultimate-ai-assistant/
├── .env                          # Main environment (shared keys)
├── environments/
│   ├── .env.template            # Base template
│   ├── .env.nihaal             # User's actual environment
│   └── .env.john               # Another user's environment
├── app/
│   ├── config.py               # Contains active USER_ID
│   └── user_env.py             # Environment management system
└── manage_users.py             # User management CLI tool
```

## How It Works

1. **Priority Loading**: Environment variables are loaded in order:
   - User-specific `.env.{username}` file (highest priority)
   - Default `.env` file
   - System environment variables

2. **Automatic Templates**: If a user's environment file doesn't exist, a template is created automatically.

3. **Easy Switching**: Change active user by updating `USER_ID` in `config.py` or using the switch command.

## Security Notes

- Never commit actual `.env.*` files to version control
- Keep API keys secure and private
- Use different API keys for different users/environments
- Template files (`.template`) are safe to commit

## Troubleshooting

### Environment file not found

Run `python manage_users.py setup` to create templates and copy to actual environment files.

### API key not working

Use `python manage_users.py validate` to check your configuration and ensure no extra spaces or quotes around values.

### Wrong user environment loaded

Check `USER_ID` in `app/config.py` and use the switch command to change active user. Restart the application after switching.
