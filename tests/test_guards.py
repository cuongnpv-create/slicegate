from __future__ import annotations

import pytest

from gatekit.config import from_dict
from gatekit.guards import all_guards, enabled_guards

GUARDS = all_guards()


@pytest.mark.parametrize("guard", GUARDS, ids=[g.NAME for g in GUARDS])
def test_selftest_green(guard):
    assert guard.selftest() == []


@pytest.mark.parametrize("guard", GUARDS, ids=[g.NAME for g in GUARDS])
def test_contract(guard):
    assert isinstance(guard.NAME, str) and guard.NAME
    assert guard.PACK is None or isinstance(guard.PACK, str)
    assert isinstance(guard.FAST, bool)
    assert set(guard.DEFECT) == {"vi", "en"} and all(v.strip() for v in guard.DEFECT.values()), \
        "mỗi guard phải khai khuyết tật mã nó chặn, đủ vi + en"


def test_core_guards_always_on(tmp_path):
    cfg = from_dict(tmp_path, {})
    names = {g.NAME for g in enabled_guards(cfg)}
    assert {"test_wiring", "naming_scope", "secret_leak"} <= names
    assert "locale_parity" not in names


def test_pack_guards_follow_packs(tmp_path):
    cfg = from_dict(tmp_path, {"project": {"packs": ["i18n", "postgres"]}})
    names = {g.NAME for g in enabled_guards(cfg)}
    assert {"locale_parity", "migration_scope"} <= names
    assert "provider_name_scope" not in names


def test_fast_subset(tmp_path):
    cfg = from_dict(tmp_path, {})
    fast = {g.NAME for g in enabled_guards(cfg, fast_only=True)}
    assert "secret_leak" not in fast and "test_wiring" in fast
