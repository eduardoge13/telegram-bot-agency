# 🤖 Agent Instructions - Telegram Client Data Bot

> **Este repositorio contiene más de un despliegue.** Este documento cubre el
> **bot de Telegram** (Cloud Run). Si vas a tocar el sitio web bajo `site/`
> (blueskytravelmx.com y la tienda Yoga Verde), su despliegue es distinto y
> tiene trampas propias: lee **[docs/SITE_DEPLOYMENT.md](SITE_DEPLOYMENT.md)**
> antes de desplegar.
>
> Resumen para el sitio: usa `site/scripts/deploy.sh` y **nunca** `rsync` ni
> `scp -r` (fallan en silencio y han destruido el código en el servidor).

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

## Yoga Verde Site Deployment Rule (Mandatory)

Yoga Verde is the static storefront under `site/src/pages/yoga-verde/` and is
served by the shared `bluesky-site` container on the VPS. When deploying this
site, always package the `site/` directory as a single `.tar.gz` tarball,
transfer that archive, extract it on the VPS, and rebuild/recreate the Docker
Compose service.

- Never use `rsync` for Yoga Verde deployments.
- Never use recursive directory copies such as `scp -r`.
- `scp` is permitted only for the single tarball artifact.
- Exclude `.git`, `node_modules`, `.astro`, `dist`, `.env` files, tokens,
  credentials, service-account JSON, private keys, and other secrets.
- Stage/extract the archive beside `/docker/blueskytravel-site` on the same
  volume, replace the complete release directory, and run `docker compose
  build` followed by `docker compose up -d` from the active root. Never apply
  the tarball as an additive overlay: deleted repository files must also
  disappear from the release.
- The script has a state-aware `EXIT`/`INT`/`TERM` rollback, verifies
  `/yoga-verde/deploy-manifest.json`, and refuses to replace a root containing
  secrets, databases or operational overrides.
- The final nginx stage upgrades Alpine packages and the deployment fails
  closed unless Trivy reports zero fixable `HIGH`/`CRITICAL` findings before
  `docker compose up -d`; do not bypass this gate.
- Deploy only from the checkout that contains the approved release commit. The
  preferred long-term source is the current `main` checkout; while a release
  is being reviewed, an explicitly named feature worktree is valid only after
  checking its branch, commit and diff. Never deploy from the stale
  `.claude/worktrees/yoga-verde-redesign` worktree.
- Verify `docker compose ps`, both live domains, and the build manifest after
  deployment.
- Read `docs/VPS_SERVICE_INVENTORY.md` and
  `docs/VPS_CLIENT_ONE_PAGER_2026-06-15.md` before changing VPS state.
- Do not deploy merely because a code change exists; deploy only when the
  user explicitly requests it or the active workflow requires it.

The current product/design brief for the storefront pass is kept in
`docs/YOGA_VERDE_OPUS5_MOBILE_PREMIUM_PROMPT.md`.
`docs/YOGA_VERDE_OPUS_PLAN_PROMPT.md` is an older historical brief; use the
Opus 5 prompt for the active iteration.

## Yoga Verde visual and interaction handoff (2026-08-05)

Yoga Verde is the active brand and project name. Do not refer to this site as
Dr Nature. The current iteration is an identity-compliance and premium-motion
pass, not a new product or catalog migration.

### Non-negotiable visual rules

- Treat the identity manual as the source of truth: cream `#F8E3D2`, terracotta
  `#C06145`, sage `#6B874C`, olive `#4F5E01` and forest `#183425`.
- Cream and warm white are the dominant surfaces. Forest green is an accent for
  text, active states, small highlights and primary actions; it must not become
  a full-width footer, newsletter, hero or bottom-of-page block.
- Prefer soft gradients, beveled/asymmetric radii and fine borders over rigid
  square panels, heavy shadows, decorative pills or app-like chrome.
- The hero is logo plus product slideshow. Do not restore the visible
  “Piel, cabello y bienestar” headline or other generic slogan copy.
- Keep the compact YG mark in the header; the full Yoga Verde logo belongs in
  the hero/brand areas and must remain legible without overwhelming mobile.
- Product derivatives under `public/yoga-verde/assets/products/display/` are
  intentional normalized assets. Preserve `object-fit: contain`, centered
  placement and consistent visual scale. Do not replace them with `cover` or
  reintroduce the old JPG whitespace problem.

### Interaction and QA rules

- Mobile product cards occupy the visible width; no accidental clipped second
  card and no document/body horizontal overflow at 320, 360, 390, 400 and
  414 px.
- Every “Ver detalle” trigger uses the shared inline SVG arrow, has a minimum
  44 px target, remains visibly separated from “Añadir”, and opens a usable
  detail sheet on mobile and desktop. The detail sheet must scroll internally,
  close by button, overlay and Escape, and restore focus.
- Scroll reveals should be calm and noticeable; the product slideshow may move
  faster to show variety. Respect `prefers-reduced-motion`.
- Before handoff, run `npm run check`, `npm run build`, and browser checks for
  the detail flow, catalog, cart, navigation highlight, first-slide render,
  overflow and console errors.

### Claude / Opus handoff

When Claude (including Opus 5) continues this site, it must first inspect the
current branch and worktree and must not assume that a stale Claude worktree is
the source of truth. It must preserve the normalized `display/*.webp` strategy,
the identity palette, the light premium surface treatment, the modal behavior,
and the no-`rsync` tarball deployment rule. Any deployment recommendation must
name the exact checkout and commit it was tested against. Claude should keep
site changes, deployment documentation and agent memory in focused commits;
never use `git add .` when unrelated work is present, and never silently
overwrite a dirty user checkout. If the visual result is in doubt, provide a
desktop and mobile screenshot/checklist before proposing deployment.

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
