"""Bộ mẫu vi ↔ en phải song song: cùng tập tệp, cùng chỗ giữ, cùng khối điều kiện.

Khuyết tật chặn: thêm/sửa mẫu ở một ngôn ngữ mà quên ngôn ngữ kia ⇒ dự án dựng bằng ngôn ngữ ấy thiếu tệp
hoặc thiếu luật (vd khối {{#pack i18n}} chỉ có ở bản vi).
"""
from __future__ import annotations

import re
from importlib import resources
from pathlib import Path

import pytest

from gatekit.scaffold import TEMPLATE_LANGS

ROOT = Path(str(resources.files("gatekit")))
TOKEN = re.compile(r"\{\{[^}]+\}\}")


def tree(base: Path) -> dict[str, Path]:
    return {p.relative_to(base).as_posix(): p for p in base.rglob("*") if p.is_file()}


def bases() -> list[tuple[str, dict[str, Path]]]:
    out = [("templates", {lang: ROOT / "templates" / lang for lang in TEMPLATE_LANGS})]
    for pack in sorted(p for p in (ROOT / "packs").iterdir() if p.is_dir()):
        out.append((f"packs/{pack.name}", {lang: pack / lang for lang in TEMPLATE_LANGS}))
    return out


@pytest.mark.parametrize("label,dirs", bases(), ids=[b[0] for b in bases()])
def test_same_files(label, dirs):
    trees = {lang: set(tree(d)) for lang, d in dirs.items()}
    ref = trees["vi"]
    for lang, files in trees.items():
        assert files == ref, f"{label}/{lang}: lệch tệp {sorted(files ^ ref)}"


@pytest.mark.parametrize("label,dirs", bases(), ids=[b[0] for b in bases()])
def test_same_placeholders(label, dirs):
    vi = tree(dirs["vi"])
    for lang, d in dirs.items():
        for rel, p in tree(d).items():
            a = sorted(TOKEN.findall(vi[rel].read_text(encoding="utf-8")))
            b = sorted(TOKEN.findall(p.read_text(encoding="utf-8")))
            assert a == b, f"{label}/{lang}/{rel}: chỗ giữ lệch {sorted(set(a) ^ set(b))}"


def test_en_templates_have_no_vietnamese():
    viet = re.compile(r"[ăâđêôơưạảấầẩẫậắằẳẵặẹẻẽếềểễệỉịọỏốồổỗộớờởỡợụủứừửữựỳỵỷỹ]", re.I)
    for base in [ROOT / "templates" / "en", *[(p / "en") for p in (ROOT / "packs").iterdir() if p.is_dir()]]:
        for rel, p in tree(base).items():
            for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
                assert not viet.search(line), f"{base.name}/{rel}:{i} còn tiếng Việt: {line.strip()[:80]}"
