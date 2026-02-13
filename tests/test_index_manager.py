import threading
import time

from bot_telegram_polling import GoogleSheetsManager


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


class DummySheetsApi:
    def __init__(self, values_api):
        self._values_api = values_api

    def values(self):
        return self._values_api


class DummyService:
    def __init__(self, values_api):
        self._values_api = values_api

    def spreadsheets(self):
        return DummySheetsApi(self._values_api)


class DummyExecutor:
    def __init__(self):
        self.submit_calls = 0

    def submit(self, fn, *args, **kwargs):
        self.submit_calls += 1
        result_value = fn(*args, **kwargs)

        class _F:
            def result(self_inner):
                return result_value

        return _F()


def build_manager_for_tests(values_api):
    manager = GoogleSheetsManager.__new__(GoogleSheetsManager)
    manager.service = DummyService(values_api)
    manager.headers = ["client phone number", "cliente", "correo", "other info"]
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


def test_execute_with_retry_recovers_from_broken_pipe():
    values = DummyValuesApi({})
    manager = build_manager_for_tests(values)

    req = DummyRequest(payload={"ok": True}, failures=2)
    result = manager._execute_with_retry(req, "test op")

    assert result == {"ok": True}
    assert req.calls == 3


def test_suffix_fallback_returns_row_data_without_rebuild():
    values = DummyValuesApi(
        {
            "Sheet1!A123:D123": DummyRequest(
                payload={
                    "values": [["5215536604547", "MORALES", "", ""]]
                }
            )
        }
    )
    manager = build_manager_for_tests(values)
    manager.index_phone_to_row = {"5215536604547": 123}

    data = manager.get_client_data("5536604547")

    assert data is not None
    assert data["cliente"] == "MORALES"
    assert manager._executor.submit_calls == 0


def test_schedule_index_rebuild_is_single_flight():
    values = DummyValuesApi({})
    manager = build_manager_for_tests(values)

    build_count = {"n": 0}

    def fake_load():
        build_count["n"] += 1

    manager.load_index = fake_load

    manager._schedule_index_rebuild("first")
    # Simulate in-flight rebuild window
    manager._index_warming = True
    manager._schedule_index_rebuild("second")

    assert build_count["n"] == 1
    assert manager._executor.submit_calls == 1
