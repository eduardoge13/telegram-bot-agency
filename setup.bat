@echo off
echo Setting up Telegram Bot with Google Sheets integration...
echo.

echo Installing Python dependencies...
pip install -r requirements.txt

echo.
echo Creating .env file...
if not exist .env (
    echo # Telegram Bot Configuration > .env
    echo TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here >> .env
    echo. >> .env
    echo # Google Sheets Configuration >> .env
    echo SPREADSHEET_ID=your_google_spreadsheet_id_here >> .env
    echo .env file created! Please edit it with your actual values.
) else (
    echo .env file already exists.
)

echo.
echo Setup completed!
echo.
echo Next steps:
echo 1. Edit .env file with your actual values
echo 2. Download credentials.json from Google Cloud Console
echo 3. Place credentials.json in this directory
echo 4. Run: python bot_telegram.py
echo.
pause

