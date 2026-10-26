from __future__ import annotations

from gatekit.config import from_dict
from gatekit.tools import guard_hygiene
from gatekit.tools.risk_zone import classify
from gatekit.tools.slice_quota import slices, violations
from tests.conftest import commit


def test_slice_quota(repo):
    cfg = from_dict(repo, {})
    commit(repo, "feat: a [S-1]", {"src/a.py": "a=1\n"})
    commit(repo, "docs: quy trình [G-1]", {"docs/x.md": "x\n"})
    commit(repo, "docs: quy trình nữa [G-1]", {"docs/y.md": "y\n"})      # cùng lát G-1
    assert violations(cfg, slices(cfg)) == []
    commit(repo, "docs: lát quản trị thứ 2 [G-2]", {"docs/z.md": "z\n"})
    v = violations(cfg, slices(cfg))
    assert len(v) == 1 and "liền nhau" in v[0]


def test_slice_quota_empty_repo(repo):
    assert slices(from_dict(repo, {})) == []


def test_slice_quota_needs_two_code_slices(repo):
    cfg = from_dict(repo, {})
    commit(repo, "docs [G-1]", {"docs/a.md": "a\n"})
    commit(repo, "feat [S-1]", {"src/a.py": "a=1\n"})
    commit(repo, "docs [G-2]", {"docs/b.md": "b\n"})
    assert any("1/2 lát MÃ" in x for x in violations(cfg, slices(cfg)))
    commit(repo, "docs [G-3] [QUOTA-EXEMPT: owner OW-3 cho phép]", {"docs/c.md": "c\n"})
    seq = slices(cfg)
    assert seq[-1].exempt and len(violations(cfg, seq)) == 1


def test_risk_zone(repo):
    cfg = from_dict(repo, {"zones": {"T": {"paths": [r"^src/payments/"], "grep": []},
                                     "F": {"paths": [], "grep": [r"\bfee_rate\b"]}}})
    base = commit(repo, "init [S-0]", {"README.md": "x\n"})
    commit(repo, "feat [S-1]", {"src/payments/charge.py": "def charge(): pass\n", "src/auth/login.py": "x=1\n",
                                "src/pricing.py": "fee_rate = 0.01\n"})
    rep = classify(cfg, base)
    assert rep.files["T"] == ["src/payments/charge.py"]
    assert rep.files["K"] == ["src/auth/login.py"]
    assert rep.grep_hits["F"] and rep.heaviest == "T"
    assert rep.zones() == ["T", "K", "F"]


def test_risk_zone_other(repo):
    cfg = from_dict(repo, {})
    base = commit(repo, "init [S-0]", {"README.md": "x\n"})
    commit(repo, "docs [S-1]", {"docs/a.md": "a\n"})
    assert classify(cfg, base).heaviest == "khác"


def test_guard_hygiene(tmp_path):
    cfg = from_dict(tmp_path, {})
    for _ in range(3):
        guard_hygiene.record(cfg, "incident", "lặp lệnh khi mạng lỗi", "S-4", "gửi 2 lần")
    guard_hygiene.record(cfg, "guard-catch", "secret_leak", "S-5", "print(token)")
    out = guard_hygiene.report(cfg, ["secret_leak", "naming_scope"])
    assert "ĐỦ ĐIỀU KIỆN" in out and "1  secret_leak" in out and "0  naming_scope" in out
