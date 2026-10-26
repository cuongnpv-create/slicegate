from __future__ import annotations

import pytest

from gatekit.config import ConfigError, from_dict, load


def test_defaults(tmp_path):
    cfg = from_dict(tmp_path, {})
    assert cfg.level == "standard"
    assert cfg.lanes()[0]["prefix"] == "P"
    assert cfg.is_prod("src/app.py") and not cfg.is_prod("docs/x.md")
    assert cfg.excluded("frontend/node_modules/x.js")


def test_deep_merge_keeps_defaults(tmp_path):
    cfg = from_dict(tmp_path, {"tests": {"budget": {"mutant_seconds": 3}}})
    assert cfg["tests"]["budget"]["mutant_seconds"] == 3
    assert cfg["tests"]["budget"]["tier1_seconds"] == 180


@pytest.mark.parametrize("over", [
    {"project": {"level": "max"}},
    {"project": {"packs": ["nope"]}},
    {"ledger": {"lanes": [{"name": "a", "prefix": "P", "dir": "x"}, {"name": "b", "prefix": "P", "dir": "y"}]}},
    {"zones": {"T": {"paths": ["("], "grep": []}}},
])
def test_invalid(tmp_path, over):
    with pytest.raises(ConfigError):
        from_dict(tmp_path, over)


def test_load_requires_file(tmp_path):
    with pytest.raises(ConfigError):
        load(tmp_path)
    assert load(tmp_path, required=False).level == "standard"


def test_agents_by_level(tmp_path):
    assert from_dict(tmp_path, {"project": {"level": "lite"}}).agents() == ["chief-architect", "qa-lead"]
    assert "compliance-officer" in from_dict(tmp_path, {"project": {"level": "regulated"}}).agents()
    assert "compliance-officer" not in from_dict(tmp_path, {}).agents()
