# 📋 Project Context - Telegram Client Data Bot

## Project Identity

**Name**: Telegram Client Data Bot (telegram-bot-agency)  
**Version**: 1.0 (Production)  
**Status**: ✅ Active in Production  
**Last Deployed**: December 30, 2025  
**Current Revision**: telegram-bot-agency-00003-qss  

## Business Context

### Purpose
Provide instant access to client information stored in Google Sheets through a Telegram bot interface. This enables sales and support teams to quickly retrieve client details during conversations or meetings without switching applications.

### Primary Users
- Sales team members (authorized Telegram user IDs)
- Support staff
- Account managers
- Anyone who needs quick client lookup on mobile/desktop

### Key Use Cases
1. **During client calls**: Quickly look up client details by phone number
2. **In team chats**: Share client information in group discussions
3. **Mobile access**: Access client database from anywhere via Telegram
4. **Audit trail**: All searches logged to separate spreadsheet for compliance

## Technical Stack

### Core Technologies
- **Language**: Python 3.12
- **Bot Framework**: python-telegram-bot 20.8 (async)
- **Hosting**: Google Cloud Run (serverless, scale-to-zero)
- **Data Source**: Google Sheets API v4
- **Secrets**: Google Cloud Secret Manager
- **Web Framework**: Flask 3.0.3 (health checks only)

### Key Dependencies
```
python-telegram-bot[job-queue]==20.8  # Telegram bot SDK
google-api-python-client==2.134.0     # Google Sheets API
google-cloud-secret-manager==2.20.0   # Secrets management
Flask==3.0.3                           # Health endpoint
gunicorn==22.0.0                       # WSGI server (backup)
pytz==2024.1                           # Timezone handling (Mexico City)
```

### Infrastructure
- **Platform**: Google Cloud Platform
- **Project ID**: promising-node-469902-m2
- **Region**: us-central1
- **Service**: Cloud Run (container-based)
- **Scaling**: 0-3 instances (scale to zero for cost optimization)
- **Resources**: 512Mi memory, 1 CPU
- **Timeout**: 300 seconds

## Data Architecture

### Google Sheets Structure

#### Primary Data Sheet (SPREADSHEET_ID)
```
| Column A           | Column B         | Column C      | Column D        |
|--------------------|------------------|---------------|-----------------|
| Client Phone Number| Cliente          | Correo        | Other Info      |
| 5536604547         | MORALES BRIEÑO...| email@...     | Additional data |
```

**Key Points**:
- First row contains headers (auto-detected)
- Client phone number in column A (primary search key)
- Additional client data in subsequent columns
- Bot auto-detects column structure on startup
- Supports flexible column arrangements

#### Logs Sheet (LOGS_SPREADSHEET_ID)
```
| Timestamp           | Level | User ID   | Username | Action  | Details      | Chat Type | Client # | Success |
|---------------------|-------|-----------|----------|---------|--------------|-----------|----------|---------|
| 2026-02-07 18:06:37 | INFO  | 8380841505| @arturo  | SEARCH  | Client: 5536 | group     | 5536...  | SUCCESS |
```

**Purpose**: Audit trail and analytics for all bot interactions

### Data Flow

```
User sends message
      ↓
Bot receives update (Telegram API polling)
      ↓
Extract & normalize phone number
      ↓
Check authorization (AUTHORIZED_USERS)
      ↓
Query SheetsManager cache
      ↓
[Cache Hit] → Return data immediately
      ↓
[Cache Miss] → Fetch from Google Sheets API
      ↓
Update cache & search index
      ↓
Format response with emojis
      ↓
Send to user via Telegram
      ↓
Log to persistent logs sheet (async)
```

## Application Architecture

### Process Model

```
Cloud Run Container
├── Port 8080 (Flask)
│   ├── GET / → Health check
│   └── GET /health → Detailed status
│
└── Main Thread (asyncio event loop)
    └── Telegram Bot (polling)
        ├── Fetch updates every ~10s
        ├── Process messages
        └── Send responses
```

### File Structure

```
telegram-bot-agency/
├── main.py                          # Entry point (Flask + Bot init)
├── bot_telegram_polling.py          # Core bot logic (1388 lines)
├── deploy.sh                        # Deployment automation
├── Dockerfile                       # Container definition
├── requirements.txt                 # Python dependencies
│
├── dev_config.env                   # Dev environment config
├── dev_config.env.template          # Template for dev setup
├── telegram_dev_token.txt           # Dev bot token (gitignored)
│
├── prod_setup/
│   ├── prod_config.env              # Production config
│   ├── telegram_prod_token.txt      # Prod bot token (gitignored)
│   └── README.md                    # Production setup guide
│
├── tests/                           # Test suite
│   ├── test_message_parsing.py
│   └── test_webhook.py
│
├── logs/                            # Local logs (dev only)
│
├── README.md                        # User documentation
├── DEPLOYMENT_GUIDE.md              # Deployment instructions
├── SECURITY.md                      # Security guidelines
├── AGENT_INSTRUCTIONS.md            # AI agent guidelines
└── PROJECT_CONTEXT.md               # This file
```

## Configuration Management

### Environment Variables (Runtime)

**Development** (`dev_config.env`):
```bash
DEV_SPREADSHEET_ID="[dev-sheet-id]"
DEV_LOGS_SPREADSHEET_ID="[dev-logs-sheet-id]"
DEV_AUTHORIZED_USERS="[test-user-ids]"
```

**Production** (`prod_setup/prod_config.env`):
```bash
PROD_SPREADSHEET_ID="1WssBio3qUqXUFOaEOk3638Hi1wGScFNNA21wh1P2G1s"
PROD_LOGS_SPREADSHEET_ID="1B52dpIGP3anSr_inRtFomGrqlJY-Ia_C2mqGpDlK6z0"
PROD_AUTHORIZED_USERS="8380841505,6842502456"
```

### Secrets (Google Cloud Secret Manager)

| Secret Name                | Purpose                    | Used By           |
|----------------------------|----------------------------|-------------------|
| telegram-bot-token         | Production bot token       | Production bot    |
| telegram-bot-token-dev     | Development bot token      | Development bot   |
| google-credentials-json    | Service account credentials| Both environments |

## Core Functionality

### 1. Client Search
- **Input**: Phone number (various formats accepted)
- **Normalization**: Strips spaces, dashes, parentheses
- **Matching**: Exact match after normalization
- **Response**: Formatted client data with emojis
- **Latency**: < 3 seconds (typically < 1 second with cache)

### 2. Authorization
- **Method**: Whitelist-based (AUTHORIZED_USERS)
- **Scope**: All bot commands and searches
- **Behavior**: Silent ignore for unauthorized users
- **Management**: Update env var and redeploy

### 3. Caching System
- **Type**: In-memory dictionary
- **TTL**: None (persists for instance lifetime)
- **Invalidation**: On cache miss (auto-rebuild)
- **Index**: Normalized phone number → row data
- **Warm-up**: Background rebuild on first miss

### 4. Logging
- **Local**: stdout (Cloud Run captures)
- **Persistent**: Google Sheets (audit trail)
- **Format**: Timestamp, level, user, action, details
- **Async**: Non-blocking writes to avoid delays

### 5. Commands

| Command  | Purpose                      | Availability      |
|----------|------------------------------|-------------------|
| /start   | Welcome message              | All users         |
| /help    | Usage instructions           | All users         |
| /info    | Spreadsheet statistics       | Authorized only   |
| /status  | System health check          | Authorized only   |
| /logs    | Recent activity (10 entries) | Authorized only   |
| /stats   | Usage analytics              | Authorized only   |

## Operational Characteristics

### Performance
- **Cold Start**: 5-10 seconds (first request after scale to zero)
- **Warm Response**: < 1 second (cached data)
- **Cache Miss**: 2-3 seconds (fetch + rebuild)
- **Polling Interval**: ~10 seconds
- **Concurrent Users**: Supports 2-3 simultaneous users efficiently

### Scaling Behavior
- **Min Instances**: 0 (scale to zero when idle)
- **Max Instances**: 3 (sufficient for current usage)
- **Trigger**: Telegram updates (bot wakes on incoming messages)
- **Cost**: ~$0 when idle, minimal cost during active use

### Reliability
- **Uptime**: 99.9% (managed by Cloud Run)
- **Error Recovery**: Automatic restart on crash
- **Retry Logic**: Built into Telegram bot framework
- **Graceful Shutdown**: SIGTERM handling for clean exits

## Development Workflow

### Local Development
```bash
# 1. Clone repository
git clone [repo-url]
cd telegram-bot-agency

# 2. Create virtual environment
python3.12 -m venv .venv
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp dev_config.env.template dev_config.env
# Edit dev_config.env with your values

# 5. Add bot token
echo "YOUR_DEV_BOT_TOKEN" > telegram_dev_token.txt

# 6. Run locally (requires credentials.json for local testing)
python main.py
```

### Deployment Workflow
```bash
# Development deployment
./deploy.sh dev

# Production deployment (after testing in dev)
./deploy.sh prod
```

### Testing Strategy
1. **Local Testing**: Run bot locally with dev token
2. **Dev Environment**: Deploy to dev, test with real Telegram
3. **Production Validation**: Deploy to prod, monitor logs
4. **Rollback Ready**: Keep previous revision available

## Security Model

### Authentication Layers
1. **User Authorization**: Telegram user ID whitelist
2. **Service Authentication**: Cloud Run requires GCP authentication
3. **API Access**: Service account for Google Sheets (read-only data, write-only logs)
4. **Secret Management**: No secrets in code or version control

### Data Privacy
- **PII Handling**: Client data treated as confidential
- **Audit Trail**: All searches logged with timestamp and user
- **Access Control**: Only authorized users can query
- **Logs**: Contain user IDs but are admin-only access

### Threat Mitigation
- **Injection**: HTML escaping on all outputs
- **Rate Limiting**: Handled by Telegram API (built-in)
- **DDoS**: Cloud Run auto-scaling + cost limits
- **Credential Exposure**: Secret Manager + .gitignore

## Cost Structure

### Google Cloud Costs (Monthly, Estimated)

| Service                 | Usage Pattern           | Estimated Cost |
|-------------------------|-------------------------|----------------|
| Cloud Run (compute)     | ~100 requests/day       | $0.50 - $2.00  |
| Cloud Run (networking)  | Minimal data transfer   | $0.10 - $0.50  |
| Secret Manager          | 3 secrets, low access   | $0.18          |
| Google Sheets API       | ~200 calls/day          | Free (quota)   |
| **Total**               |                         | **~$1-3/month**|

**Cost Optimization**:
- Scale to zero when idle (min-instances=0)
- No database costs (using Google Sheets)
- No storage costs (stateless container)
- Free tier covers most API usage

### Telegram Costs
- **Bot API**: Free (no cost for Telegram bot usage)

## Monitoring & Observability

### Key Metrics
- **Response Time**: < 3 seconds target
- **Error Rate**: < 1% target
- **Cache Hit Rate**: > 90% typical
- **Daily Queries**: ~50-100 (current usage)

### Logging Sources
1. **Cloud Run Logs**: All stdout/stderr
2. **Persistent Logs Sheet**: User actions and searches
3. **Telegram API Logs**: Included in Cloud Run logs

### Alerts (Recommended)
- [ ] Cloud Run errors > 5 in 5 minutes
- [ ] Response time > 10 seconds
- [ ] Service down > 5 minutes
- [ ] Memory usage > 450Mi

## Known Limitations

### Current Constraints
1. **Single Spreadsheet**: One data source per deployment
2. **Phone Number Only**: No name/email search (yet)
3. **No Bulk Operations**: One query at a time
4. **Polling Mode**: 10-second delay for updates (not instant)
5. **Cache Invalidation**: Manual redeploy to force refresh

### Intentional Design Choices
1. **Polling vs Webhooks**: Polling chosen for simplicity, easier debugging
2. **In-Memory Cache**: No external cache (Redis) to minimize complexity
3. **Scale to Zero**: Cost optimization over instant response
4. **Private Service**: No public access, requires authentication

## Future Roadmap

### Planned Improvements
- [ ] Fuzzy name search (not just phone numbers)
- [ ] Multiple spreadsheet support (multi-tenant)
- [ ] Webhook mode (faster, more efficient)
- [ ] Admin dashboard for analytics
- [ ] Scheduled cache refresh (e.g., daily at 6 AM)
- [ ] Export functionality (CSV/Excel)

### Technical Debt
- [ ] Add comprehensive unit tests
- [ ] Implement integration test suite
- [ ] Add performance benchmarks
- [ ] Document API surface for extensions
- [ ] Refactor large bot_telegram_polling.py into modules

## Dependencies & Integrations

### External Services
1. **Telegram Bot API**: Core messaging platform
2. **Google Sheets API**: Data source
3. **Google Cloud Secret Manager**: Credential storage
4. **Google Cloud Run**: Hosting platform

### Service Accounts
- **Role**: Custom role with Sheets read/write
- **Scopes**: `https://www.googleapis.com/auth/spreadsheets`
- **Storage**: Secret Manager as JSON key

## Troubleshooting Guide

### Common Issues

**Issue**: Bot not responding
- **Check**: Logs for errors
- **Verify**: Service is running (Cloud Run console)
- **Test**: Send /start command
- **Fix**: Redeploy if crashed

**Issue**: "Not authorized" or no response
- **Check**: User ID in AUTHORIZED_USERS
- **Verify**: Environment variable deployed correctly
- **Fix**: Add user ID to config and redeploy

**Issue**: Client not found (but exists in sheet)
- **Check**: Phone number format matches
- **Verify**: Spreadsheet ID is correct
- **Test**: Try with different phone format
- **Fix**: Update normalization logic or fix sheet data

**Issue**: Slow responses
- **Check**: Cold start vs warm start
- **Verify**: Cache is working
- **Monitor**: Google Sheets API quota
- **Fix**: Increase min-instances if consistent

## Contact & Support

**Repository**: [Insert GitHub/GitLab URL]  
**Deployment Owner**: eduardo.gaitan.escalante@gmail.com  
**Production Service**: telegram-bot-agency (GCP)  
**Development Service**: telegram-bot-dev (GCP)  

---

**Last Updated**: February 7, 2026  
**Document Version**: 1.0  
**Next Review**: March 2026
