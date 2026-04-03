# WhatsApp Migration Status

Date: 2026-04-02

This document records the work completed to move the WhatsApp agent stack from Twilio to Meta WhatsApp Cloud API, plus the remaining steps needed to finish go-live.

## What We Changed In The Repo

- Refactored `whatsapp-bot` from Twilio webhook handling to Meta WhatsApp Cloud API.
- Added `whatsapp-bot/app/meta_client.py` to send outbound WhatsApp replies through Graph API.
- Updated `whatsapp-bot/app/main.py` to:
  - accept Meta webhook verification
  - validate `X-Hub-Signature-256` when `WHATSAPP_APP_SECRET` is configured
  - process Meta inbound message payloads
  - route replies through the Meta client
- Updated `whatsapp-bot/app/config.py` to load Meta WhatsApp settings from environment variables.
- Updated `whatsapp-bot/app/businesses.py` to use the real Meta phone number mapping.
- Replaced webhook tests with Meta payload tests in `whatsapp-bot/tests/test_webhook.py`.
- Removed the Twilio runtime dependency from `whatsapp-bot/requirements.txt`.
- Archived the old Twilio transport layer under `whatsapp-bot/archive/twilio/`.
- Added `whatsapp-bot/.env.example` for the Meta-based runtime.

## What We Verified

- The Meta WhatsApp Cloud API token in n8n is valid and has the required scopes:
  - `whatsapp_business_management`
  - `whatsapp_business_messaging`
  - `whatsapp_business_manage_events`
- The live n8n workflow `whatsapp` was updated to the Meta WhatsApp path and published.
- The n8n instance on the VPS was upgraded and restarted successfully.
- The Meta webhook callback URL is configured in the dashboard.
- The WhatsApp Business Account was successfully subscribed to the app via:
  - `POST /v24.0/2096890844395384/subscribed_apps`
- The new Astro-based marketing site and privacy-policy routes were deployed to the VPS behind Traefik.

## IDs And URLs We Confirmed

- Meta App ID: `1261089452534033`
- WhatsApp Business Account ID: `2096890844395384`
- WhatsApp Phone Number ID: `926644930535185`
- Business phone: `+52 81 4821 7361`
- n8n webhook callback URL:
  - `https://n8n.srv1175749.hstgr.cloud/webhook/a3e592a2-ecdd-4f72-bb56-b1af1479a926/webhook`
- Verify token used in Meta:
  - `mi_verify_token_2026`
- Canonical privacy policy URL:
  - `https://blueskytravelmx.com/privacy-policy`

## Current State

- The app is still in Meta Development mode.
- Meta will only deliver production WhatsApp data when the app is switched to Live.
- The new website is running on the VPS, but public DNS for `blueskytravelmx.com` still points to the old provider.
- n8n has one WhatsApp trigger per Meta app limitation, so the same app cannot host multiple WhatsApp triggers at once.
- The current workflow is active in n8n; if the trigger is not firing, the problem is usually app mode, webhook state, or app/webhook reuse rather than the bot logic itself.

## Checklist To Finish Go-Live

1. Replace the legal placeholders in `site/src/config/site.ts` with the final legal entity and address.
2. Point `blueskytravelmx.com` DNS to `72.60.228.135`.
3. Confirm `https://blueskytravelmx.com/privacy-policy` returns `200` publicly.
4. Add that public URL in **Meta Developers -> App Settings -> Basic**.
5. Switch the Meta app from **Development** to **Live**.
6. Confirm the WhatsApp workflow in n8n stays active after the app switch.
7. Send a real WhatsApp message to the business number and verify the execution appears in n8n.
8. If Meta or n8n reports an existing webhook subscription conflict, remove the old subscription before re-registering the trigger.
9. Keep the Meta access token current and rotate it before it expires.
10. After the first end-to-end test, document the exact runtime health check and incident response steps for future maintenance.

## Notes

- Do not store access tokens or secrets in this document.
- If the team wants to re-enable Twilio later, the archived transport is available in `whatsapp-bot/archive/twilio/`.
