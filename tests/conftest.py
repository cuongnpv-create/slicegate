from __future__ import annotations

import subprocess
from pathlib import Path

import pytest


def sh(root: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True, text=True).stdout


def write(root: Path, rel: str, body: str) -> None:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body, encoding="utf-8")


def commit(root: Path, msg: str, files: dict[str, str]) -> str:
    for rel, body in files.items():
        write(root, rel, body)
    sh(root, "add", "-A")
    sh(root, "commit", "-q", "-m", msg)
    return sh(root, "rev-parse", "HEAD").strip()


@pytest.fixture(autouse=True)
def _reset_lang(monkeypatch):
    """Ngôn ngữ thông báo là trạng thái toàn tiến trình — mỗi test bắt đầu ở `vi`, ⛔ rò sang test sau."""
    from gatekit import messages
    monkeypatch.delenv("GATEKIT_LANG", raising=False)
    messages.set_lang("vi")
    yield
    messages.set_lang("vi")


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    sh(tmp_path, "init", "-q", "-b", "main")
    sh(tmp_path, "config", "user.email", "t@example.com")
    sh(tmp_path, "config", "user.name", "t")
    sh(tmp_path, "config", "commit.gpgsign", "false")
    return tmp_path
