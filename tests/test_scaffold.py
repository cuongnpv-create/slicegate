from __future__ import annotations

import re

import pytest

from slicegate.cli import main
from slicegate.config import load
from slicegate.scaffold import init

ALL_PACKS = ["i18n", "multi_provider", "legacy_upgrade", "postgres", "fintech", "data_pipeline", "ecommerce", "saas_multitenant", "healthcare", "logistics"]


@pytest.mark.parametrize("lang", ["vi", "en"])
@pytest.mark.parametrize("level", ["lite", "standard", "regulated"])
@pytest.mark.parametrize("packs", [[], ALL_PACKS], ids=["no-pack", "all-packs"])
def test_init_renders_clean(repo, level, packs, lang):
    written, skipped = init(repo, name="Demo", level=level, packs=packs, lanes=[("core", "P"), ("be", "PB")],
                            language=lang)
    assert not skipped
    for rel in written:
        text = (repo / rel).read_text(encoding="utf-8")
        assert not re.search(r"\{\{[A-Z_#/][^}]*\}\}", text), f"{rel} còn chỗ giữ"
    agents = sorted(p.stem for p in (repo / ".claude/agents").glob("*.md"))
    cfg = load(repo)
    assert set(cfg.agents()) <= set(agents)
    if "fintech" in packs:
        assert {"execution-lead", "quant-lead", "domain-auditor"} <= set(agents)
    if "ecommerce" in packs:
        assert {"checkout-lead", "pricing-lead"} <= set(agents)
        assert (repo / "docs/governance/ECOMMERCE_GUIDE.md").exists()
    if "saas_multitenant" in packs:
        assert {"tenancy-lead", "billing-lead"} <= set(agents)
        assert (repo / "docs/governance/SAAS_GUIDE.md").exists()
    if "healthcare" in packs:
        assert {"privacy-lead", "clinical-safety-lead"} <= set(agents)
        assert (repo / "docs/governance/HEALTHCARE_GUIDE.md").exists()
    if "logistics" in packs:
        assert {"fulfillment-lead", "routing-lead"} <= set(agents)
        assert (repo / "docs/governance/LOGISTICS_GUIDE.md").exists()
    if level == "lite":
        assert not (repo / "docs/ledger/LEDGER.md").exists()
        assert not (repo / "docs/governance/SESSION_PROTOCOL.md").exists()
    else:
        assert (repo / "docs/ledger/be/LEDGER.md").exists()
        assert "PB-L<n>" in (repo / "docs/ledger/be/LEDGER.md").read_text(encoding="utf-8")


@pytest.mark.parametrize("lang", ["vi", "en"])
def test_fresh_init_is_green(repo, lang):
    init(repo, name="Demo", level="regulated", packs=ALL_PACKS, language=lang)
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


@pytest.mark.parametrize("language,docs,expect", [
    ("en", "", "Process for every slice"),
    ("vi", "", "Quy trình mỗi lát"),
    ("ja", "", "Process for every slice"),        # chưa có mẫu tiếng Nhật ⇒ en
    ("ja", "vi", "Quy trình mỗi lát"),           # khai docs_language ⇒ theo khai
])
def test_docs_language_selection(repo, language, docs, expect):
    init(repo, name="Demo", level="standard", packs=["fintech"], language=language, docs_language=docs)
    assert expect in (repo / "CLAUDE.md").read_text(encoding="utf-8")
    assert f"Communicate in `{language}`" in (repo / ".claude/agents/execution-lead.md").read_text(encoding="utf-8") \
        or f"Giao tiếp bằng `{language}`" in (repo / ".claude/agents/execution-lead.md").read_text(encoding="utf-8")
    toml = (repo / "slicegate.toml").read_text(encoding="utf-8")
    assert ("SINGLE SOURCE" in toml) == ("Process for every slice" == expect)


def test_cli_docs_language(repo):
    assert main(["--root", str(repo), "init", "--name", "X", "--language", "en", "--level", "lite"]) == 0
    assert "Hard architectural constraints" in (repo / "CLAUDE.md").read_text(encoding="utf-8")


def test_init_seeds_manifest_from_existing_tests(repo):
    """Lượt `check` đầu trên dự án có sẵn test ⇒ ⛔ ĐỎ test_wiring (đo trên itsdangerous: 5 tệp test đỏ oan)."""
    for rel in ("tests/unit/test_a.py", "tests/unit/test_b.py", "tests/test_top.py", "web/src/app.test.ts"):
        (repo / rel).parent.mkdir(parents=True, exist_ok=True)
        (repo / rel).write_text("", encoding="utf-8")
    init(repo, name="Demo", level="standard", packs=[], lanes=[("be", "PB")])
    man = (repo / "tests/manifest.tsv").read_text(encoding="utf-8")
    assert "tests/unit/test_*.py\tbe\t1" in man and man.count("tests/unit/") == 1
    assert "tests/test_*.py\tbe\t1" in man and "web/src/*.test.ts\tbe\t1" in man
    assert main(["--root", str(repo), "check"]) == 0


def test_migrate_from_gatekit(repo, capsys):
    """Dự án cài từ thời tên gatekit chuyển sang slicegate một lần: tên tệp, thư mục, hook, settings."""
    init(repo, name="demo", level="lite", packs=[])
    import subprocess
    (repo / "slicegate.toml").rename(repo / "gatekit.toml")
    (repo / ".slicegate").rename(repo / ".gatekit")
    (repo / ".gatekit/hooks/pre-commit").write_text("#!/bin/sh\ngatekit check --fast\n", encoding="utf-8")
    settings = repo / ".claude/settings.json"
    settings.write_text(settings.read_text(encoding="utf-8").replace(".slicegate/", ".gatekit/"), encoding="utf-8")
    subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)
    assert main(["--root", str(repo), "migrate"]) == 0
    assert (repo / "slicegate.toml").exists() and not (repo / "gatekit.toml").exists()
    assert (repo / ".slicegate/hooks").is_dir() and not (repo / ".gatekit").exists()
    assert "gatekit" not in (repo / ".slicegate/hooks/pre-commit").read_text(encoding="utf-8")
    assert ".gatekit/" not in settings.read_text(encoding="utf-8")
    assert "gatekit" not in (repo / ".git/hooks/pre-commit").read_text(encoding="utf-8")
    assert main(["--root", str(repo), "migrate"]) == 0   # chạy lại: không có gì để chuyển
    assert not load(repo).legacy
