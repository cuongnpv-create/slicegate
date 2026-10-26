"""Guard `secret_leak` — bí mật không có đường ra khỏi hệ, và không nằm trong repo.

ĐỎ khi:
  1. (Python, AST) biến/thuộc tính có tên khớp `secrets.name_regex` được đưa vào print / log / repr / f-string /
     ngoại lệ — đường ra log, stdout, thông báo lỗi.
  2. (mọi tệp văn bản) hằng bí mật dán thẳng: khối PEM private key, khoá AWS `AKIA…`, `xox?-` Slack,
     `ghp_` GitHub, hoặc gán `<tên bí mật> = "<chuỗi ≥ 8 ký tự>"`.
     Luật gán hằng BỎ QUA tệp test (`tests.test_globs` ∨ thư mục tests/fixtures) — khoá giả trong test là bình thường
     (đo trên itsdangerous: 7/7 báo nhầm là `secret_key="secret-key"` trong test) — và giá trị giữ chỗ
     (example · dummy · fake · changeme · placeholder · your-… · xxx). Khối PEM / khoá AWS / token thật vẫn ĐỎ ở mọi nơi.
Miễn trừ: `secrets.allowlist` — mỗi dòng `tệp:dòng` hoặc `tệp:*`, kèm lý do sau dấu `#`.
"""
from __future__ import annotations

import ast
import re

from slicegate.config import Config
from slicegate.guards._common import Finding, expect, fixture, iter_files, read
from slicegate.messages import t

NAME = "secret_leak"
PACK = None
FAST = False
DEFECT = {"vi": "khoá/mật khẩu/token lọt ra log, stdout, thông báo lỗi hoặc bị commit vào repo",
          "en": "keys/passwords/tokens leak into logs, stdout, error messages or get committed"}

_LITERALS = [
    (re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"), "secret.pem"),
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "secret.aws"),
    (re.compile(r"\bxox[abprs]-[0-9A-Za-z-]{10,}"), "secret.slack"),
    (re.compile(r"\bghp_[0-9A-Za-z]{36}\b"), "secret.github"),
]
_PLACEHOLDER = re.compile(r"(?i)(example|dummy|fake|changeme|change[-_]me|placeholder|your[-_]|xxx|\*\*\*)")
_TEST_DIR = re.compile(r"(^|/)(tests?|fixtures?|__tests__|testdata)/")
_SINKS = {"print", "repr", "format"}
_LOG_ATTRS = {"debug", "info", "warning", "warn", "error", "exception", "critical", "log", "write"}
_TEXT_EXT = (".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".java", ".kt", ".rs", ".cs", ".rb", ".php",
             ".env", ".ini", ".cfg", ".toml", ".yaml", ".yml", ".json", ".sh", ".sql", ".properties")


def _allow(cfg: Config) -> set[str]:
    p = cfg.root / cfg["secrets"]["allowlist"]
    if not p.exists():
        return set()
    return {ln.split("#", 1)[0].strip() for ln in p.read_text(encoding="utf-8").splitlines() if ln.split("#", 1)[0].strip()}


def _names(node: ast.AST) -> list[str]:
    out = []
    for n in ast.walk(node):
        if isinstance(n, ast.Name):
            out.append(n.id)
        elif isinstance(n, ast.Attribute):
            out.append(n.attr)
    return out


def _py_sinks(rel: str, text: str, rx: re.Pattern) -> list[tuple[int, str]]:
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return []
    hits: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        args: list[ast.AST] = []
        where = ""
        if isinstance(node, ast.Call):
            f = node.func
            if isinstance(f, ast.Name) and f.id in _SINKS:
                args, where = list(node.args), f.id
            elif isinstance(f, ast.Attribute) and f.attr in _LOG_ATTRS:
                args, where = list(node.args) + [k.value for k in node.keywords], f"…{f.attr}()"
        elif isinstance(node, ast.JoinedStr):
            args, where = [v.value for v in node.values if isinstance(v, ast.FormattedValue)], "f-string"
        elif isinstance(node, ast.Raise) and node.exc is not None:
            args, where = [node.exc], "raise"
        for a in args:
            bad = [n for n in _names(a) if rx.search(n)]
            if bad:
                hits.append((getattr(node, "lineno", 0), t("secret.sink", name=bad[0], where=where)))
    return hits


def check(cfg: Config) -> list[Finding]:
    rx = re.compile(cfg["secrets"]["name_regex"])
    assign = re.compile(r"""(?P<n>[A-Za-z_][\w]*)\s*[:=]\s*["'](?P<v>[^"'\s]{8,})["']""")
    allow = _allow(cfg)
    found: list[Finding] = []

    def add(rel: str, line: int, msg: str) -> None:
        if f"{rel}:{line}" in allow or f"{rel}:*" in allow:
            return
        found.append(Finding(NAME, rel, line, msg))

    for rel in iter_files(cfg, exts=_TEXT_EXT):
        if rel == cfg["secrets"]["allowlist"]:
            continue
        text = read(cfg, rel)
        is_test = bool(_TEST_DIR.search(rel)) or any(re.search(g, rel) for g in cfg["tests"]["test_globs"])
        for i, line in enumerate(text.splitlines(), 1):
            for pat, what in _LITERALS:
                if pat.search(line):
                    add(rel, i, t("secret.literal", what=t(what)))
            for m in ([] if is_test else assign.finditer(line)):
                v = m.group("v")
                if rx.search(m.group("n")) and not v.startswith(("${", "$", "<", "os.environ", "env:")) and not v.isupper() \
                        and not _PLACEHOLDER.search(v):
                    add(rel, i, t("secret.assign", name=m.group("n")))
        if rel.endswith(".py"):
            for line_no, msg in _py_sinks(rel, text, rx):
                add(rel, line_no, msg)
    return found


def selftest() -> list[str]:
    errs: list[str] = []
    with fixture({"src/a.py": "import logging\nlog=logging.getLogger()\ndef f(user):\n    log.info('login %s', user)\n"}) as cfg:
        expect(errs, "log tên thường", check(cfg), red=False)
    with fixture({"src/a.py": "def f(api_key):\n    print(api_key)\n"}) as cfg:
        expect(errs, "print(api_key)", check(cfg), red=True)
    with fixture({"src/a.py": "def f(cfg):\n    x = f'{cfg.password}'\n"}) as cfg:
        expect(errs, "f-string password", check(cfg), red=True)
    with fixture({"src/a.py": "def f(token):\n    raise ValueError(token)\n"}) as cfg:
        expect(errs, "raise mang token", check(cfg), red=True)
    with fixture({"conf/app.yaml": "db_password: \"hunter22secret\"\n"}) as cfg:
        expect(errs, "gán hằng mật khẩu", check(cfg), red=True)
    with fixture({"conf/app.yaml": "db_password: \"${DB_PASSWORD}\"\n"}) as cfg:
        expect(errs, "tham chiếu biến môi trường", check(cfg), red=False)
    with fixture({"tests/test_sign.py": "s = Signer(secret_key=\"secret-key\")\napi_key = \"abcdefgh123\"\n"}) as cfg:
        expect(errs, "khoá giả trong test", check(cfg), red=False)
    with fixture({"src/settings.py": "api_key = \"changeme-please\"\n"}) as cfg:
        expect(errs, "giá trị giữ chỗ", check(cfg), red=False)
    with fixture({"tests/data.py": "K = \"-----BEGIN PRIVATE KEY-----\"\n"}) as cfg:
        expect(errs, "PEM trong test vẫn ĐỎ", check(cfg), red=True)
    with fixture({"k.pem.txt": "", "src/k.py": "K = '''-----BEGIN PRIVATE KEY-----'''\n"}) as cfg:
        expect(errs, "PEM", check(cfg), red=True)
    with fixture({"src/a.py": "def f(api_key):\n    print(api_key)\n",
                  ".slicegate/secret_allowlist.txt": "src/a.py:2  # ca minh hoạ\n"}) as cfg:
        expect(errs, "allowlist", check(cfg), red=False)
    return errs
