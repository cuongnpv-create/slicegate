"""Catalog thông báo vi ↔ en: cùng khoá, cùng tham số; dòng lệnh in đúng ngôn ngữ dự án.

Khuyết tật chặn: thêm thông báo một ngôn ngữ mà quên ngôn ngữ kia ⇒ KeyError giữa lúc chạy guard (ĐỎ giả) hoặc
người dùng tiếng Anh nhận câu tiếng Việt.
"""
from __future__ import annotations

import re
import string

import pytest

from gatekit import messages
from gatekit.cli import main
from gatekit.scaffold import init

VIET = re.compile(r"[ăâđêôơưạảấầẩẫậắằẳẵặẹẻẽếềểễệỉịọỏốồổỗộớờởỡợụủứừửữựỳỵỷỹ]", re.I)


def fields(text: str) -> set[str]:
    return {f for _, f, _, _ in string.Formatter().parse(text) if f}


def test_same_keys():
    vi, en = messages.CATALOG["vi"], messages.CATALOG["en"]
    assert set(vi) == set(en), sorted(set(vi) ^ set(en))


@pytest.mark.parametrize("key", sorted(messages.CATALOG["vi"]))
def test_same_params(key):
    assert fields(messages.CATALOG["vi"][key]) == fields(messages.CATALOG["en"][key])


def test_en_has_no_vietnamese():
    bad = {k: v for k, v in messages.CATALOG["en"].items() if VIET.search(v)}
    assert not bad, bad


def test_lang_resolution(tmp_path, monkeypatch):
    from gatekit.config import from_dict
    assert messages.lang_for(from_dict(tmp_path, {"project": {"language": "en"}})) == "en"
    assert messages.lang_for(from_dict(tmp_path, {"project": {"language": "ja"}})) == "en"
    assert messages.lang_for(from_dict(tmp_path, {"project": {"language": "ja", "docs_language": "vi"}})) == "vi"
    monkeypatch.setenv("GATEKIT_LANG", "vi")
    assert messages.lang_for(from_dict(tmp_path, {"project": {"language": "en"}})) == "vi"


def test_cli_speaks_project_language(repo, capsys):
    init(repo, name="Acme", level="standard", packs=["i18n", "postgres"], language="en")
    (repo / "src").mkdir()
    (repo / "src" / "a.py").write_text("giá = 1\nprint(api_key)\n", encoding="utf-8")
    (repo / "tests" / "test_x.py").write_text("", encoding="utf-8")
    assert main(["--root", str(repo), "check", "--full"]) == 1
    assert main(["--root", str(repo), "report"]) == 0
    assert main(["--root", str(repo), "debt"]) == 0
    out = capsys.readouterr().out
    assert "non-ASCII identifier `giá`" in out and "nothing runs it" in out and "secret has a way out" in out
    assert "OPEN conditions" in out
    leaked = [ln for ln in out.splitlines() if VIET.search(ln) and "giá" not in ln]
    assert not leaked, leaked


def test_cli_init_message_follows_flag(repo, capsys):
    assert main(["--root", str(repo), "init", "--name", "X", "--language", "en", "--level", "lite"]) == 0
    assert "new files" in capsys.readouterr().out


def test_env_override(repo, capsys, monkeypatch):
    init(repo, name="Acme", level="lite", packs=[], language="en")
    monkeypatch.setenv("GATEKIT_LANG", "vi")
    main(["--root", str(repo), "report", "--brief"])
    assert "điều kiện OPEN" in capsys.readouterr().out
