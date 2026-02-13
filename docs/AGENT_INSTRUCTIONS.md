# 🤖 Agent Instructions - Telegram Client Data Bot

## Project Overview

This is a **production Telegram bot** deployed on Google Cloud Run that provides instant client data lookups from Google Sheets for business teams. The bot is actively used by authorized users to search client information in real-time.

## Core Principles

### 1. **Production-Ready Code Only**
- All code changes must be thoroughly tested before deployment
- Never introduce breaking changes without validation
- Maintain backward compatibility with existing Google Sheets data
- Error handling is critical - the bot must gracefully handle all edge cases

### 2. **Security First**
- No sensitive data (tokens, credentials, IDs) in code or version control
- All secrets managed via Google Cloud Secret Manager
- User authorization strictly enforced (AUTHORIZED_USERS env var)
- Private/group chat access controlled appropriately

### 3. **Cost Optimization**
- Cloud Run configured to scale to zero when idle (min-instances=0)
- No unnecessary resource allocation
- Efficient polling intervals and API usage
- Serverless architecture for pay-per-use model

### 4. **User Experience Priority**
- Response time under 3 seconds for typical queries
- Clear, formatted Spanish responses with emojis
- Helpful error messages in Spanish
- Works seamlessly in both private chats and group contexts

## Architecture Overview

```
┌─────────────────┐
│  Telegram API   │
│   (Polling)     │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────┐
│   Google Cloud Run              │
│  ┌──────────────────────────┐   │
│  │  main.py (entrypoint)    │   │
│  │  - Flask health server   │   │
│  │  - Bot initialization    │   │
│  └────────┬─────────────────┘   │
│           ▼                      │
│  ┌──────────────────────────┐   │
│  │ bot_telegram_polling.py  │   │
│  │  - Message handling      │   │
│  │  - Client search logic   │   │
│  │  - Authorization         │   │
│  └────────┬─────────────────┘   │
│           ▼                      │
│  ┌──────────────────────────┐   │
│  │  SheetsManager           │   │
│  │  - Data caching          │   │
│  │  - Search indexing       │   │
│  │  - Auto-refresh          │   │
│  └────────┬─────────────────┘   │
└───────────┼─────────────────────┘
            │
            ▼
┌───────────────────────────┐
│   Google Sheets API       │
│  - Client data (read)     │
│  - Persistent logs (write)│
└───────────────────────────┘
```

## Critical Files

### `/main.py` - Application Entrypoint
- **Purpose**: Cloud Run container entry point
- **Responsibilities**:
  - Start Flask health check server (port 8080) in background thread
  - Initialize and run Telegram bot in main thread (required for asyncio)
  - Handle graceful shutdown on SIGTERM/SIGINT
- **DO NOT**: Run bot in daemon thread (asyncio requires main thread)
- **DO NOT**: Implement restart loops (let Cloud Run handle restarts)

### `/bot_telegram_polling.py` - Core Bot Logic
- **Purpose**: All Telegram bot functionality
- **Key Classes**:
  - `SheetsManager`: Google Sheets integration with caching and indexing
  - `PersistentLogger`: Logs all searches to separate Google Sheet
  - `TelegramBot`: Main bot class with message handlers
- **Message Format**: Spanish with emojis (see format specification below)
- **Search Logic**: Fuzzy matching with normalized phone numbers
- **Authorization**: Check user_id against AUTHORIZED_USERS env var

### `/deploy.sh` - Deployment Script
- **Purpose**: Automated deployment to Cloud Run (dev or prod)
- **Environments**:
  - `./deploy.sh dev` - Development bot with test data
  - `./deploy.sh prod` - Production bot with live client data
- **Configuration Files**:
  - Dev: `dev_config.env` + `telegram_dev_token.txt`
  - Prod: `prod_setup/prod_config.env` + `prod_setup/telegram_prod_token.txt`
- **Never**: Hardcode sensitive values in this script

## Response Format Specification

All successful client lookups must return this **exact format**:

```
✅ Cliente encontrado

Número 📞: [phone_number]
Cliente 🙋🏻‍♀️: [client_name]
Correo ✉️: [email or empty]
Otra Información ℹ️: [other_info or empty]

Buscado por: [@username or first_name]
```

**Implementation Notes**:
- First line: "✅ Cliente encontrado" (no colon, no client number)
- Field format: `Label: Value` (no bold tags, simple format)
- Empty fields show just the label with empty value
- Field mappings defined in `field_mappings` dict
- HTML escaping via `safe_html()` to prevent injection
- Parse mode: `HTML` for Telegram API

## Environment Variables

### Required (All Environments)
- `GCP_PROJECT_ID` - Google Cloud project identifier
- `SPREADSHEET_ID` - Main client data Google Sheet ID
- `LOGS_SPREADSHEET_ID` - Persistent logs Google Sheet ID
- `AUTHORIZED_USERS` - Comma-separated Telegram user IDs (e.g., "123456,789012")

### Managed by Cloud Run
- `PORT` - Flask server port (default: 8080, auto-set by Cloud Run)

### Secrets (via Secret Manager)
- `telegram-bot-token` (prod) or `telegram-bot-token-dev` (dev) - Bot token from @BotFather
- `google-credentials-json` - Service account credentials for Sheets API

## Deployment Process

### Development Deployment
```bash
./deploy.sh dev
```
- Uses dev configuration and test data
- Safe for testing new features
- Separate dev bot token and spreadsheets

### Production Deployment
```bash
./deploy.sh prod
```
- Deploys to live production service
- Uses production client data
- Requires careful validation before deployment

### Deployment Checklist
1. ✅ Test locally if possible
2. ✅ Review code changes for security issues
3. ✅ Verify environment configuration files exist
4. ✅ Check bot token file exists for target environment
5. ✅ Run deployment script
6. ✅ Monitor logs for first few minutes: `gcloud run services logs read telegram-bot-agency --region=us-central1 --project=promising-node-469902-m2 --tail`
7. ✅ Test bot with a real query in Telegram
8. ✅ Check health endpoint (will return 403 as service is private - this is correct)

## Common Development Tasks

### Adding a New Command
1. Add handler in `bot_telegram_polling.py`:
   ```python
   async def new_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
       # Implementation
   ```
2. Register in `setup_handlers()`:
   ```python
   self.application.add_handler(CommandHandler("newcmd", self.new_command))
   ```
3. Test locally, then deploy to dev, then to prod

### Modifying Search Logic
- **File**: `bot_telegram_polling.py`
- **Class**: `SheetsManager`
- **Method**: `get_client_data_async()`
- **Important**: Maintain fuzzy matching and phone number normalization
- **Test**: Try various phone number formats

### Updating Google Sheets Integration
- **Credentials**: Never commit credentials - always use Secret Manager
- **Scopes**: `https://www.googleapis.com/auth/spreadsheets`
- **Cache**: SheetsManager caches data - consider invalidation strategy
- **Index**: Automatic rebuilds on cache miss (background task)

### Changing Message Format
- **Location**: Search for "Cliente encontrado" in `bot_telegram_polling.py`
- **Update**: Both main handler and `_followup_after_rebuild()` method
- **Consistency**: Ensure same format in all response paths
- **Testing**: Test with real data to verify formatting

## Error Handling Patterns

### Graceful Degradation
```python
try:
    # Attempt operation
    result = await primary_operation()
except Exception as e:
    logger.error(f"Primary operation failed: {e}")
    # Fall back to simpler response
    try:
        await fallback_operation()
    except Exception:
        logger.debug("Fallback also failed - silent fail")
```

### User-Facing Errors (Spanish)
- ❌ Por favor, envía un número de cliente válido
- 🔄 Actualizando índice...
- 🔎 No se encontró información para el cliente
- ⚠️ Error al procesar la solicitud

### Logging Strategy
- `logger.info()` - User actions, successful operations
- `logger.warning()` - Recoverable issues, missing config
- `logger.error()` - Failures that impact functionality
- `logger.debug()` - Detailed troubleshooting (silent fails)

## Testing Guidelines

### Manual Testing Checklist
- [ ] Private chat: Send client number → Verify response format
- [ ] Group chat: Mention bot + client number → Verify response
- [ ] Invalid number → Verify error message
- [ ] Unauthorized user → Verify no response
- [ ] `/start` command → Verify welcome message
- [ ] `/info` command → Verify spreadsheet details
- [ ] `/status` command → Verify system status

### Before Production Deployment
1. Deploy to dev environment first
2. Test all critical paths
3. Verify logs show no errors
4. Check response times (should be < 3 seconds)
5. Test with real production data format (if possible)
6. Get approval from stakeholder

## Monitoring & Debugging

### Check Service Status
```bash
gcloud run services list --project=promising-node-469902-m2 --region=us-central1
```

### View Live Logs
```bash
gcloud run services logs read telegram-bot-agency \
  --project=promising-node-469902-m2 \
  --region=us-central1 \
  --tail
```

### Health Check
```bash
# Will return 403 (correct - service is private)
curl https://telegram-bot-agency-[hash].run.app/health
```

### Common Issues

**Bot not responding**:
- Check logs for errors
- Verify AUTHORIZED_USERS includes your Telegram user ID
- Check bot token is valid in Secret Manager
- Verify service is running (check Cloud Run console)

**Slow responses**:
- Check if cache is warming (first query after cold start)
- Verify Google Sheets API quotas not exceeded
- Check Cloud Run instance cold start time

**Wrong data returned**:
- Verify SPREADSHEET_ID points to correct sheet
- Check column mappings in code match sheet structure
- Review search normalization logic

## Code Style & Conventions

### Python Style
- Follow PEP 8
- Use type hints where helpful
- Async/await for I/O operations
- Descriptive variable names
- Comments for complex logic only

### Naming Conventions
- Classes: `PascalCase`
- Functions/methods: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- Private methods: `_leading_underscore`

### Import Order
1. Standard library
2. Third-party packages
3. Local modules

### Logging
- Use structured messages: `logger.info(f"Action: {details}")`
- Include context in error messages
- Use emojis in user-facing logs for visibility

## Security Considerations

### Never Commit
- Bot tokens
- Service account credentials
- User IDs
- Spreadsheet IDs (keep in env vars only)
- Any PII or sensitive business data

### Always Validate
- User authorization before processing requests
- Input sanitization (HTML escaping)
- Rate limiting (built into Telegram API)
- Environment variable presence before use

### Principle of Least Privilege
- Service account: Read-only on client sheet, write-only on logs sheet
- Bot token: Scoped to single bot
- Cloud Run: Private service, no public access
- Users: Explicit whitelist only

## Future Considerations

### Potential Improvements
- [ ] Webhook mode instead of polling (requires HTTPS endpoint setup)
- [ ] Redis cache for faster lookups (adds complexity + cost)
- [ ] Multiple spreadsheet support (multi-tenant)
- [ ] Advanced search (fuzzy name matching, not just phone numbers)
- [ ] Analytics dashboard (query frequency, popular searches)
- [ ] Batch operations (export, bulk search)

### Migration Path to Webhooks
If moving from polling to webhooks:
1. Set up Cloud Run to accept POST requests
2. Register webhook with Telegram API
3. Implement signature verification
4. Remove polling loop
5. Update deployment to use webhook mode
6. Test thoroughly (webhooks are harder to debug)

## Support & Escalation

### For Issues
1. Check logs first
2. Review recent deployments
3. Test in dev environment
4. If persistent, rollback to last known good version
5. Debug in isolation

### Rollback Procedure
```bash
# List revisions
gcloud run revisions list --service=telegram-bot-agency \
  --project=promising-node-469902-m2 --region=us-central1

# Route traffic to previous revision
gcloud run services update-traffic telegram-bot-agency \
  --to-revisions=REVISION_NAME=100 \
  --project=promising-node-469902-m2 --region=us-central1
```

---

**Remember**: This bot serves real users with production data. Every change should prioritize stability, security, and user experience. When in doubt, test in dev first.
