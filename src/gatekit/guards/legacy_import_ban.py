"""Guard `legacy_import_ban` (gói legacy_upgrade) — hệ mới ⛔ import mã hệ cũ; mang mã cũ sang = CHÉP có ghi nguồn.

ĐỎ khi một tệp Python/TS/JS import module thuộc `packs.legacy_upgrade.legacy_modules`
(vd `legacy_app`, `@old/core`) — phụ thuộc ngầm vào cây cũ khiến không tắt được hệ cũ và không test được ở hệ mới.
"""
from __future__ import annotations

import ast
import re

from gatekit.config import Config
from gatekit.guards._common import Finding, expect, fixture, iter_files, read
from gatekit.messages import t

NAME = "legacy_import_ban"
PACK = "legacy_upgrade"
FAST = True
DEFECT = {"vi": "hệ mới phụ thuộc ngầm vào mã hệ cũ ⇒ tắt hệ cũ là gãy, hành vi cũ chạy mà không có test ở hệ mới",
          "en": "the new system silently depends on legacy code ⇒ turning legacy off breaks it, legacy behaviour runs untested"}

_JS_IMPORT = re.compile(r"""(?:import\s[^'"]*from\s*|import\s*\(|require\s*\()\s*['"](?P<m>[^'"]+)['"]""")


def check(cfg: Config) -> list[Finding]:
    mods = [m for m in cfg.pack("legacy_upgrade")["legacy_modules"] if m]
    if not mods:
        return []

    def banned(name: str) -> str | None:
        return next((m for m in mods if name == m or name.startswith(m + ".") or name.startswith(m + "/")), None)

    found: list[Finding] = []
    for rel in iter_files(cfg, exts=(".py", ".ts", ".tsx", ".js", ".jsx", ".mjs")):
        text = read(cfg, rel)
        if rel.endswith(".py"):
            try:
                tree = ast.parse(text)
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                names = []
                if isinstance(node, ast.Import):
                    names = [a.name for a in node.names]
                elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                    names = [node.module]
                for n in names:
                    if (m := banned(n)):
                        found.append(Finding(NAME, rel, node.lineno, t("legacy.import", name=n, legacy=m)))
        else:
            for i, line in enumerate(text.splitlines(), 1):
                for mm in _JS_IMPORT.finditer(line):
                    if (m := banned(mm.group("m"))):
                        found.append(Finding(NAME, rel, i, t("legacy.import", name=mm.group("m"), legacy=m)))
    return found


def selftest() -> list[str]:
    errs: list[str] = []
    on = {"project": {"packs": ["legacy_upgrade"]}, "packs": {"legacy_upgrade": {"legacy_modules": ["legacy_app", "@old/core"]}}}
    with fixture({"src/a.py": "import json\nfrom app.core import x\n"}, on) as cfg:
        expect(errs, "import thường", check(cfg), red=False)
    with fixture({"src/a.py": "from legacy_app.billing import charge\n"}, on) as cfg:
        expect(errs, "py import hệ cũ", check(cfg), red=True)
    with fixture({"src/a.ts": "import { x } from '@old/core/util';\n"}, on) as cfg:
        expect(errs, "ts import hệ cũ", check(cfg), red=True)
    with fixture({"src/a.py": "import legacy_application\n"}, on) as cfg:
        expect(errs, "tên gần giống không bị bắt nhầm", check(cfg), red=False)
    return errs
