from __future__ import annotations

import re

import pytest

from gatekit.cli import main
from gatekit.config import load
from gatekit.scaffold import init

ALL_PACKS = ["i18n", "multi_provider", "legacy_upgrade", "postgres", "fintech", "data_pipeline"]


@pytest.mark.parametrize("level", ["lite", "standard", "regulated"])
@pytest.mark.parametrize("packs", [[], ALL_PACKS], ids=["no-pack", "all-packs"])
def test_init_renders_clean(repo, level, packs):
    written, skipped = init(repo, name="Demo", level=level, packs=packs, lanes=[("core", "P"), ("be", "PB")])
    assert not skipped
    for rel in written:
        text = (repo / rel).read_text(encoding="utf-8")
        assert not re.search(r"\{\{[A-Z_#/][^}]*\}\}", text), f"{rel} còn chỗ giữ"
    agents = sorted(p.stem for p in (repo / ".claude/agents").glob("*.md"))
    cfg = load(repo)
    assert set(cfg.agents()) <= set(agents)
    if "fintech" in packs:
        assert {"execution-lead", "quant-lead", "domain-auditor"} <= set(agents)
    if level == "lite":
        assert not (repo / "docs/ledger/LEDGER.md").exists()
        assert not (repo / "docs/governance/SESSION_PROTOCOL.md").exists()
    else:
        assert (repo / "docs/ledger/be/LEDGER.md").exists()
        assert "PB-L<n>" in (repo / "docs/ledger/be/LEDGER.md").read_text(encoding="utf-8")


def test_fresh_init_is_green(repo):
    init(repo, name="Demo", level="regulated", packs=ALL_PACKS)
    assert main(["--root", str(repo), "check", "--full"]) == 0
    assert main(["--root", str(repo), "selftest"]) == 0


def test_init_never_overwrites(repo):
    init(repo, name="Demo", level="standard", packs=[])
    (repo / "CLAUDE.md").write_text("của tôi", encoding="utf-8")
    written, skipped = init(repo, name="Demo", level="standard", packs=[])
    assert "CLAUDE.md" in skipped and (repo / "CLAUDE.md").read_text(encoding="utf-8") == "của tôi"
    assert not written


def test_constitution_articles_follow_packs(repo):
    init(repo, name="Demo", level="standard", packs=["i18n"])
    text = (repo / "docs/governance/CONSTITUTION.md").read_text(encoding="utf-8")
    assert "Bản địa hoá" in text and "Nhà cung cấp là tường minh" not in text


def test_hooks_install(repo):
    init(repo, name="Demo", level="lite", packs=[])
    assert main(["--root", str(repo), "hooks", "install"]) == 0
    assert (repo / ".git/hooks/pre-push").stat().st_mode & 0o111
