"""Guard `migration_scope` (gói postgres) — migration đã áp ⛔ bị sửa; chuỗi số ⛔ đứt/trùng; migration mới phải ghim.

Tệp khoá (`lock_file`): mỗi dòng `<tên tệp> <sha256>`. ĐỎ khi:
  · tệp đã ghim mà sha lệch (sửa byte migration đã chạy ở môi trường thật — mỗi nơi một schema khác nhau);
  · tệp migration chưa ghim (chạy `slicegate migrations lock` sau khi gate duyệt);
  · dòng khoá trỏ tệp đã xoá;
  · số thứ tự trùng hoặc đứt quãng (hai làn song song cùng lấy một số).
"""
from __future__ import annotations

import hashlib
import re

from slicegate.config import Config
from slicegate.guards._common import Finding, expect, fixture
from slicegate.messages import t

NAME = "migration_scope"
PACK = "postgres"
FAST = True
DEFECT = {"vi": "migration đã áp bị sửa ⇒ schema các môi trường lệch nhau; hai lát song song trùng số migration",
          "en": "an applied migration is edited ⇒ environments drift apart; two parallel slices take the same migration number"}


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def migrations(cfg: Config) -> dict[str, str]:
    spec = cfg.pack("postgres")
    d = cfg.root / spec["migrations_dir"]
    pat = re.compile(spec["pattern"])
    if not d.is_dir():
        return {}
    return {p.name: _sha(p.read_bytes()) for p in sorted(d.iterdir()) if p.is_file() and pat.match(p.name)}


def read_lock(cfg: Config) -> dict[str, str]:
    p = cfg.root / cfg.pack("postgres")["lock_file"]
    if not p.exists():
        return {}
    out = {}
    for ln in p.read_text(encoding="utf-8").splitlines():
        if ln.strip() and not ln.startswith("#"):
            name, sha = ln.split()
            out[name] = sha
    return out


def write_lock(cfg: Config) -> list[str]:
    """Ghim tệp MỚI; ⛔ ghi đè sha của tệp đã ghim (sửa migration cũ phải qua gate, sửa tay tệp khoá)."""
    lock, cur = read_lock(cfg), migrations(cfg)
    added = [n for n in cur if n not in lock]
    lock.update({n: cur[n] for n in added})
    p = cfg.root / cfg.pack("postgres")["lock_file"]
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("".join(f"{n} {s}\n" for n, s in sorted(lock.items())), encoding="utf-8")
    return added


def check(cfg: Config) -> list[Finding]:
    spec = cfg.pack("postgres")
    lock_rel = spec["lock_file"]
    cur, lock = migrations(cfg), read_lock(cfg)
    found: list[Finding] = []
    for name, sha in cur.items():
        rel = f"{spec['migrations_dir']}/{name}"
        if name not in lock:
            found.append(Finding(NAME, rel, 0, t("migration.unpinned")))
        elif lock[name] != sha:
            found.append(Finding(NAME, rel, 0, t("migration.edited")))
    for name in lock:
        if name not in cur:
            found.append(Finding(NAME, lock_rel, 0, t("migration.stale_lock", name=name)))
    pat = re.compile(spec["pattern"])
    nums = sorted(int(pat.match(n).group("n")) for n in cur)
    for a, b in zip(nums, nums[1:]):
        if b == a:
            found.append(Finding(NAME, spec["migrations_dir"], 0, t("migration.duplicate", n=a)))
        elif b != a + 1:
            found.append(Finding(NAME, spec["migrations_dir"], 0, t("migration.gap", a=a, b=b)))
    return found


def selftest() -> list[str]:
    errs: list[str] = []
    on = {"project": {"packs": ["postgres"]}}
    m1, m2 = "CREATE TABLE a (id int);\n", "ALTER TABLE a ADD b int;\n"
    lock = f"0001_init.sql {_sha(m1.encode())}\n0002_b.sql {_sha(m2.encode())}\n"
    base = {"db/migrations/0001_init.sql": m1, "db/migrations/0002_b.sql": m2, "db/migrations.lock": lock}
    with fixture(base, on) as cfg:
        expect(errs, "khớp khoá", check(cfg), red=False)
    with fixture({**base, "db/migrations/0001_init.sql": m1 + "-- sửa\n"}, on) as cfg:
        expect(errs, "sửa migration đã ghim", check(cfg), red=True)
    with fixture({**base, "db/migrations/0003_c.sql": "SELECT 1;\n"}, on) as cfg:
        expect(errs, "chưa ghim", check(cfg), red=True)
    with fixture({**base, "db/migrations/0004_d.sql": "SELECT 1;\n"}, on) as cfg:
        f = check(cfg)
        if not any(x.message == t("migration.gap", a=2, b=4) for x in f):
            errs.append("đứt quãng: kỳ vọng ĐỎ")
    with fixture({**base, "db/migrations/0002_dup.sql": "SELECT 1;\n"}, on) as cfg:
        f = check(cfg)
        if not any(x.message == t("migration.duplicate", n=2) for x in f):
            errs.append("trùng số: kỳ vọng ĐỎ")
    return errs
