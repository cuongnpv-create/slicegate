"""Guard `phi_log` (gói healthcare) — dữ liệu sức khoẻ (PHI) ⛔ đi vào log, print, ngoại lệ, công cụ analytics/giám sát lỗi.

Log, dịch vụ analytics và công cụ bắt lỗi nằm NGOÀI phạm vi bảo vệ của hồ sơ bệnh án (quyền xem, mã hoá, hạn lưu, nhật ký
truy cập): PHI vào đó là rò, và thường bị sao ra bên thứ ba.

ĐỎ khi một định danh là TÊN PHI — tách từ snake_case/camelCase, có từ trong `packs.healthcare.phi_words` (dob, ssn, mrn,
diagnosis, medication, allergy…) và ⛔ có từ trong `non_phi_words` (id, count, code_system…) — xuất hiện trong đối số của:
  · Python: print · logger.<debug|info|warning|error|exception|critical|log> · raise · analytics/giám sát
    (`track`, `capture`, `identify`, `set_user`, `set_context`, `set_extra`, `add_breadcrumb`, `capture_message`);
  · JS/TS: `console.<log|info|warn|error|debug>(…)`, `logger.<…>(…)`, `track(…)`, `Sentry.<…>(…)`.
"""
from __future__ import annotations

import ast
import re

from slicegate.config import Config
from slicegate.guards._common import Finding, expect, fixture, iter_files, read
from slicegate.guards.money_float import words
from slicegate.messages import t

NAME = "phi_log"
PACK = "healthcare"
FAST = True
DEFECT = {"vi": "dữ liệu sức khoẻ của bệnh nhân lọt ra log / analytics / công cụ bắt lỗi — ngoài quyền xem, mã hoá và hạn lưu",
          "en": "patient health data leaks into logs / analytics / error trackers — outside access control, encryption and retention"}

_LOG_ATTRS = {"debug", "info", "warning", "warn", "error", "exception", "critical", "log"}
_TRACK = {"track", "capture", "identify", "set_user", "set_context", "set_extra", "add_breadcrumb", "capture_message",
          "capture_exception"}
_JS_CALL = re.compile(r"\b(?:console\.(?:log|info|warn|error|debug)|logger\.\w+|track|Sentry\.\w+)\s*\((?P<args>[^;]*)")
# chuỗi truy cập `a.b.c` ⇒ chỉ xét `c` (thứ thật sự được ghi); `p.id` ⛔ là PHI dù `p` là bệnh nhân
_JS_LAST = re.compile(r"(?:[A-Za-z_$][\w$]*\s*\??\.\s*)*(?P<last>[A-Za-z_$][\w$]*)")
_JS_STR = re.compile(r"`(?:\\.|[^`\\])*`|\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\])*'")
_JS_TPL_EXPR = re.compile(r"\$\{([^}]*)\}")


def _js_args(args: str) -> str:
    """Bỏ chữ trong chuỗi (\"patient loaded\" ⛔ là dữ liệu) nhưng giữ biểu thức `${…}` của template literal."""
    return _JS_STR.sub(lambda m: " ".join(_JS_TPL_EXPR.findall(m.group(0))) if m.group(0).startswith("`") else " ", args)


def _spec(cfg: Config) -> tuple[set[str], set[str]]:
    pk = cfg.pack("healthcare")
    return {w.lower() for w in pk["phi_words"]}, {w.lower() for w in pk["non_phi_words"]}


def is_phi(spec: tuple[set[str], set[str]], name: str) -> bool:
    ws = words(name)
    return bool(ws & spec[0]) and not (ws & spec[1])


def _names(node: ast.AST) -> list[str]:
    """Tên của GIÁ TRỊ được ghi: `patient.id` ⇒ `id` (⛔ `patient`), `rec["dob"]` ⇒ `dob`, `patient` ⇒ `patient`."""
    if isinstance(node, ast.Name):
        return [node.id]
    if isinstance(node, ast.Attribute):
        return [node.attr]
    if isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Constant) and isinstance(node.slice.value, str):
        return [node.slice.value]   # record["diagnosis"]
    if isinstance(node, ast.Call):   # hàm(a) ⇒ xét đối số, ⛔ tên hàm
        return [n for a in list(node.args) + [k.value for k in node.keywords] for n in _names(a)]
    return [n for child in ast.iter_child_nodes(node) for n in _names(child)]


def check(cfg: Config) -> list[Finding]:
    spec = _spec(cfg)
    found: list[Finding] = []
    for rel in iter_files(cfg, exts=(".py", ".ts", ".tsx", ".js", ".jsx", ".mjs")):
        if not cfg.is_prod(rel):
            continue
        text = read(cfg, rel)
        if rel.endswith(".py"):
            try:
                tree = ast.parse(text)
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                args: list[ast.AST] = []
                where = ""
                if isinstance(node, ast.Call):
                    f = node.func
                    fname = f.id if isinstance(f, ast.Name) else f.attr if isinstance(f, ast.Attribute) else ""
                    if (isinstance(f, ast.Name) and fname == "print") or \
                            (isinstance(f, ast.Attribute) and fname in _LOG_ATTRS) or fname in _TRACK:
                        args, where = list(node.args) + [k.value for k in node.keywords], f"{fname}()"
                elif isinstance(node, ast.Raise) and node.exc is not None:
                    args, where = [node.exc], "raise"
                bad = sorted({n for a in args for n in _names(a) if is_phi(spec, n)})
                if bad:
                    found.append(Finding(NAME, rel, getattr(node, "lineno", 0), t("phi.sink", names=", ".join(bad), where=where)))
        else:
            for i, line in enumerate(text.splitlines(), 1):
                for m in _JS_CALL.finditer(line):
                    bad = sorted({x.group("last") for x in _JS_LAST.finditer(_js_args(m.group("args")))
                                  if is_phi(spec, x.group("last"))})
                    if bad:
                        found.append(Finding(NAME, rel, i, t("phi.sink", names=", ".join(bad), where=m.group(0).split("(")[0] + "()")))
    return found


def selftest() -> list[str]:
    errs: list[str] = []
    on = {"project": {"packs": ["healthcare"]}}
    with fixture({"src/visit.py": "import logging\nlog = logging.getLogger()\ndef f(patient_id, visit):\n    log.info('visit saved %s %s', patient_id, visit.id)\n"}, on) as cfg:
        expect(errs, "log id nội bộ", check(cfg), red=False)
    with fixture({"src/visit.py": "def f(log, patient):\n    log.info('saved %s', patient.diagnosis)\n"}, on) as cfg:
        expect(errs, "log chẩn đoán", check(cfg), red=True)
    with fixture({"src/visit.py": "def f(p):\n    print(f'DOB: {p.date_of_birth}')\n"}, on) as cfg:
        expect(errs, "print f-string ngày sinh", check(cfg), red=True)
    with fixture({"src/visit.py": "def f(rec):\n    raise ValueError(rec['medication'])\n"}, on) as cfg:
        expect(errs, "raise mang thuốc", check(cfg), red=True)
    with fixture({"src/visit.py": "import sentry_sdk\ndef f(p):\n    sentry_sdk.set_context('patient', {'mrn': p.mrn})\n"}, on) as cfg:
        expect(errs, "gửi MRN cho công cụ bắt lỗi", check(cfg), red=True)
    with fixture({"src/visit.ts": "export const f = (p) => console.log('allergies', p.allergies);\n"}, on) as cfg:
        expect(errs, "console.log dị ứng", check(cfg), red=True)
    with fixture({"src/visit.ts": "export const f = (p) => console.log('loaded', p.id, p.allergyCount);\n"}, on) as cfg:
        expect(errs, "console.log số đếm", check(cfg), red=False)
    with fixture({"src/visit.py": "def f(log, patient):\n    log.info('opened %s', patient.id)\n"}, on) as cfg:
        expect(errs, "patient.id là id nội bộ", check(cfg), red=False)
    with fixture({"src/visit.ts": "export const f = (p) => console.log('patient loaded', p.id);\n"}, on) as cfg:
        expect(errs, "chữ trong chuỗi không phải dữ liệu", check(cfg), red=False)
    with fixture({"src/visit.ts": "export const f = (p) => console.log(`dob=${p.dateOfBirth}`);\n"}, on) as cfg:
        expect(errs, "biểu thức trong template literal", check(cfg), red=True)
    with fixture({"src/visit.py": "def f(log, patient):\n    log.info('opened %s', patient)\n"}, on) as cfg:
        expect(errs, "ghi cả bản ghi bệnh nhân", check(cfg), red=True)
    with fixture({"tests/test_visit.py": "print(patient.diagnosis)\n"}, on) as cfg:
        expect(errs, "test không phải mã sản xuất", check(cfg), red=False)
    return errs
