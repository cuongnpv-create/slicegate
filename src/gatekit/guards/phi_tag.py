"""Guard `phi_tag` (gói healthcare) — mỗi cột SQL chứa dữ liệu sức khoẻ phải KHAI nhãn `-- phi` trên cùng dòng.

Quy định về dữ liệu sức khoẻ đòi biết PHI nằm ở đâu (bản đồ dữ liệu) để áp mã hoá, quyền xem, nhật ký truy cập, hạn lưu
và xoá theo yêu cầu. Nhãn bắt buộc khiến mỗi cột PHI mới phải qua gate `privacy-lead` thay vì lặng lẽ vào DB; danh sách
cột có nhãn chính là bản đồ dữ liệu (`grep -rn -- "-- phi" db/`).

ĐỎ khi cột (trong `CREATE TABLE` hoặc `ALTER TABLE … ADD COLUMN`) có tên là TÊN PHI (cùng luật từ của `phi_log`) mà dòng
ấy thiếu `-- phi` (vd `diagnosis_code text, -- phi: mã hoá cột, chỉ vai clinician đọc`).
"""
from __future__ import annotations

import re

from gatekit.config import Config
from gatekit.guards._common import Finding, expect, fixture, iter_files, read
from gatekit.guards.phi_log import _spec, is_phi
from gatekit.messages import t

NAME = "phi_tag"
PACK = "healthcare"
FAST = True
DEFECT = {"vi": "cột dữ liệu sức khoẻ mới vào DB không ai rà mã hoá, quyền xem, nhật ký truy cập, hạn lưu",
          "en": "a new health-data column reaches the database without review of encryption, access control, access logging, retention"}

_COL = re.compile(r"^\s*(?:alter\s+table\s+[\w.\"]+\s+add\s+(?:column\s+)?(?:if\s+not\s+exists\s+)?)?\"?(?P<col>[A-Za-z_]\w*)\"?\s+"
                  r"(?P<type>[A-Za-z]\w*)", re.I)
_SQL_KEYWORDS = {"create", "table", "primary", "constraint", "foreign", "unique", "check", "index", "alter", "insert", "select",
                 "update", "delete", "comment", "grant", "references", "on", "drop"}
_TAG = re.compile(r"--\s*phi\b", re.I)


def check(cfg: Config) -> list[Finding]:
    spec = _spec(cfg)
    found: list[Finding] = []
    for rel in iter_files(cfg, exts=(".sql",)):
        for i, line in enumerate(read(cfg, rel).splitlines(), 1):
            code = line.split("--", 1)[0]
            m = _COL.match(code)
            if not m or m.group("col").lower() in _SQL_KEYWORDS:
                continue
            if is_phi(spec, m.group("col")) and not _TAG.search(line):
                found.append(Finding(NAME, rel, i, t("phi.untagged", name=m.group("col"))))
    return found


def selftest() -> list[str]:
    errs: list[str] = []
    on = {"project": {"packs": ["healthcare"]}}
    with fixture({"db/1.sql": "CREATE TABLE visits (\n  id uuid,\n  patient_id uuid,\n  diagnosis_code text, -- phi: mã hoá cột\n  allergy_count int\n);\n"}, on) as cfg:
        expect(errs, "cột PHI có nhãn + id + số đếm", check(cfg), red=False)
    with fixture({"db/1.sql": "CREATE TABLE patients (\n  id uuid,\n  date_of_birth date\n);\n"}, on) as cfg:
        expect(errs, "ngày sinh thiếu nhãn", check(cfg), red=True)
    with fixture({"db/2.sql": "ALTER TABLE patients ADD COLUMN medication_list jsonb;\n"}, on) as cfg:
        expect(errs, "ALTER ADD COLUMN thuốc thiếu nhãn", check(cfg), red=True)
    with fixture({"db/2.sql": "ALTER TABLE patients ADD COLUMN medication_list jsonb; -- phi\n"}, on) as cfg:
        expect(errs, "ALTER có nhãn", check(cfg), red=False)
    return errs
