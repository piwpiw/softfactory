import subprocess
from urllib.error import URLError
from pathlib import Path

from scripts import verify_integration


def test_is_server_ready_accepts_api_health():
    calls = []

    def fake_urlopen(url, timeout=2):
        raw_url = getattr(url, "full_url", url)
        calls.append(raw_url)
        if raw_url.endswith("/api/health"):
            return object()
        if raw_url.endswith("/health"):
            raise URLError("not ready")
        raise AssertionError(f"unexpected url: {url}")

    assert verify_integration._is_server_ready("http://localhost:8000", opener=fake_urlopen) is True
    assert calls[:2] == [
        "http://localhost:8000/health",
        "http://localhost:8000/api/health",
    ]


def test_start_server_uses_start_server_entrypoint(monkeypatch):
    captured = {}

    class DummyProcess:
        pass

    def fake_popen(cmd, cwd=None, env=None, stdout=None, stderr=None, text=None):
        captured["cmd"] = cmd
        captured["cwd"] = cwd
        captured["env"] = env
        captured["stdout"] = stdout
        captured["stderr"] = stderr
        captured["text"] = text
        return DummyProcess()

    monkeypatch.setattr(subprocess, "Popen", fake_popen)

    proc = verify_integration.start_server(8123)

    assert isinstance(proc, DummyProcess)
    assert captured["cmd"][1] == "start_server.py"
    assert captured["env"]["DEBUG"] == "false"
    assert captured["env"]["FLASK_ENV"] == "development"
    assert captured["env"]["ENVIRONMENT"] == "development"
    assert isinstance(captured["stdout"].name, str)
    assert Path(captured["stdout"].name).name == "verify_integration_server_8123.log"
    assert captured["stderr"] == captured["stdout"]
    assert captured["text"] is True
    captured["stdout"].close()
