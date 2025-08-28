# Deployment Guide: Running Your Telegram Bot Online

This guide will help you deploy your Telegram bot to the cloud so your 8-person team can access it 24/7.

## 🚀 Quick Deployment Options

### Option 1: Railway (Recommended - Free & Easy)
### Option 2: Heroku (Free tier discontinued, but reliable)
### Option 3: DigitalOcean App Platform (Paid, but very reliable)

---

## 🚂 Option 1: Railway Deployment (Recommended)

### Step 1: Prepare Your Google Service Account

1. **Go to [Google Cloud Console](https://console.cloud.google.com/)**
2. **Create a new project** or select existing one
3. **Enable Google Sheets API**:
   - Go to "APIs & Services" → "Library"
   - Search for "Google Sheets API" and enable it
4. **Create Service Account**:
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "Service Account"
   - Give it a name (e.g., "telegram-bot-sheets")
   - Click "Create and Continue"
   - Skip role assignment, click "Done"
5. **Generate Key**:
   - Click on your service account
   - Go to "Keys" tab
   - Click "Add Key" → "Create New Key"
   - Choose "JSON" format
   - Download the file

### Step 2: Share Your Google Sheet

1. **Open your Google Sheet**
2. **Click "Share"** (top right)
3. **Add your service account email** (found in the JSON file under `client_email`)
4. **Give it "Viewer" access**
5. **Copy the Spreadsheet ID** from the URL:
   ```
   https://docs.google.com/spreadsheets/d/SPREADSHEET_ID_HERE/edit
   ```

### Step 3: Deploy to Railway

1. **Go to [Railway.app](https://railway.app/)**
2. **Sign up/Login** with GitHub
3. **Click "New Project"** → "Deploy from GitHub repo"
4. **Connect your GitHub repository** (push your code first)
5. **Add Environment Variables**:
   - `TELEGRAM_BOT_TOKEN` = Your bot token from @BotFather
   - `SPREADSHEET_ID` = Your Google Sheet ID
   - `GOOGLE_CREDENTIALS_JSON` = Copy the entire content of your downloaded JSON file
6. **Deploy** - Railway will automatically build and deploy your bot

### Step 4: Test Your Bot

1. **Wait for deployment to complete** (usually 2-3 minutes)
2. **Test your bot** on Telegram
3. **Check Railway logs** if there are any issues

---

## 🎯 Option 2: Heroku Deployment

### Step 1: Install Heroku CLI
```bash
# Windows
winget install --id=Heroku.HerokuCLI

# Or download from: https://devcenter.heroku.com/articles/heroku-cli
```

### Step 2: Login and Deploy
```bash
heroku login
heroku create your-bot-name
git add .
git commit -m "Deploy bot"
git push heroku main
```

### Step 3: Set Environment Variables
```bash
heroku config:set TELEGRAM_BOT_TOKEN=your_bot_token
heroku config:set SPREADSHEET_ID=your_spreadsheet_id
heroku config:set GOOGLE_CREDENTIALS_JSON='{"type":"service_account",...}'
```

---

## ☁️ Option 3: DigitalOcean App Platform

1. **Go to [DigitalOcean App Platform](https://cloud.digitalocean.com/apps)**
2. **Create new app** from GitHub repository
3. **Configure environment variables** same as above
4. **Deploy** (starts at $5/month)

---

## 🔧 Environment Variables Setup

### Required Variables:

| Variable | Description | Example |
|----------|-------------|---------|
| `TELEGRAM_BOT_TOKEN` | Your bot token from @BotFather | `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz` |
| `SPREADSHEET_ID` | Your Google Sheet ID | `1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms` |
| `GOOGLE_CREDENTIALS_JSON` | Full content of your service account JSON file | `{"type":"service_account","project_id":"..."}` |

### How to Get Your Bot Token:

1. **Message [@BotFather](https://t.me/botfather) on Telegram**
2. **Send `/newbot`** (or use existing bot with `/mybots`)
3. **Follow instructions** to create bot
4. **Copy the token** (looks like: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`)

---

## 📱 Team Access Setup

### For Your 8 Team Members:

1. **Share the bot username** with your team
2. **Team members search for the bot** on Telegram
3. **They click "Start"** to begin using it
4. **Send client numbers** to get data

### Bot Commands for Team:
- `/start` - Welcome message
- `/help` - Instructions
- **Send any text** - Treated as client number to search

---

## 🔍 Monitoring & Maintenance

### Check Bot Status:
- **Railway Dashboard** → View logs and status
- **Test bot responses** regularly
- **Monitor error logs** for issues

### Common Issues & Solutions:

1. **Bot not responding**:
   - Check Railway logs
   - Verify environment variables
   - Ensure Google Sheet is shared with service account

2. **Authentication errors**:
   - Verify `GOOGLE_CREDENTIALS_JSON` is set correctly
   - Check service account has access to sheet

3. **Rate limiting**:
   - Google Sheets API has quotas
   - Monitor usage in Google Cloud Console

---

## 💰 Cost Breakdown

### Railway (Recommended):
- **Free tier**: 500 hours/month
- **Paid**: $5/month for unlimited usage
- **Perfect for small teams**

### Heroku:
- **Basic dyno**: $7/month
- **Standard dyno**: $25/month

### DigitalOcean:
- **Basic app**: $5/month
- **Professional**: $12/month

---

## 🎉 Success Checklist

- [ ] Google Service Account created
- [ ] Google Sheets API enabled
- [ ] Sheet shared with service account
- [ ] Bot deployed to cloud platform
- [ ] Environment variables set
- [ ] Bot responding to messages
- [ ] Team members can access bot
- [ ] Client data extraction working

---

## 🆘 Need Help?

1. **Check the logs** in your deployment platform
2. **Verify all environment variables** are set correctly
3. **Test Google Sheets access** manually
4. **Check bot token** is valid
5. **Ensure spreadsheet ID** is correct

Your bot should now be running 24/7 and accessible to your entire team! 🚀
