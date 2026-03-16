---
phase: 2
slug: whatsapp-bot-platform
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-16
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | `whatsapp-bot/pytest.ini` — Wave 0 creates |
| **Quick run command** | `pytest whatsapp-bot/tests/ -x -q` |
| **Full suite command** | `pytest whatsapp-bot/tests/ -v` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest whatsapp-bot/tests/ -x -q`
- **After every plan wave:** Run `pytest whatsapp-bot/tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 02-01-01 | 01 | 1 | INFRA-05 | smoke | `pytest whatsapp-bot/tests/test_health.py -x` | ❌ W0 | ⬜ pending |
| 02-01-02 | 01 | 1 | BOT-01 | unit | `pytest whatsapp-bot/tests/test_webhook.py::test_signature_valid -x` | ❌ W0 | ⬜ pending |
| 02-01-03 | 01 | 1 | BOT-01 | unit | `pytest whatsapp-bot/tests/test_webhook.py::test_url_reconstruction -x` | ❌ W0 | ⬜ pending |
| 02-01-04 | 01 | 1 | BOT-02 | integration | `pytest whatsapp-bot/tests/test_gemini.py::test_spanish_response -x` | ❌ W0 | ⬜ pending |
| 02-01-05 | 01 | 1 | BOT-03 | unit | `pytest whatsapp-bot/tests/test_sheets.py::test_product_search -x` | ❌ W0 | ⬜ pending |
| 02-01-06 | 01 | 1 | BOT-04 | unit | `pytest whatsapp-bot/tests/test_handlers.py::test_product_handler_output -x` | ❌ W0 | ⬜ pending |
| 02-02-01 | 02 | 1 | PLAT-01 | unit | `pytest whatsapp-bot/tests/test_config.py::test_business_lookup -x` | ❌ W0 | ⬜ pending |
| 02-02-02 | 02 | 1 | PLAT-02 | unit | `pytest whatsapp-bot/tests/test_dispatcher.py::test_handler_routing -x` | ❌ W0 | ⬜ pending |
| 02-02-03 | 02 | 1 | PLAT-03 | unit | `pytest whatsapp-bot/tests/test_session_store.py::test_session_isolation -x` | ❌ W0 | ⬜ pending |
| 02-02-04 | 02 | 1 | PLAT-03 | unit | `pytest whatsapp-bot/tests/test_session_store.py::test_session_expiry -x` | ❌ W0 | ⬜ pending |
| 02-02-05 | 02 | 1 | PLAT-04 | unit | `pytest whatsapp-bot/tests/test_config.py::test_new_business_no_code_change -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `whatsapp-bot/tests/test_health.py` — stubs for INFRA-05
- [ ] `whatsapp-bot/tests/test_webhook.py` — stubs for BOT-01 (signature validation, URL reconstruction)
- [ ] `whatsapp-bot/tests/test_gemini.py` — stubs for BOT-02 (Gemini Spanish response)
- [ ] `whatsapp-bot/tests/test_sheets.py` — stubs for BOT-03 (product search)
- [ ] `whatsapp-bot/tests/test_handlers.py` — stubs for BOT-04, PLAT-02
- [ ] `whatsapp-bot/tests/test_config.py` — stubs for PLAT-01, PLAT-04
- [ ] `whatsapp-bot/tests/test_session_store.py` — stubs for PLAT-03
- [ ] `whatsapp-bot/tests/test_dispatcher.py` — stubs for PLAT-02
- [ ] `whatsapp-bot/pytest.ini` — basic config
- [ ] Framework install: `pip install pytest pytest-asyncio`

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| WhatsApp message receives AI response within 10s | BOT-02 | Requires live Twilio + Gemini | Send message to Twilio sandbox number, time response |
| Bot restarts after crash/VPS reboot | INFRA-05 | Requires Docker restart policy on VPS | `docker kill whatsapp-bot`, verify auto-restart |
| Two simultaneous customers get isolated responses | PLAT-03 | End-to-end concurrency test | Send messages from two phones simultaneously |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
