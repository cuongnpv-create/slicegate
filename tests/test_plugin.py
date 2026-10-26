"""Gói plugin Claude Code: manifest, marketplace, skill, lệnh bin/slicegate, hook.

Khuyết tật chặn: phát hành plugin mà manifest lệch phiên bản / tên với marketplace (cài báo "not found"), skill thiếu
mô tả (Claude không biết khi nào dùng), lệnh `slicegate` của plugin không chạy được khi không pip install, git hook
không tìm thấy slicegate ngoài Claude Code (commit lọt qua cổng hoặc bị chặn oan).
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from slicegate import __version__

ROOT = Path(__file__).resolve().parents[1]
BIN = ROOT / "bin" / "slicegate"
HOOK = ROOT / "hooks" / "session_start.sh"
CLEAN_PATH = "/usr/bin:/bin"


def run(cmd, cwd, env_extra=None, path=CLEAN_PATH):
    env = {"PATH": path, "HOME": os.environ.get("HOME", "/tmp"), "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@e",
           "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@e"}
    env.update(env_extra or {})
    return subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True)


def test_manifests_agree():
    plugin = json.loads((ROOT / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))
    market = json.loads((ROOT / ".claude-plugin/marketplace.json").read_text(encoding="utf-8"))
    assert plugin["name"] == "slicegate" and plugin["version"] == __version__
    entry = next(p for p in market["plugins"] if p["name"] == plugin["name"])
    assert entry["source"] == "./" and entry["version"] == __version__
    assert market["owner"]["name"]
    assert (ROOT / ".claude-plugin/icon.png").read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"


@pytest.mark.parametrize("skill", sorted(p.name for p in (ROOT / "skills").iterdir()))
def test_skill_frontmatter(skill):
    text = (ROOT / "skills" / skill / "SKILL.md").read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    assert m, "thiếu frontmatter"
    meta = dict(line.split(":", 1) for line in m.group(1).splitlines() if ":" in line)
    assert meta["name"].strip() == skill
    assert len(meta["description"].strip()) > 40


def test_hooks_json_points_to_existing_script():
    data = json.loads((ROOT / "hooks/hooks.json").read_text(encoding="utf-8"))
    cmd = data["hooks"]["SessionStart"][0]["hooks"][0]["command"]
    rel = cmd.replace('"', "").replace("${CLAUDE_PLUGIN_ROOT}/", "")
    assert (ROOT / rel).is_file() and os.access(ROOT / rel, os.X_OK)


def test_bin_runs_without_install(tmp_path):
    r = run([sys.executable, str(BIN), "--version"], tmp_path)
    assert r.returncode == 0 and __version__ in r.stdout


def test_plugin_session_hook(repo):
    env = {"CLAUDE_PLUGIN_ROOT": str(ROOT), "CLAUDE_PROJECT_DIR": str(repo)}
    r = run([str(HOOK)], repo, env)
    assert r.returncode == 0 and r.stdout == "", "dự án chưa cài slicegate ⇒ im lặng"
    run([sys.executable, str(BIN), "init", "--name", "Demo", "--language", "en", "--level", "lite"], repo)
    r = run([str(HOOK)], repo, env)
    assert r.returncode == 0 and "OPEN conditions" in r.stdout


def test_git_hook_finds_plugin_slicegate(repo, tmp_path):
    """Ngoài Claude Code: không có `slicegate` trên PATH, python3 không import được slicegate ⇒ hook dùng SLICEGATE_BIN."""
    run([sys.executable, str(BIN), "init", "--name", "Demo", "--language", "en", "--level", "lite"], repo)
    r = run([sys.executable, str(BIN), "hooks", "install"], repo, {"SLICEGATE_ENTRY": str(BIN)})
    assert r.returncode == 0
    assert f'SLICEGATE_BIN="${{SLICEGATE_BIN:-{BIN}}}"' in (repo / ".git/hooks/pre-commit").read_text(encoding="utf-8")
    fake = tmp_path / "fakebin"
    fake.mkdir()
    # python3 giả: chỉ chạy được bin/slicegate (qua sys.executable thật), ⛔ import slicegate từ site-packages
    (fake / "python3").write_text(f'#!/bin/sh\nif [ "$1" = "-c" ]; then exit 1; fi\nexec {sys.executable} "$@"\n')
    (fake / "python3").chmod(0o755)
    path = f"{fake}:{CLEAN_PATH}"
    assert shutil.which("slicegate", path=path) is None
    run(["git", "add", "-A"], repo, path=path)
    assert run(["git", "commit", "-qm", "init [G-1]"], repo, path=path).returncode == 0
    (repo / "src").mkdir()
    (repo / "src/a.py").write_text("tên = 1\n", encoding="utf-8")
    run(["git", "add", "-A"], repo, path=path)
    r = run(["git", "commit", "-qm", "x [S-1]"], repo, path=path)
    assert r.returncode != 0 and "naming_scope" in r.stdout + r.stderr


@pytest.mark.skipif(shutil.which("claude") is None, reason="không có Claude Code CLI")
def test_claude_plugin_validate():
    r = subprocess.run(["claude", "plugin", "validate", str(ROOT)], capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, r.stdout + r.stderr
