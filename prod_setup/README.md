# Production Setup

This folder contains production-specific configuration files and credentials.

## Files

### Required for Production Deployment:

1. **`telegram_prod_token.txt`** _(not in git)_
   - Contains your production Telegram bot token
   - Get from @BotFather on Telegram
   - Format: Just the token, nothing else

2. **`prod_config.txt`** _(not in git)_
   - Contains production Google Sheets IDs and settings
   - Copy from `prod_config.txt.template` and customize

### Templates (safe to commit):

- **`prod_config.txt.template`** - Template for production config
- **`README.md`** - This file

## Setup Instructions

1. **Create production bot token file:**
   ```bash
   echo "your-production-bot-token-here" > prod_setup/telegram_prod_token.txt
   ```

2. **Create production config:**
   ```bash
   cp prod_setup/prod_config.txt.template prod_setup/prod_config.txt
   # Then edit prod_config.txt with your actual production sheet IDs
   ```

3. **Deploy to production:**
   ```bash
   ./deploy.sh prod
   ```

## What Changes Between Dev and Prod

| Setting | Dev | Prod |
|---------|-----|------|
| Bot Token | `telegram_dev_token.txt` | `prod_setup/telegram_prod_token.txt` |
| Secret Name | `telegram-bot-token-dev` | `telegram-bot-token` |
| Sheet IDs | Current dev sheets | Values from `prod_config.txt` |
| Service Account | Same (dev account with prod sheets access) | Same |

## Security

- All sensitive files in this folder are gitignored
- Only templates and documentation are committed
- Production credentials never leave this folder