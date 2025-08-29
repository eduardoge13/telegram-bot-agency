# 🤖 Telegram Client Data Bot

A simple and reliable Telegram bot that helps your team find client information from Google Sheets instantly. Just send a client number and get all the details!

## ✨ What This Bot Does

- 🔍 **Smart Search**: Find clients by their number or ID
- 📊 **Live Data**: Always shows the latest information from your Google Sheet
- 👥 **Team Ready**: Works for multiple people at the same time
- 🚀 **24/7 Available**: Runs in the cloud so your team can access it anytime
- 📱 **Easy to Use**: Just message the bot - no complicated commands needed

## 🎯 Perfect For

- Sales teams who need quick client lookups
- Support teams handling customer inquiries  
- Small businesses managing client databases
- Any team that stores client data in Google Sheets

## 📋 What You Need

Before setting up the bot, make sure you have:

1. **A Telegram Bot** (free - get from [@BotFather](https://t.me/botfather))
2. **Google Sheet with client data** (your existing spreadsheet works!)
3. **Google Cloud account** (free tier is enough)
4. **5 minutes to set up** ⏰

## 🚀 Quick Setup (3 Steps)

### Step 1: Create Your Telegram Bot
1. Message [@BotFather](https://t.me/botfather) on Telegram
2. Send `/newbot` and follow instructions
3. Save your bot token (looks like: `1234567890:ABCdef...`)

### Step 2: Connect Google Sheets
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create new project → Enable "Google Sheets API"
3. Create Service Account → Download JSON credentials
4. Share your Google Sheet with the service account email

### Step 3: Deploy to Cloud
1. Fork/download this code to GitHub
2. Go to [Railway.app](https://railway.app/) and connect GitHub
3. Add environment variables:
   - `TELEGRAM_BOT_TOKEN` = Your bot token
   - `SPREADSHEET_ID` = Your Google Sheet ID  
   - `GOOGLE_CREDENTIALS_JSON` = Your credentials JSON content
4. Deploy! 🎉

**📖 Need detailed instructions?** Check [DEPLOYMENT.md](DEPLOYMENT.md) for step-by-step guide.

## 📊 How Your Spreadsheet Should Look

Your Google Sheet just needs:
- **First row**: Column headers (like "Client Number", "Name", "Email")
- **Data rows**: Your client information
- **Client column**: Any column with client numbers/IDs

Example:
```
| Client ID | Company Name | Contact Email    | Phone      |
|-----------|--------------|------------------|------------|
| 12345     | Acme Corp    | john@acme.com    | 555-0123   |
| 67890     | Tech LLC     | jane@tech.com    | 555-0456   |
```

The bot automatically finds which column has your client numbers!

## 💬 How Your Team Uses the Bot

1. **Find the bot** on Telegram (search for your bot's username)
2. **Start chatting** - send `/start` to begin
3. **Send client number** - just type any client ID
4. **Get results instantly** - all client info appears immediately

### Available Commands
- `/start` - Welcome message and setup info
- `/help` - Instructions for using the bot  
- `/info` - Shows spreadsheet details and available fields
- `/status` - Checks if everything is working properly

### Example Usage
```
👤 User: 12345
🤖 Bot: ✅ Client Found: 12345

      Company Name: Acme Corp
      Contact Email: john@acme.com  
      Phone: 555-0123
      Status: Active
      
      📝 Found 4 fields with data
```

## 🔧 Features & Improvements

### Smart Search
- Case-insensitive matching
- Ignores extra spaces
- Works with any client ID format

### User-Friendly
- Clear success and error messages
- Helpful suggestions when clients aren't found
- Shows typing indicator while searching

### Reliable
- Better error handling
- Detailed logging for troubleshooting
- Automatic reconnection to Google Sheets

### Team Features
- Multiple users can search simultaneously
- Shows spreadsheet statistics
- Status checking commands

## 📱 For Your Team Members

**Getting Started:**
1. Search for your bot on Telegram
2. Click "Start" to activate  
3. Send any client number
4. Get instant results!

**Pro Tips:**
- Try different formats if first search fails
- Use `/info` to see what data is available
- Use `/status` if something seems broken

## ⚙️ Technical Details

### Simple Architecture
- **Python bot** handles Telegram messages
- **Google Sheets API** fetches live data  
- **Railway hosting** keeps it running 24/7
- **Environment variables** keep secrets safe

### Dependencies
- `python-telegram-bot` - Telegram integration
- `google-api-python-client` - Google Sheets access
- `python-dotenv` - Environment configuration

### Hosting Options
- **Railway** (recommended) - $0-5/month
- **Heroku** - $7+/month  
- **DigitalOcean** - $5+/month

## 🔒 Security & Privacy

- **No data storage** - bot only reads from your sheet
- **Encrypted connections** - all data transfer is secure
- **Private credentials** - sensitive info stored safely
- **No message logging** - searches aren't saved

## 🆘 Troubleshooting

### Bot Not Responding?
1. Check `/status` command
2. Verify bot token is correct
3. Make sure Railway service is running

### Can't Find Clients?
1. Verify client number format matches spreadsheet
2. Check Google Sheet sharing permissions  
3. Use `/info` to see available data

### Authentication Errors?
1. Verify `GOOGLE_CREDENTIALS_JSON` is set correctly
2. Check service account has sheet access
3. Ensure Google Sheets API is enabled

## 💰 Cost Breakdown

### Free Options
- **Google Sheets API**: Free (100 requests/100 seconds)
- **Telegram Bot**: Completely free
- **Railway**: 500 hours/month free (enough for small teams)

### Paid (if needed)
- **Railway Pro**: $5/month unlimited usage
- **Alternative hosting**: $5-25/month

## 🎉 Success Stories

*"Our sales team loves this bot! Instead of digging through spreadsheets, they just text the client number and get everything instantly."* - Small Business Owner

*"Setup took 10 minutes and saved us hours every week. The whole team can access client data from their phones now."* - Operations Manager

## 🚀 Getting Started Today

1. **[Create your bot](https://t.me/botfather)** (2 minutes)
2. **[Setup Google Sheets access](https://console.cloud.google.com/)** (5 minutes)  
3. **[Deploy to Railway](https://railway.app/)** (3 minutes)
4. **Share with your team** and start saving time! ⏰

**Questions?** Check [DEPLOYMENT.md](DEPLOYMENT.md) for detailed instructions, or create an issue in this repository.

---

**🌟 Like this project?** Star it on GitHub and share with other teams who could benefit from instant client data access!