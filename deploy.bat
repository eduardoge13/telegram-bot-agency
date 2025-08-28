@echo off
echo ========================================
echo Telegram Bot Deployment Helper
echo ========================================
echo.

echo This script will help you prepare your bot for deployment.
echo.

echo Step 1: Make sure you have:
echo - A Telegram bot token from @BotFather
echo - A Google Service Account JSON file
echo - Your Google Sheet ID
echo - A GitHub repository
echo.

echo Step 2: Push your code to GitHub:
echo git add .
echo git commit -m "Prepare for deployment"
echo git push origin main
echo.

echo Step 3: Deploy to Railway:
echo 1. Go to https://railway.app/
echo 2. Sign in with GitHub
echo 3. Click "New Project"
echo 4. Select "Deploy from GitHub repo"
echo 5. Choose your repository
echo 6. Add environment variables:
echo    - TELEGRAM_BOT_TOKEN
echo    - SPREADSHEET_ID  
echo    - GOOGLE_CREDENTIALS_JSON
echo.

echo Step 4: Test your bot!
echo.

pause
