#!/bin/bash

# Secure Telegram Bot Deployment Script
# Usage: ./deploy.sh dev|prod
# NO SENSITIVE DATA IN THIS SCRIPT - All config from external files

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

print_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }

# Fixed configuration (non-sensitive)
PROJECT_ID="promising-node-469902-m2"
REGION="us-central1"
# Default production service name
SERVICE_NAME="telegram-bot-agency"
# Default dev service name (used when deploying dev)
DEV_SERVICE_NAME="telegram-bot-dev"

# Check argument
if [ $# -ne 1 ] || ([ "$1" != "dev" ] && [ "$1" != "prod" ]); then
    print_error "Usage: $0 [dev|prod]"
    echo ""
    echo "Examples:"
    echo "  $0 dev   # Deploy with dev bot token and dev sheets"
    echo "  $0 prod  # Deploy with prod bot token and prod sheets"
    echo ""
    echo "Required files:"
    echo "  dev:  dev_config.env + telegram_dev_token.txt"
    echo "  prod: prod_setup/prod_config.env + prod_setup/telegram_prod_token.txt"
    exit 1
fi

ENVIRONMENT=$1

print_info "🚀 Deploying $ENVIRONMENT environment to Google Cloud Run..."

# Set environment-specific configurations
if [ "$ENVIRONMENT" == "dev" ]; then
    print_info "📋 Using DEVELOPMENT configuration..."
    
    # Load dev configuration from external file
    if [ ! -f "dev_config.env" ]; then
        print_error "Development config file not found: dev_config.env"
        print_info "Create it from template: cp dev_config.env.template dev_config.env"
        print_info "Then edit dev_config.env with your actual values"
        exit 1
    fi
    
    source "dev_config.env"

    # Allow dev_config.env to override project/region and optionally service name
    PROJECT_ID="${DEV_PROJECT_ID:-$PROJECT_ID}"
    REGION="${DEV_REGION:-$REGION}"
    SERVICE_NAME="${DEV_SERVICE_NAME}"

    SPREADSHEET_ID="$DEV_SPREADSHEET_ID"
    LOGS_SPREADSHEET_ID="$DEV_LOGS_SPREADSHEET_ID"
    AUTHORIZED_USERS="$DEV_AUTHORIZED_USERS"

    # Dev token file
    BOT_TOKEN_FILE="telegram_dev_token.txt"
    SECRET_NAME="telegram-bot-token-dev"
    
else
    print_info "📋 Using PRODUCTION configuration..."
    
    # Load production configuration from external file
    if [ ! -f "prod_setup/prod_config.env" ]; then
        print_error "Production config file not found: prod_setup/prod_config.env"
        print_info "Create it from template: cp prod_setup/prod_config.env.template prod_setup/prod_config.env"
        print_info "Then edit prod_config.env with your actual production values"
        exit 1
    fi
    
    source "prod_setup/prod_config.env"
    
    SPREADSHEET_ID="$PROD_SPREADSHEET_ID"
    LOGS_SPREADSHEET_ID="$PROD_LOGS_SPREADSHEET_ID"
    AUTHORIZED_USERS="$PROD_AUTHORIZED_USERS"
    
    # Prod token file
    BOT_TOKEN_FILE="prod_setup/telegram_prod_token.txt"
    SECRET_NAME="telegram-bot-token"
fi

# Validate that configuration was loaded
if [ -z "$SPREADSHEET_ID" ] || [ -z "$LOGS_SPREADSHEET_ID" ] || [ -z "$AUTHORIZED_USERS" ]; then
    print_error "Configuration incomplete. Check your config file:"
    echo "SPREADSHEET_ID: ${SPREADSHEET_ID:-MISSING}"
    echo "LOGS_SPREADSHEET_ID: ${LOGS_SPREADSHEET_ID:-MISSING}"
    echo "AUTHORIZED_USERS: ${AUTHORIZED_USERS:-MISSING}"
    exit 1
fi

print_info "📄 Bot token file: $BOT_TOKEN_FILE"
print_info "📊 Spreadsheet ID: $SPREADSHEET_ID"
print_info "📝 Logs sheet ID: $LOGS_SPREADSHEET_ID"
print_info "👥 Authorized users: $AUTHORIZED_USERS"

# Check if bot token file exists
if [ ! -f "$BOT_TOKEN_FILE" ]; then
    print_error "Bot token file not found: $BOT_TOKEN_FILE"
    
    if [ "$ENVIRONMENT" == "prod" ]; then
        print_info "Create the file: prod_setup/telegram_prod_token.txt"
        print_info "And add your production bot token from @BotFather"
    else
        print_info "Create the file: telegram_dev_token.txt"
        print_info "And add your development bot token from @BotFather"
    fi
    exit 1
fi

# Validate bot token format (basic check)
BOT_TOKEN=$(cat "$BOT_TOKEN_FILE" | tr -d '\n\r')
if [[ ! "$BOT_TOKEN" =~ ^[0-9]+:[A-Za-z0-9_-]{35}$ ]]; then
    print_warning "Bot token format looks unusual. Make sure it's correct."
fi

# Update Secret Manager with the bot token
print_info "🔐 Updating bot token in Secret Manager..."

if gcloud secrets describe "$SECRET_NAME" --project="$PROJECT_ID" >/dev/null 2>&1; then
    print_info "Updating existing secret: $SECRET_NAME"
    gcloud secrets versions add "$SECRET_NAME" --data-file="$BOT_TOKEN_FILE" --project="$PROJECT_ID" --quiet
else
    print_info "Creating new secret: $SECRET_NAME"
    gcloud secrets create "$SECRET_NAME" --data-file="$BOT_TOKEN_FILE" --project="$PROJECT_ID" --quiet
fi

print_success "Bot token updated in Secret Manager"

# Deploy to Cloud Run
print_info "🚀 Deploying to Cloud Run..."
# Deploy to Cloud Run. We intentionally omit --allow-unauthenticated so the
# service is private and requires authentication to invoke.
gcloud run deploy "$SERVICE_NAME" --source . --project="$PROJECT_ID" --region="$REGION" --min-instances=1 --no-cpu-throttling --memory=512Mi --cpu=1000m --timeout=300 --set-env-vars="GCP_PROJECT_ID=$PROJECT_ID,SPREADSHEET_ID=$SPREADSHEET_ID,LOGS_SPREADSHEET_ID=$LOGS_SPREADSHEET_ID,AUTHORIZED_USERS=$AUTHORIZED_USERS" --quiet

# Get service URL and test
SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" --project="$PROJECT_ID" --region="$REGION" --format="value(status.url)")

print_success "🎉 Deployment completed!"
print_info "🌐 Service URL: $SERVICE_URL"

print_info "📌 Deployed service name: $SERVICE_NAME"

# Test the deployment
print_info "🏥 Testing health check..."
sleep 3

if HEALTH=$(curl -s "$SERVICE_URL/health" 2>/dev/null); then
    print_success "Health check passed!"
    echo "$HEALTH" | grep -q '"status":"running"' && print_success "Bot is running!"
    echo "$HEALTH" | grep -o '"total_clients":[0-9]*' | sed 's/"total_clients":/📊 Total clients: /'
else
    print_warning "Health check failed, but deployment completed"
fi

echo ""
print_success "✨ $ENVIRONMENT deployment complete!"

if [ "$ENVIRONMENT" == "prod" ]; then
    print_warning "🚨 PRODUCTION bot is now live!"
    print_info "Monitor logs: gcloud run services logs read $SERVICE_NAME --region=$REGION --project=$PROJECT_ID"
else
    print_info "💡 Safe to test your development bot now"
fi