import pytest

from clutch_x.api import run


def test_api_runner_uses_platform_port(monkeypatch) -> None:
    called = {}

    def fake_run(app, *, host, port):
        called.update(app=app, host=host, port=port)

    monkeypatch.setenv("PORT", "9000")
    monkeypatch.setattr(run.uvicorn, "run", fake_run)

    run.main()

    assert called == {
        "app": "clutch_x.api.main:app",
        "host": "0.0.0.0",
        "port": 9000,
    }


@pytest.mark.parametrize("value", ["not-a-port", "0", "65536"])
def test_api_runner_rejects_invalid_port(monkeypatch, value: str) -> None:
    monkeypatch.setenv("PORT", value)

    with pytest.raises(ValueError):
        run.main()
