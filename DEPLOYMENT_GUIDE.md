# 🚀 Complete Deployment Guide - Telegram Bot Agency

This guide provides **step-by-step instructions** to deploy the Telegram bot to development and production environments on Google Cloud Platform.

## 📋 Before You Start - Requirements

### Required Tools (Install These First)
1. **Google Cloud SDK**: [Download here](https://cloud.google.com/sdk/docs/install)
2. **Git**: For version control
3. **Text editor**: VS Code, nano, or vim
4. **Terminal access**: Command line

### Required Accounts & Access
1. **Google Cloud Platform account** with billing enabled
2. **Telegram account** (to create bots with @BotFather)
3. **Access to Google Sheets** where your client data is stored
4. **Admin access** to the GCP project `promising-node-469902-m2`

## 🏗️ PART 1: Initial Setup (Do This Once)

### Step 1: Verify Google Cloud Access
```bash
# Login to Google Cloud (opens browser)
gcloud auth login

# Set your project
gcloud config set project promising-node-469902-m2

# Verify you're authenticated
gcloud auth list

# You should see your email marked as ACTIVE
```

### Step 2: Enable Required APIs
```bash
# Enable the APIs we need
gcloud services enable run.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable sheets.googleapis.com
gcloud services enable cloudbuild.googleapis.com
```

### Step 3: Clone/Navigate to Your Project
```bash
# If you haven't cloned the repo yet:
git clone https://github.com/eduardoge13/telegram-bot-agency.git
cd telegram-bot-agency

# If you already have it:
cd /path/to/telegram-bot-agency
git pull origin main
```

## 🧪 PART 2: Development Deployment (Test First)

### Step 1: Verify Development Files Exist
```bash
# Check that these files exist:
ls -la telegram_dev_token.txt    # Your dev bot token
ls -la credentials.json          # Your dev service account
ls -la deploy.sh                 # Deployment script

# If any are missing, stop here and create them first
```

### Step 2: Make Deploy Script Executable
```bash
chmod +x deploy.sh
```

### Step 3: Deploy to Development
```bash
./deploy.sh dev
```

**What this command does:**
- Uses your `telegram_dev_token.txt` for the bot token
- Uses your current Google Sheets IDs (the dev ones)
- Creates/updates Secret Manager secret: `telegram-bot-token-dev`
- Deploys to Cloud Run service: `telegram-bot-agency`
- Sets up health check endpoints

### Step 4: Test Development Deployment
```bash
# The script will show you a URL like:
# https://telegram-bot-agency-xxxxx.us-central1.run.app

# Test the bot by sending a client number to your dev bot on Telegram
# You should get back client information from your sheets
```

**✅ If development works:** Continue to production setup
**❌ If development fails:** Fix issues before proceeding to production

## 🚀 PART 3: Production Setup (More Complex)

### Step 1: Create Production Bot Token

1. **Open Telegram and find @BotFather**
2. **Send:** `/newbot`
3. **Follow prompts** to create your production bot
4. **Copy the token** (looks like: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)
5. **Save token to file:**
   ```bash
   echo "123456789:ABCdefGHIjklMNOpqrsTUVwxyz" > prod_setup/telegram_prod_token.txt
   ```

### Step 2: Set Up Production Google Sheets

**Option A: Use Same Sheets (Simple)**
1. Give your dev service account access to production project
2. Use same sheet IDs
3. Skip to Step 3

**Option B: Create New Production Sheets (Recommended)**

1. **Create Production Client Data Sheet:**
   ```
   - Go to Google Sheets
   - Create new spreadsheet
   - Copy the structure from your dev sheet (headers)
   - Add your production client data
   - Note the spreadsheet ID from URL: 
     https://docs.google.com/spreadsheets/d/[SPREADSHEET-ID]/edit
   ```

2. **Create Production Logs Sheet:**
   ```
   - Create another new spreadsheet
   - Leave it empty (bot will add headers automatically)
   - Note this spreadsheet ID too
   ```

3. **Share both sheets with your service account:**
   ```
   - Open each sheet
   - Click "Share" button
   - Add your service account email (from credentials.json)
   - Give "Editor" permission
   ```

### Step 3: Configure Production Settings

1. **Copy the template:**
   ```bash
   cp prod_setup/prod_config.txt.template prod_setup/prod_config.txt
   ```

2. **Edit the production config:**
   ```bash
   nano prod_setup/prod_config.txt
   # OR use VS Code:
   code prod_setup/prod_config.txt
   ```

3. **Update with YOUR actual values:**
   ```bash
   # Replace these with your actual production sheet IDs:
   PROD_SPREADSHEET_ID="1ABCdef123456789_YOUR_PRODUCTION_CLIENT_SHEET_ID"
   PROD_LOGS_SPREADSHEET_ID="1XYZ789abcdef456_YOUR_PRODUCTION_LOGS_SHEET_ID"
   
   # Update authorized users (your Telegram user ID):
   PROD_AUTHORIZED_USERS="8380841505"
   ```

4. **Save and close** the file

### Step 4: Deploy to Production

```bash
./deploy.sh prod
```

**What this command does:**
- Uses `prod_setup/telegram_prod_token.txt` for bot token
- Uses production sheet IDs from `prod_setup/prod_config.txt`
- Creates/updates Secret Manager secret: `telegram-bot-token` (no -dev suffix)
- Deploys to same Cloud Run service but with production configuration
- Tests the deployment

### Step 5: Test Production Deployment

1. **Check the health endpoint:**
   ```bash
   # Script shows URL like: https://telegram-bot-agency-xxxxx.us-central1.run.app
   curl https://telegram-bot-agency-xxxxx.us-central1.run.app/health
   
   # Should show: "status":"running" and your client count
   ```

2. **Test the production bot:**
   - Send a message to your production bot on Telegram
   - Try searching for a client number
   - Verify it returns data from your production sheets

## 🔧 PART 4: Switching Between Environments

### Deploy Development Changes
```bash
# Make your code changes
# Test locally if possible
# Then deploy to dev:
./deploy.sh dev

# Test in dev environment first
# Only deploy to prod when dev works
```

### Update Production
```bash
# After testing in dev:
./deploy.sh prod

# This updates the same service but with production tokens/sheets
```

### Change Production Configuration
```bash
# Edit production settings:
nano prod_setup/prod_config.txt

# Deploy with new settings:
./deploy.sh prod
```

## 🔍 PART 5: Monitoring & Troubleshooting

### Check Bot Status
```bash
# Get service URL:
gcloud run services describe telegram-bot-agency --region=us-central1 --format="value(status.url)"

# Check health:
curl https://your-service-url/health

# Should return JSON with:
# - "status": "running"
# - "bot_ready": true
# - "sheets_connected": true
# - "total_clients": [number]
```

### View Logs
```bash
# Real-time logs:
gcloud run services logs tail telegram-bot-agency --region=us-central1

# Recent logs:
gcloud run services logs read telegram-bot-agency --region=us-central1 --limit=50
```

### Common Issues & Solutions

**Problem: "Bot token file not found"**
```bash
# Solution: Create the token file
echo "your-bot-token-here" > telegram_dev_token.txt
# OR for production:
echo "your-production-bot-token-here" > prod_setup/telegram_prod_token.txt
```

**Problem: "Sheets not connected"**
```bash
# Solution: Check service account permissions
# 1. Open your Google Sheet
# 2. Click "Share"  
# 3. Add your service account email from credentials.json
# 4. Give "Editor" permission
```

**Problem: "Permission denied" errors**
```bash
# Solution: Check your GCP permissions
gcloud auth list
gcloud config set project promising-node-469902-m2
# You need Cloud Run Admin and Secret Manager Admin roles
```

## 📊 PART 6: Understanding What Gets Deployed

### File Structure
```
Local Files Used:          -> Cloud Run Service:
├── main.py                   ├── Container with Python app
├── bot_telegram_polling.py   ├── Health check endpoints  
├── requirements.txt          ├── Auto-restart capability
├── Dockerfile               └── Environment variables set

Secret Manager:             Environment Variables:
├── telegram-bot-token-dev     ├── GCP_PROJECT_ID  
├── telegram-bot-token         ├── SPREADSHEET_ID
└── google-credentials-json    ├── LOGS_SPREADSHEET_ID
                              └── AUTHORIZED_USERS
```

### Development vs Production Differences

| Component | Development | Production |
|-----------|-------------|------------|
| **Bot Token** | `telegram_dev_token.txt` | `prod_setup/telegram_prod_token.txt` |
| **Secret Name** | `telegram-bot-token-dev` | `telegram-bot-token` |
| **Sheets Config** | Hardcoded in script | From `prod_setup/prod_config.txt` |
| **Service Name** | `telegram-bot-agency` | `telegram-bot-agency` |
| **Testing** | Safe to test | **LIVE PRODUCTION** |

## ✅ Pre-Deployment Checklist

### Before EVERY Deployment:
- [ ] Code changes committed and pushed to GitHub
- [ ] No sensitive data (tokens, keys) in code  
- [ ] All required files exist locally

### Before PRODUCTION Deployment:
- [ ] Development deployment tested and working
- [ ] Production bot token created and saved
- [ ] Production Google Sheets created and shared
- [ ] Production config file updated with correct IDs
- [ ] Authorized users list verified
- [ ] Team notified about production deployment

## 🚨 Emergency Procedures

### Immediate Production Issues
```bash
# 1. Check current status
curl https://your-bot-url/health

# 2. View recent logs for errors
gcloud run services logs read telegram-bot-agency --region=us-central1 --limit=20

# 3. If needed, quickly rollback by redeploying previous working version
git checkout previous-working-commit
./deploy.sh prod
```

### Rollback to Previous Version
```bash
# List recent revisions
gcloud run revisions list --service=telegram-bot-agency --region=us-central1

# Rollback to specific revision
gcloud run services update-traffic telegram-bot-agency \
  --to-revisions=telegram-bot-agency-00XXX-xxx=100 \
  --region=us-central1
```

---

## 📞 Need Help?

1. **Check the logs first:** `gcloud run services logs read telegram-bot-agency --region=us-central1`
2. **Test health endpoint:** `curl https://your-service-url/health`  
3. **Verify bot token works:** Test bot manually on Telegram
4. **Check sheet permissions:** Try opening sheets with service account email

**Remember:** Always test in development before deploying to production!

**Google Service Account:**
1. Create new service account in GCP Console
2. Download JSON key
3. Save as `prod_setup/telegram_bot_production.json`
4. Share your production Google Sheets with the service account email

### 3. Create Production Google Sheets

**Client Data Sheet:**
- Copy your development sheet structure
- Add production client data
- Note the spreadsheet ID from URL

**Logs Sheet:**
- Create new empty Google Sheet
- Note the spreadsheet ID from URL

## 🎯 Deployment Commands

### Development Environment
- **Service Name**: `telegram-bot-agency-dev`
- **Secrets**: Uses `-dev` suffix
- **Sheets**: Development sheets
- **Command**: `./deploy.sh dev promising-node-469902-m2`

### Production Environment
- **Service Name**: `telegram-bot-agency`
- **Secrets**: Production secrets
- **Sheets**: Production sheets
- **Command**: `./deploy.sh prod your-production-project-id`

## 🔍 Monitoring

### Health Checks
```bash
# Development
curl https://telegram-bot-agency-dev-[hash].us-central1.run.app/health

# Production
curl https://telegram-bot-agency-[hash].us-central1.run.app/health
```

### View Logs
```bash
# Development
gcloud run services logs read telegram-bot-agency-dev --region=us-central1 --project=promising-node-469902-m2

# Production
gcloud run services logs read telegram-bot-agency --region=us-central1 --project=your-production-project-id
```

## 🔄 Deployment Features

### Automatic Secret Management
- Creates/updates secrets in Google Secret Manager
- Sets proper IAM permissions
- Uses different secret names for dev/prod

### Health Testing
- Tests basic health endpoint
- Tests detailed health endpoint
- Shows deployment summary

### Environment Isolation
- Separate service names
- Separate secrets
- Separate configurations

## 🚨 Emergency Procedures

### Rollback Production
```bash
# List revisions
gcloud run revisions list --service=telegram-bot-agency --region=us-central1 --project=your-prod-project

# Rollback to previous revision
gcloud run services update-traffic telegram-bot-agency \
  --to-revisions=telegram-bot-agency-00XXX-xxx=100 \
  --region=us-central1 \
  --project=your-prod-project
```

### Quick Production Hotfix
```bash
# Make code changes
# Deploy to dev first
./deploy.sh dev promising-node-469902-m2

# Test dev deployment
# Then deploy to prod
./deploy.sh prod your-production-project-id
```

## 📁 File Structure

```
telegram-bot-agency/
├── deploy.sh                           # Main deployment script
├── main.py                            # Application entry point
├── bot_telegram_polling.py            # Bot logic
├── requirements.txt                   # Dependencies
├── Dockerfile                         # Container config
├── prod_setup/                        # Production configuration
│   ├── PRODUCTION_SETUP.md           # Detailed setup guide
│   ├── prod_config.env.template       # Configuration template
│   ├── prod_config.env               # Your production config (gitignored)
│   ├── telegram_prod_token.txt       # Production bot token (gitignored)
│   └── telegram_bot_production.json  # Production service account (gitignored)
└── DEPLOYMENT_GUIDE.md               # This file
```

## ✅ Pre-deployment Checklist

### Development
- [ ] Code changes committed to git
- [ ] Local testing completed
- [ ] No sensitive data in code

### Production
- [ ] Development deployment tested
- [ ] Production configuration file created
- [ ] Production bot token added
- [ ] Production service account configured
- [ ] Production sheets created and shared
- [ ] Authorized users list verified
- [ ] Backup of current production taken

## 📊 Environment Comparison

| Feature | Development | Production |
|---------|------------|------------|
| Service Name | telegram-bot-agency-dev | telegram-bot-agency |
| Telegram Secret | telegram-bot-token-dev | telegram-bot-token |
| Credentials Secret | google-credentials-json-dev | google-credentials-json |
| Min Instances | 1 | 1 |
| CPU Throttling | Disabled | Disabled |
| Monitoring | Basic | Enhanced |

## 🔗 Useful Commands

```bash
# Check deployment status
gcloud run services list --region=us-central1

# Get service URL
gcloud run services describe telegram-bot-agency --region=us-central1 --format="value(status.url)"

# Update environment variables only
gcloud run services update telegram-bot-agency \
  --region=us-central1 \
  --update-env-vars="NEW_VAR=value"

# Scale service
gcloud run services update telegram-bot-agency \
  --region=us-central1 \
  --min-instances=2 \
  --max-instances=10
```