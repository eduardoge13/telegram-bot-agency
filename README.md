# Telegram Bot for Google Sheets Data Extraction

A Telegram bot that extracts client data from Google Sheets based on client numbers. Users can simply send a client number to the bot and receive all associated information from the spreadsheet.

## Features

- 🤖 **Telegram Bot Integration**: Easy-to-use bot interface
- 📊 **Google Sheets API**: Direct connection to your spreadsheets
- 🔍 **Smart Search**: Automatically finds client data by number
- 📱 **User-Friendly**: Simple commands and clear responses
- 🔒 **Secure**: OAuth2 authentication with Google

## Prerequisites

Before running this bot, you'll need:

1. **Python 3.8+** installed on your system
2. **A Telegram Bot Token** (get from [@BotFather](https://t.me/botfather))
3. **Google Cloud Project** with Google Sheets API enabled
4. **Google Service Account** or OAuth2 credentials
5. **Google Spreadsheet** with client data

## Installation

### For Local Development:

1. **Clone or download** this project to your local machine

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   - Copy `config.env.example` to `.env`
   - Fill in your actual values:
     ```bash
     TELEGRAM_BOT_TOKEN=your_actual_bot_token
     SPREADSHEET_ID=your_actual_spreadsheet_id
     ```

### For Team Deployment (Recommended):

**To make this bot available 24/7 for your 8-person team, see [DEPLOYMENT.md](DEPLOYMENT.md) for complete cloud deployment instructions.**

**Quick Start:**
1. Follow the Railway deployment guide in `DEPLOYMENT.md`
2. Your team will be able to access the bot anytime via Telegram
3. No need to run the bot locally - it runs automatically in the cloud

## Google Sheets Setup

### Option 1: OAuth2 (Recommended for personal use)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the **Google Sheets API**
4. Go to **Credentials** → **Create Credentials** → **OAuth 2.0 Client IDs**
5. Choose **Desktop application**
6. Download the `credentials.json` file
7. Place it in your project directory

### Option 2: Service Account (Recommended for production)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the **Google Sheets API**
4. Go to **Credentials** → **Create Credentials** → **Service Account**
5. Download the JSON key file
6. Rename it to `credentials.json` and place in project directory
7. Share your Google Sheet with the service account email

## Spreadsheet Structure

Your Google Sheet should have:
- **Headers in the first row** (e.g., "Client Number", "Name", "Email", "Phone")
- **Client data starting from the second row**
- **A column containing client numbers** (the bot will automatically detect this)

Example structure:
```
| Client Number | Name        | Email           | Phone        |
|---------------|-------------|-----------------|--------------|
| 001          | John Doe    | john@email.com  | 555-0123     |
| 002          | Jane Smith  | jane@email.com  | 555-0456     |
```

## Usage

### Starting the Bot

1. **Run the bot**:
   ```bash
   python bot_telegram.py
   ```

2. **First run**: The bot will open a browser window for Google OAuth authentication
3. **Subsequent runs**: Uses cached authentication token

### Bot Commands

- `/start` - Welcome message and instructions
- `/help` - Detailed help information
- **Send any text** - Treated as a client number to search for

### Example Usage

1. Start a chat with your bot on Telegram
2. Send `/start` to see welcome message
3. Send a client number (e.g., "001")
4. Bot will search the spreadsheet and return client data
5. If found, displays all client information
6. If not found, shows helpful error message

## Configuration Options

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `TELEGRAM_BOT_TOKEN` | Your Telegram bot token | Yes |
| `SPREADSHEET_ID` | Google Sheets spreadsheet ID | Yes |

### Customizing Sheet Range

By default, the bot searches in `Sheet1!A:Z`. To customize:

1. Edit `bot_telegram.py`
2. Find the line: `range_name = 'Sheet1!A:Z'`
3. Change to your desired range (e.g., `'Clients!A:F'`)

## Troubleshooting

### Common Issues

1. **"TELEGRAM_BOT_TOKEN not found"**
   - Check your `.env` file exists and has the correct token

2. **"SPREADSHEET_ID not found"**
   - Verify your `.env` file contains the spreadsheet ID

3. **"credentials.json not found"**
   - Download credentials from Google Cloud Console
   - Place in project directory

4. **Authentication errors**
   - Delete `token.pickle` file and re-authenticate
   - Check your Google Cloud project has Sheets API enabled

5. **"No client found"**
   - Verify client number exists in spreadsheet
   - Check spreadsheet sharing permissions
   - Ensure correct sheet name and range

### Getting Help

- Check the logs for detailed error messages
- Verify all environment variables are set correctly
- Ensure Google Sheets API is enabled in your project
- Check spreadsheet sharing permissions

## Security Notes

- Keep your `.env` file private and never commit it to version control
- The `credentials.json` file contains sensitive information
- The `token.pickle` file stores authentication tokens
- Consider using environment variables in production

## Development

### Project Structure

```
bot-telegram/
├── bot_telegram.py      # Main bot code
├── requirements.txt     # Python dependencies
├── config.env.example  # Example configuration
├── README.md           # This file
├── credentials.json    # Google API credentials (not in repo)
├── token.pickle       # Authentication token (auto-generated)
└── .env               # Your actual configuration (not in repo)
```

### Adding Features

The bot is designed to be easily extensible:

- Add new commands in the `TelegramBot` class
- Modify sheet search logic in `GoogleSheetsManager`
- Customize response formatting in message handlers
- Add data validation or filtering

## License

This project is open source. Feel free to modify and distribute as needed.

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review Google Sheets API documentation
3. Check python-telegram-bot documentation
4. Create an issue in the project repository

