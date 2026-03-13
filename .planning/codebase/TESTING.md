# Testing Patterns

**Analysis Date:** 2026-03-13

## Test Framework

**Runner:**
- pytest (version inferred from `.pytest_cache/` containing `pytest-9.0.2` in compiled filename)
- No `pytest.ini`, `setup.cfg`, or `pyproject.toml` config found — pytest runs with defaults
- `pytest-asyncio` used for async test support

**Assertion Library:**
- Built-in `assert` statements (pytest assertion rewriting)

**Run Commands:**
```bash
python -m pytest tests/          # Run all tests
python -m pytest tests/ -v       # Verbose output
python -m pytest tests/ -k "test_name"   # Run specific test by name
```

## Test File Organization

**Location:**
- All tests in a top-level `tests/` directory (separate from source)
- Source is in project root: `bot_telegram_polling.py`, `main.py`

**Naming:**
- Files: `test_<feature>.py`
- Functions: `test_<what_is_being_tested>()`
- No test classes used — all tests are plain functions

**Structure:**
```
tests/
├── test_index_manager.py    # GoogleSheetsManager index/retry tests
├── test_message_parsing.py  # TelegramBot message parsing and mention detection
└── test_webhook.py          # Live integration script (sends HTTP to local server)
```

**Note:** `tests/test_webhook.py` is not a pytest test — it is a manual integration script that POSTs to a running local server using `requests`. It contains no `assert` statements and no test functions.

## Test Structure

**Suite Organization:**
```python
# test_index_manager.py — no class wrapping, standalone test functions
def test_execute_with_retry_recovers_from_broken_pipe():
    values = DummyValuesApi({})
    manager = build_manager_for_tests(values)
    req = DummyRequest(payload={"ok": True}, failures=2)
    result = manager._execute_with_retry(req, "test op")
    assert result == {"ok": True}
    assert req.calls == 3
```

```python
# test_message_parsing.py — async test functions with @pytest.mark.asyncio
@pytest.mark.asyncio
async def test_extract_client_number():
    tb = build_test_bot()
    assert tb._extract_client_number('cliente 12345') == '12345'
    assert tb._extract_client_number('no digits') == ''
```

**Patterns:**
- Setup via factory functions, not fixtures: `build_manager_for_tests()` and `build_test_bot()` construct pre-wired instances
- No `setUp`/`tearDown` — each test is fully self-contained
- No `conftest.py` found — no shared fixtures registered
- Assertions use plain `assert` (no helper wrappers)

## Mocking

**Framework:** Manual stub objects (no `unittest.mock`, no `pytest-mock` detected)

**Pattern — Dummy API stubs:**
```python
class DummyRequest:
    def __init__(self, payload=None, failures=0, error_factory=None):
        self.payload = payload if payload is not None else {}
        self.failures = failures
        self.calls = 0
        self.error_factory = error_factory or (lambda: BrokenPipeError("broken pipe"))

    def execute(self):
        self.calls += 1
        if self.calls <= self.failures:
            raise self.error_factory()
        return self.payload

class DummyValuesApi:
    def __init__(self, responses):
        self.responses = responses
        self.calls = []

    def get(self, spreadsheetId, range):
        self.calls.append((spreadsheetId, range))
        req = self.responses.get(range)
        if req is None:
            req = DummyRequest(payload={"values": []})
        return req
```

**Pattern — Bypass `__init__` with `__new__` + manual attribute injection:**
```python
def build_manager_for_tests(values_api):
    manager = GoogleSheetsManager.__new__(GoogleSheetsManager)
    manager.service = DummyService(values_api)
    manager.headers = ["client phone number", "cliente", "correo", "banco"]
    manager.client_column = 0
    manager.spreadsheet_id = "sheet"
    manager.index_phone_to_row = {}
    manager.index_timestamp = time.time()
    manager.index_ttl = 1800
    manager.row_cache = {}
    manager.row_cache_size = 100
    manager.sheets_retry_attempts = 3
    manager.sheets_retry_base_delay = 0
    manager._index_lock = threading.Lock()
    manager._row_cache_lock = threading.Lock()
    manager._index_build_lock = threading.Lock()
    manager._index_warming = False
    manager._executor = DummyExecutor()
    manager._normalize_phone = lambda raw: ''.join(ch for ch in str(raw) if ch.isdigit()).lstrip('0')
    return manager
```

**Pattern — `SimpleNamespace` for lightweight Telegram objects:**
```python
from types import SimpleNamespace

class DummyUpdate:
    def __init__(self, message=None, chat_type='private'):
        self.message = message
        self.effective_chat = SimpleNamespace(id=1, type=chat_type)
        self.effective_user = SimpleNamespace(id=123, username='tester', first_name='Test')
```

**Pattern — `monkeypatch` for env vars (pytest built-in):**
```python
async def test_addressed_and_processed_text_group_direct_number_enabled(monkeypatch):
    monkeypatch.setenv('ALLOW_DIRECT_GROUP_NUMBER', 'true')
    ...
```

**What to Mock:**
- All external I/O: Google Sheets API calls (via `DummyService`, `DummyValuesApi`, `DummyRequest`)
- The `ThreadPoolExecutor` (via `DummyExecutor`) to make async background tasks synchronous in tests
- Environment variables (via `monkeypatch.setenv`)
- Bot `bot_info` via `SimpleNamespace(username='mybot', id=999)`

**What NOT to Mock:**
- Threading primitives (`threading.Lock()`) — real locks used in test instances
- The method under test itself — tests call real methods on constructed instances

## Fixtures and Factories

**Test Data:**
- No separate fixture files or factories module
- Hard-coded data inline in factory functions:
  ```python
  manager.headers = ["client phone number", "cliente", "correo", "banco"]
  manager.spreadsheet_id = "sheet"
  ```
- Phone numbers as plain strings: `"5536604547"`, `"5215536604547"`

**Location:**
- Factory functions defined at module level within each test file:
  - `build_manager_for_tests(values_api)` in `tests/test_index_manager.py`
  - `build_test_bot()` in `tests/test_message_parsing.py`

## Coverage

**Requirements:** None enforced — no coverage config or thresholds defined

**View Coverage:**
```bash
python -m pytest tests/ --cov=bot_telegram_polling --cov-report=term-missing
```
(requires `pytest-cov` to be installed — not in `requirements.txt`)

## Test Types

**Unit Tests:**
- `tests/test_index_manager.py`: Tests `GoogleSheetsManager` retry logic, index lookup with suffix fallback, and single-flight index rebuild
- `tests/test_message_parsing.py`: Tests `TelegramBot` methods for client number extraction, mention detection, and addressed-text routing

**Integration Tests:**
- None using pytest

**E2E / Manual Tests:**
- `tests/test_webhook.py`: Manual script POSTing a fake Telegram update to a local Flask server; not a pytest test

**Shell-based Tests:**
- `test_scale_to_zero.sh`: Shell script testing Cloud Run scale-to-zero behavior; not pytest

## Common Patterns

**Async Testing:**
```python
import pytest

@pytest.mark.asyncio
async def test_addressed_and_processed_text_private():
    tb = build_test_bot()
    msg = DummyMessage(text='12345')
    update = DummyUpdate(message=msg, chat_type='private')
    ctx = DummyContext()

    addressed, processed = await tb._addressed_and_processed_text(update, ctx)
    assert addressed is True
    assert processed == '12345'
```

**Single-flight / Idempotency Testing:**
```python
def test_schedule_index_rebuild_is_single_flight():
    manager = build_manager_for_tests(DummyValuesApi({}))
    build_count = {"n": 0}

    def fake_load():
        build_count["n"] += 1

    manager.load_index = fake_load
    manager._schedule_index_rebuild("first")
    manager._index_warming = True           # simulate in-flight
    manager._schedule_index_rebuild("second")

    assert build_count["n"] == 1
    assert manager._executor.submit_calls == 1
```

**Error Recovery Testing:**
```python
def test_execute_with_retry_recovers_from_broken_pipe():
    req = DummyRequest(payload={"ok": True}, failures=2)
    result = manager._execute_with_retry(req, "test op")
    assert result == {"ok": True}
    assert req.calls == 3           # failed 2 times, succeeded on 3rd
```

---

*Testing analysis: 2026-03-13*
