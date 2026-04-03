# Twilio Archive

This folder preserves the pre-Meta transport layer for the WhatsApp bot.

Status:
- Archived for reference only
- Not imported by the active app
- Snapshot source: git `HEAD` before the Meta Cloud API refactor on 2026-03-25

What is preserved:
- `app/main.py`: Twilio webhook entrypoint with signature validation and TwiML replies
- `app/config.py`: Twilio-related settings
- `app/businesses.py`: sender mapping keyed by Twilio WhatsApp numbers
- `tests/test_webhook.py`: Twilio webhook tests
- `requirements.txt`: includes the `twilio` dependency used by the archived transport

Twilio-specific env vars used by this snapshot:
- `TWILIO_AUTH_TOKEN`
- `TWILIO_ACCOUNT_SID`
- `WEBHOOK_BASE_URL`
- `GEMINI_API_KEY`

Notes:
- The active app now uses Meta WhatsApp Cloud API instead.
- If we ever restore this path, we should copy the archived files back into `whatsapp-bot/app/` and `whatsapp-bot/tests/`, then restore the `twilio` dependency.
