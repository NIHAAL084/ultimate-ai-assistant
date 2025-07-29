# Gmail Credentials Directory

This directory stores user-specific Gmail authentication credentials generated during the registration process.

## Files Structure

- `credentials_{user_id}.json` - Gmail authentication tokens for each user
- Files are automatically created during user registration
- Each user gets their own isolated Gmail credentials

## Security

- All credential files are ignored by Git (see main .gitignore)
- Files contain sensitive authentication tokens - do not share or commit
- Credentials are automatically managed by the system during registration and authentication setup
