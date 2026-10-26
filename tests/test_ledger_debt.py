from __future__ import annotations

import datetime as dt

import pytest

from gatekit.config import from_dict
from gatekit.tools import debt, ledger
from tests.conftest import write

LANES = {"ledger": {"lanes": [{"name": "core", "prefix": "P", "dir": "docs/ledger"},
                              {"name": "be", "prefix": "PB", "dir": "docs/ledger/be"}]}}


def entry(n: int, date: str, status: str, conds: str = "") -> str:
    return f"## P-L{n} — G-OUT S-{n} · {date}\nTrạng thái: {status}\nVERDICT: APPROVE\n{conds}\n"


def test_alloc_after_used_and_reserved(tmp_path):
    cfg = from_dict(tmp_path, LANES)
    write(tmp_path, "docs/ledger/LEDGER.md", "# x\n" + entry(1, "2026-01-01", "CLOSED") + entry(7, "2026-01-02", "OPEN"))
    assert ledger.alloc(cfg, "core", "L", 1, "điều phối") == (8, 8)
    assert ledger.alloc(cfg, "core", "L", 3, "điều phối") == (9, 11)
    assert ledger.alloc(cfg, "be", "L", 1, "điều phối") == (1, 1)   # làn khác đánh số riêng
    with pytest.raises(KeyError):
        ledger.alloc(cfg, "nope", "L", 1, "x")


def test_duplicates_detected(tmp_path):
    cfg = from_dict(tmp_path, LANES)
    write(tmp_path, "docs/ledger/LEDGER.md", entry(3, "2026-01-01", "OPEN") + entry(3, "2026-01-02", "OPEN"))
    assert any("P-L3" in d for d in ledger.duplicates(cfg))
    write(tmp_path, "docs/ledger/LEDGER.md", entry(3, "2026-01-01", "OPEN") + entry(4, "2026-01-02", "OPEN"))
    assert ledger.duplicates(cfg) == []


def test_conditions_and_open(tmp_path):
    cfg = from_dict(tmp_path, LANES)
    conds = "- **P-C10** [OPEN] mất khoá idempotency · đo: pytest -k idem · vùng: T\n- **P-C11** [CLOSED] x · đo: y · vùng: K\n"
    write(tmp_path, "docs/ledger/LEDGER.md", entry(1, "2026-01-01", "OPEN", conds))
    assert ledger.used(cfg, "core", "C") == [10, 11]
    opens = ledger.open_conditions(cfg, "core")
    assert len(opens) == 1 and opens[0].startswith("P-C10")


def test_roll_moves_only_old_closed(tmp_path):
    cfg = from_dict(tmp_path, LANES)
    write(tmp_path, "docs/ledger/LEDGER.md", "# đầu sổ\n\n" + entry(1, "2025-01-10", "CLOSED")
          + entry(2, "2025-01-11", "OPEN") + entry(3, "2026-10-20", "CLOSED"))
    ids = ledger.roll(cfg, "core", today=dt.date(2026, 10, 26))
    assert ids == ["P-L1"]
    live = (tmp_path / "docs/ledger/LEDGER.md").read_text(encoding="utf-8")
    assert "# đầu sổ" in live and "P-L1 " not in live and "P-L2" in live and "P-L3" in live
    arch = (tmp_path / "docs/ledger/archive/LEDGER-2025Q1.md").read_text(encoding="utf-8")
    assert "P-L1" in arch
    # số đã cuộn vẫn được tính khi cấp số và kiểm trùng
    assert ledger.alloc(cfg, "core", "L", 1, "x") == (4, 4)
    write(tmp_path, "docs/ledger/LEDGER.md", live + entry(1, "2026-10-21", "OPEN"))
    assert any("P-L1" in d for d in ledger.duplicates(cfg))


HEAD = "| Mã | Nợ | Khuyết tật còn ngỏ | Điều kiện đóng (đo được) | Lát đóng | Hạn | TT |\n|---|---|---|---|---|---|---|\n"


def test_debt_rules(tmp_path):
    cfg = from_dict(tmp_path, LANES)
    write(tmp_path, "docs/ledger/DEBT.md", HEAD
          + "| P-N1 | chờ API | đơn treo | test_x XANH | S-9 | 2026-12-01 | OPEN |\n"
          + "| P-N2 | chờ | — | test_y | S-9 | 2026-12-01 | OPEN |\n"
          + "| P-N3 | chờ | z | test_z | S-9 | 2026-01-01 | OPEN |\n"
          + "| P-N4 | xong | z | test_z | S-9 | 2020-01-01 | CLOSED |\n"
          + "| P-N5 | chờ | z | test_z | S-9 | sớm | OPEN |\n")
    probs = debt.problems(cfg, today=dt.date(2026, 10, 26))
    joined = "\n".join(probs)
    assert "P-N1" not in joined and "P-N4" not in joined
    assert "P-N2: nợ MỞ thiếu khuyết tật" in joined
    assert "P-N3: QUÁ HẠN" in joined
    assert "P-N5" in joined


def test_roll_english_status(tmp_path):
    cfg = from_dict(tmp_path, LANES)
    body = "## P-L1 — G-OUT S-1 · 2025-01-10\nStatus: CLOSED\n\n## P-L2 — G-OUT S-2 · 2025-01-11\nStatus: OPEN\n"
    write(tmp_path, "docs/ledger/LEDGER.md", body)
    assert ledger.roll(cfg, "core", today=dt.date(2026, 10, 26)) == ["P-L1"]
