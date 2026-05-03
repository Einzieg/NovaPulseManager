import backend.test_mvp as mvp


async def test_mvp_scheduler_can_run_without_fixture(monkeypatch):
    init_calls = []

    monkeypatch.setattr(mvp, "init_database", lambda db_path=None: init_calls.append(db_path))
    monkeypatch.setattr(mvp.DeviceConfig, "select", lambda: [])

    await mvp.test_scheduler()

    assert init_calls == [None]
