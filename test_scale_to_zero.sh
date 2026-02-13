#!/bin/bash
# Quick test to verify if bot scales to zero with polling mode

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

print_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }

PROJECT_ID="promising-node-469902-m2"
REGION="us-central1"
SERVICE_NAME="telegram-bot-dev"

print_info "🧪 Testing scale-to-zero behavior with polling mode"
echo ""

# Check if service exists
if ! gcloud run services describe "$SERVICE_NAME" --project="$PROJECT_ID" --region="$REGION" >/dev/null 2>&1; then
    print_error "Service $SERVICE_NAME not found. Deploy first with: ./deploy.sh dev"
    exit 1
fi

# Get current instance count
print_info "Checking current active instances..."
REVISION=$(gcloud run services describe "$SERVICE_NAME" \
    --project="$PROJECT_ID" \
    --region="$REGION" \
    --format="value(status.traffic[0].revisionName)")

print_info "Current revision: $REVISION"

# Check logs to see if bot is polling
print_info "Checking if bot is actively polling..."
echo ""

RECENT_LOGS=$(gcloud run services logs read "$SERVICE_NAME" \
    --project="$PROJECT_ID" \
    --region="$REGION" \
    --limit=5 2>&1)

if echo "$RECENT_LOGS" | grep -q "getUpdates"; then
    print_warning "Bot is actively polling Telegram API"
    echo "$RECENT_LOGS" | grep "getUpdates" | head -3
    echo ""
    print_error "CONCLUSION: Bot will NOT scale to zero in polling mode"
    echo ""
    echo "📊 Why? The bot makes HTTP requests every ~10 seconds, keeping the instance busy."
    echo ""
    echo "💡 Options:"
    echo "   1. Keep polling but set min-instances=1 (simple, ~\$10-15/month)"
    echo "   2. Switch to webhook mode (complex, ~\$1-3/month, true scale-to-zero)"
    echo ""
    echo "🔧 To switch to polling with min-instances=1:"
    echo "   Edit deploy.sh line 123: change --min-instances=0 to --min-instances=1"
    echo ""
    echo "🚀 To implement webhooks (recommended for scale-to-zero):"
    echo "   Run: cat SCALING_TEST_PLAN.md"
    exit 1
else
    print_success "No active polling detected"
    
    # Wait and check if instance scales down
    print_info "Waiting 5 minutes to see if instance scales down..."
    print_warning "Don't send any messages to the bot during this time!"
    
    for i in {5..1}; do
        echo -ne "\r⏰ ${i} minutes remaining...   "
        sleep 60
    done
    echo ""
    
    # Check instance count after waiting
    print_info "Checking instance count..."
    
    INSTANCES=$(gcloud run services describe "$SERVICE_NAME" \
        --project="$PROJECT_ID" \
        --region="$REGION" \
        --format="value(status.conditions)" | grep -c "True" || echo "0")
    
    if [ "$INSTANCES" -gt 0 ]; then
        print_error "Instance is still running (did not scale to zero)"
        print_warning "Recommendation: Keep min-instances=1 or switch to webhooks"
    else
        print_success "Instance scaled to zero! ✨"
        print_success "Scale-to-zero is working correctly"
    fi
fi

echo ""
print_info "Test complete. Check SCALING_TEST_PLAN.md for detailed analysis."
