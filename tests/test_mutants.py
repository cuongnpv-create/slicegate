from __future__ import annotations

import sys

import pytest

from slicegate.cli import main
from slicegate.config import from_dict
from slicegate.qa import mutants as mq
from tests.conftest import commit, write

APP = "def can_withdraw(balance, amount):\n    if amount <= 0:\n        return False\n    return amount <= balance\n"
GOOD_TEST = ("from app import can_withdraw\n"
             "assert can_withdraw(10, 5)\n"
             "assert not can_withdraw(10, 50)\n"
             "assert not can_withdraw(10, -1)\n")
WEAK_TEST = "from app import can_withdraw\nassert can_withdraw(10, 5)\n"


def suite(cmd: str) -> str:
    return f'''zone = "T"
cmd = "{cmd}"

[[mutant]]
id = "wd-01"
file = "app.py"
find = "return amount <= balance"
replace = "return True"
why = "bỏ kiểm số dư ⇒ rút quá số dư"

[[mutant]]
id = "wd-02"
file = "app.py"
find = "if amount <= 0:"
replace = "if False:"
why = "bỏ chặn số tiền âm"
'''


def setup(root, test_body):
    write(root, "app.py", APP)
    write(root, "check_app.py", test_body)
    write(root, "mutants/withdraw.toml", suite(f"{sys.executable} check_app.py"))
    return from_dict(root, {})


def test_strong_test_kills_all(tmp_path):
    cfg = setup(tmp_path, GOOD_TEST)
    res = mq.run(cfg, mq.select(mq.load_suites(cfg), None), log=lambda *a: None)
    assert [r.status for r in res] == ["KILLED", "KILLED"]
    assert (tmp_path / "app.py").read_text(encoding="utf-8") == APP, "checkout thật không được đụng"


def test_weak_test_survives(tmp_path):
    cfg = setup(tmp_path, WEAK_TEST)
    res = mq.run(cfg, mq.select(mq.load_suites(cfg), None), log=lambda *a: None)
    assert {r.status for r in res} == {"SURVIVED"}


def test_red_baseline_refused(tmp_path):
    cfg = setup(tmp_path, "raise SystemExit(1)\n")
    with pytest.raises(RuntimeError):
        mq.run(cfg, mq.select(mq.load_suites(cfg), None), log=lambda *a: None)


def test_anchors(tmp_path):
    cfg = setup(tmp_path, GOOD_TEST)
    assert mq.anchor_problems(cfg) == []
    write(tmp_path, "app.py", APP.replace("return amount <= balance", "return balance >= amount"))
    probs = mq.anchor_problems(cfg)
    assert len(probs) == 1 and "wd-01" in probs[0]


def test_select(tmp_path):
    cfg = setup(tmp_path, GOOD_TEST)
    suites = mq.load_suites(cfg)
    assert mq.select(suites, ["docs/x.md"]) == []
    assert len(mq.select(suites, ["app.py"])) == 2
    assert len(mq.select(suites, ["mutants/withdraw.toml"])) == 2
    assert [m.id for m in mq.select(suites, None, only=["wd-02"])] == ["wd-02"]
    with pytest.raises(ValueError):
        mq.select(suites, None, only=["nope"])


def test_cli_zone_requires_permanent_suite_for_T(repo):
    write(repo, "slicegate.toml", '[zones.T]\npaths = ["^app\\\\.py$"]\ngrep = []\n')
    base = commit(repo, "init [S-0]", {"README.md": "x\n"})
    commit(repo, "feat [S-1]", {"app.py": APP})
    assert main(["--root", str(repo), "zone", "--base", base]) == 1      # chưa có bộ đột biến
    commit(repo, "test [S-1]", {"check_app.py": GOOD_TEST,
                                 "mutants/withdraw.toml": suite(f"{sys.executable} check_app.py")})
    assert main(["--root", str(repo), "zone", "--base", base]) == 0
    assert main(["--root", str(repo), "mutants", "run"]) == 0
