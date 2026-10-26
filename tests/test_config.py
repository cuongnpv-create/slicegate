from __future__ import annotations

import pytest

from slicegate.config import ConfigError, from_dict, load


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


def test_new_name_has_no_legacy_paths(tmp_path):
    (tmp_path / "slicegate.toml").write_text('[project]\nname = "x"\n', encoding="utf-8")
    cfg = load(tmp_path)
    assert not cfg.legacy and cfg.state_dir == ".slicegate"
    assert cfg["secrets"]["allowlist"].startswith(".slicegate/")


def test_legacy_gatekit_toml_still_loads(tmp_path, capsys):
    """Dự án cài từ thời tên gatekit: đọc gatekit.toml, tệp trạng thái vẫn ở .gatekit/, có lời nhắc đổi tên."""
    import slicegate.config as config
    config._warned = False
    (tmp_path / "gatekit.toml").write_text('[project]\nname = "x"\n[naming]\nbaseline = "custom/base.txt"\n',
                                           encoding="utf-8")
    cfg = load(tmp_path)
    assert cfg.legacy and cfg.state_dir == ".gatekit"
    assert cfg["secrets"]["allowlist"] == ".gatekit/secret_allowlist.txt"
    assert cfg["naming"]["baseline"] == "custom/base.txt"   # giá trị dự án tự đặt giữ nguyên
    assert "gatekit.toml" in capsys.readouterr().err


def test_new_name_wins_over_legacy(tmp_path):
    (tmp_path / "slicegate.toml").write_text('[project]\nname = "new"\n', encoding="utf-8")
    (tmp_path / "gatekit.toml").write_text('[project]\nname = "old"\n', encoding="utf-8")
    assert load(tmp_path)["project"]["name"] == "new"
