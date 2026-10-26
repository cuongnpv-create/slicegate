"""Dòng lệnh gatekit.

  gatekit init [--name N] [--level lite|standard|regulated] [--pack P …] [--lane name:PREFIX …] [--force]
  gatekit check [--fast|--full]          guard đang bật (+ neo đột biến, số sổ trùng khi --full)
  gatekit selftest                        ca âm/dương của mọi guard đang bật
  gatekit zone --base <rev> [--rev R]     vùng rủi ro của diff + hình thức kiểm bắt buộc
  gatekit ledger alloc --lane L --kind L|D|C|N --count n --owner X
  gatekit ledger check | open | roll --lane L [--dry-run]
  gatekit debt                            nợ thiếu cột / quá hạn
  gatekit quota [--since R]               tỷ lệ lát quản trị : lát mã
  gatekit hygiene report | record --kind K --subject S --source S --description D
  gatekit mutants anchors | plan [--changed BASE] | run [--changed BASE]   (MUT_ONLY=id,… để chọn)
  gatekit migrations lock                 ghim migration mới (gói postgres)
  gatekit hooks install                   cài pre-commit / pre-push vào .git/hooks
  gatekit report [--brief]                tổng hợp: nợ, điều kiện OPEN, tỷ lệ lát
Mã thoát: 0 XANH · 1 ĐỎ · 2 lỗi dùng lệnh.
"""
from __future__ import annotations

import argparse
import os
import shutil
import sys
import traceback
from pathlib import Path

from gatekit import __version__
from gatekit.config import ConfigError, load


def _p(*a: object) -> None:
    print(*a, flush=True)


def cmd_init(args: argparse.Namespace) -> int:
    from gatekit.scaffold import init
    lanes = []
    for spec in args.lane or ["core:P"]:
        name, _, prefix = spec.partition(":")
        if not name or not prefix:
            _p(f"--lane phải dạng name:PREFIX (nhận {spec!r})")
            return 2
        lanes.append((name, prefix))
    root = Path(args.root)
    written, skipped = init(root, name=args.name or root.resolve().name, level=args.level,
                            packs=args.pack or [], language=args.language, lanes=lanes, force=args.force)
    for w in written:
        _p(f"  + {w}")
    for s in skipped:
        _p(f"  = {s} (đã có, bỏ qua)")
    _p(f"gatekit init: {len(written)} tệp mới, {len(skipped)} bỏ qua. Kế: điền CLAUDE.md §1/§2/§7, khai [zones], `gatekit hooks install`.")
    return 0


def _run_guards(cfg, *, fast: bool) -> int:
    from gatekit.guards import enabled_guards
    red = 0
    for g in enabled_guards(cfg, fast_only=fast):
        try:
            found = g.check(cfg)
        except Exception:  # fail-closed
            _p(f"🔴 {g.NAME}: guard lỗi khi chạy\n{traceback.format_exc()}")
            red += 1
            continue
        if found:
            red += 1
            _p(f"🔴 {g.NAME} — {len(found)} vi phạm (chặn: {g.DEFECT})")
            for f in found[:50]:
                _p(f"   {f}")
            if len(found) > 50:
                _p(f"   … còn {len(found) - 50}")
        else:
            _p(f"🟢 {g.NAME}")
    return red


def cmd_check(args: argparse.Namespace) -> int:
    cfg = load(args.root)
    red = _run_guards(cfg, fast=args.fast)
    if args.full:
        from gatekit.qa.mutants import anchor_problems
        from gatekit.tools.ledger import duplicates
        for name, probs in (("mutant_anchors", anchor_problems(cfg)), ("ledger_ids", duplicates(cfg))):
            if probs:
                red += 1
                _p(f"🔴 {name} — {len(probs)}")
                for x in probs:
                    _p(f"   {x}")
            else:
                _p(f"🟢 {name}")
    return 1 if red else 0


def cmd_selftest(args: argparse.Namespace) -> int:
    from gatekit.guards import all_guards, enabled_guards
    cfg = load(args.root, required=False)
    guards = all_guards() if args.all else enabled_guards(cfg)
    red = 0
    for g in guards:
        try:
            errs = g.selftest()
        except Exception:
            errs = [traceback.format_exc()]
        if errs:
            red += 1
            _p(f"🔴 {g.NAME} selftest")
            for e in errs:
                _p(f"   {e}")
        else:
            _p(f"🟢 {g.NAME} selftest")
    return 1 if red else 0


def cmd_zone(args: argparse.Namespace) -> int:
    from gatekit.qa.mutants import load_suites
    from gatekit.tools.risk_zone import REQUIREMENTS, classify
    cfg = load(args.root)
    rep = classify(cfg, args.base, args.rev)
    _p(f"Vùng nặng nhất: {rep.heaviest}")
    for z in ("T", "K", "F"):
        for f in rep.files.get(z, []):
            _p(f"  {z}  {f}")
        for h in rep.grep_hits.get(z, []):
            _p(f"  {z}  (nội dung) {h}")
    for z in rep.zones():
        _p(f"Bắt buộc [{z}]: {REQUIREMENTS[z]}")
    # T/K: mỗi tệp trong vùng phải có bộ đột biến THƯỜNG TRỰC canh nó
    import fnmatch
    suites = load_suites(cfg)
    missing = []
    for z in ("T", "K"):
        for f in rep.files.get(z, []):
            if not (cfg.root / f).exists():
                continue
            if not any(s.zone in ("T", "K") and any(fnmatch.fnmatchcase(f, t) or f == t
                                                     for m in s.mutants for t in m.targets) for s in suites):
                missing.append(f"{z}  {f}")
    if missing:
        _p("🔴 tệp vùng T/K chưa có bộ đột biến thường trực canh:")
        for x in missing:
            _p(f"   {x}")
        return 1
    return 0


def cmd_ledger(args: argparse.Namespace) -> int:
    from gatekit.tools import ledger
    cfg = load(args.root)
    if args.action == "alloc":
        if not (args.lane and args.kind and args.count and args.owner):
            _p("alloc cần --lane --kind --count --owner")
            return 2
        a, b = ledger.alloc(cfg, args.lane, args.kind, args.count, args.owner, args.note or "")
        prefix = next(x["prefix"] for x in cfg.lanes() if x["name"] == args.lane)
        _p(f"{prefix}-{args.kind}{a}" + (f"…{prefix}-{args.kind}{b}" if b != a else ""))
        return 0
    if args.action == "check":
        d = ledger.duplicates(cfg)
        for x in d:
            _p(f"🔴 {x}")
        if not d:
            _p("🟢 số sổ duy nhất")
        return 1 if d else 0
    if args.action == "open":
        n = 0
        for ln in cfg.lanes():
            for c in ledger.open_conditions(cfg, ln["name"]):
                _p(f"[{ln['name']}] {c}")
                n += 1
        _p(f"{n} điều kiện OPEN")
        return 0
    if args.action == "roll":
        if not args.lane:
            _p("roll cần --lane")
            return 2
        ids = ledger.roll(cfg, args.lane, dry_run=args.dry_run)
        _p(("(thử) " if args.dry_run else "") + f"cuộn {len(ids)} entry: {', '.join(ids) or '—'}")
        return 0
    return 2


def cmd_debt(args: argparse.Namespace) -> int:
    from gatekit.tools.debt import problems
    probs = problems(load(args.root))
    for x in probs:
        _p(f"🔴 {x}")
    if not probs:
        _p("🟢 nợ: đủ cột, chưa quá hạn")
    return 1 if probs and args.strict else 0


def cmd_quota(args: argparse.Namespace) -> int:
    from gatekit.tools.slice_quota import slices, violations
    cfg = load(args.root)
    seq = slices(cfg, args.since)
    for s in seq[-args.last:]:
        _p(f"  {s.kind:<9} {s.id}  ({len(s.commits)} commit){'  [miễn]' if s.exempt else ''}")
    v = violations(cfg, seq)
    for x in v:
        _p(f"🔴 {x}")
    if not v:
        _p("🟢 tỷ lệ lát đạt")
    return 1 if v else 0


def cmd_hygiene(args: argparse.Namespace) -> int:
    from gatekit.guards import all_guards
    from gatekit.tools import guard_hygiene as gh
    cfg = load(args.root)
    if args.action == "record":
        gh.record(cfg, args.kind, args.subject, args.source, args.description)
        _p("đã ghi")
        return 0
    _p(gh.report(cfg, [g.NAME for g in all_guards()]))
    return 0


def cmd_mutants(args: argparse.Namespace) -> int:
    from gatekit.qa import mutants as mq
    from gatekit.tools.risk_zone import changed
    cfg = load(args.root)
    suites = mq.load_suites(cfg)
    if args.action == "anchors":
        probs = mq.anchor_problems(cfg, suites)
        for x in probs:
            _p(f"🔴 {x}")
        if not probs:
            _p(f"🟢 neo đột biến: {sum(len(s.mutants) for s in suites)} đột biến, {len(suites)} bộ")
        return 1 if probs else 0
    only = [x.strip() for x in os.environ.get("MUT_ONLY", "").split(",") if x.strip()] or None
    files = changed(cfg, args.changed)[0] if args.changed else None
    picked = mq.select(suites, files, only)
    if args.action == "plan":
        for m in picked:
            _p(f"  {m.id:<20} {m.suite}  {m.why}")
        _p(f"{len(picked)} đột biến được chọn" + ("" if files is not None or only else " (ĐỦ)"))
        return 0
    if not picked:
        _p("không có đột biến nào bị ảnh hưởng")
        return 0
    res = mq.run(cfg, picked, log=_p)
    bad = [r for r in res if r.status != "KILLED"]
    total = sum(r.seconds for r in res)
    _p(f"{len(res) - len(bad)}/{len(res)} bị giết · {total:.1f}s")
    if total > cfg["tests"]["budget"]["mutants_total_seconds"]:
        _p(f"⚠ ngân sách: tổng {total:.0f}s > {cfg['tests']['budget']['mutants_total_seconds']}s")
    for r in bad:
        _p(f"🔴 {r.status}: {r.mutant.id} ({r.mutant.suite}) — {r.mutant.why}")
    if res and all(r.status == "SURVIVED" for r in res):
        _p("⚠ MỌI đột biến đều SỐNG — kiểm lệnh có chạy mã của BẢN SAO không (gói cài `pip -e` / đường dẫn tuyệt đối trỏ "
           "về checkout gốc ⇒ đột biến không có tác dụng). Python: thêm `PYTHONPATH=src` vào cmd.")
    return 1 if bad else 0


def cmd_migrations(args: argparse.Namespace) -> int:
    from gatekit.guards.migration_scope import write_lock
    added = write_lock(load(args.root))
    _p(f"ghim {len(added)} migration mới: {', '.join(added) or '—'}")
    return 0


def cmd_hooks(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    src = root / ".gatekit" / "hooks"
    dst = root / ".git" / "hooks"
    if not dst.is_dir():
        _p("không thấy .git/hooks — chạy trong gốc repo git")
        return 2
    for name in ("pre-commit", "pre-push"):
        if not (src / name).exists():
            _p(f"thiếu {src / name} — chạy gatekit init")
            return 2
        shutil.copy2(src / name, dst / name)
        (dst / name).chmod(0o755)
        _p(f"  cài {name}")
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    from gatekit.tools import ledger
    from gatekit.tools.debt import problems
    cfg = load(args.root)
    probs = problems(cfg)
    opens = [(ln["name"], c) for ln in cfg.lanes() for c in ledger.open_conditions(cfg, ln["name"])]
    dups = ledger.duplicates(cfg)
    quota = "—"
    try:
        from gatekit.tools.slice_quota import slices, violations
        v = violations(cfg, slices(cfg))
        quota = "🟢 đạt" if not v else f"🔴 {len(v)} vi phạm"
    except Exception:
        pass
    _p(f"── 📋 gatekit · {cfg['project']['name']} · mức {cfg.level} ──")
    _p(f"   điều kiện OPEN: {len(opens)} · nợ có vấn đề: {len(probs)} · số sổ trùng: {len(dups)} · tỷ lệ lát: {quota}")
    if not args.brief:
        for lane, c in opens:
            _p(f"   [{lane}] {c}")
        for x in probs + dups:
            _p(f"   🔴 {x}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="gatekit", description="Quy trình có cổng duyệt cho đội agent AI.")
    ap.add_argument("--version", action="version", version=f"gatekit {__version__}")
    ap.add_argument("--root", default=".", help="gốc repo (mặc định thư mục hiện tại)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("init")
    p.add_argument("--name")
    p.add_argument("--level", default="standard", choices=["lite", "standard", "regulated"])
    p.add_argument("--pack", action="append", choices=["i18n", "multi_provider", "legacy_upgrade", "postgres",
                                                       "fintech", "data_pipeline"])
    p.add_argument("--lane", action="append", help="name:PREFIX, lặp lại cho nhiều làn (làn đầu = sổ chung)")
    p.add_argument("--language", default="vi")
    p.add_argument("--force", action="store_true")
    p.set_defaults(fn=cmd_init)

    p = sub.add_parser("check")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--fast", action="store_true")
    g.add_argument("--full", action="store_true")
    p.set_defaults(fn=cmd_check)

    p = sub.add_parser("selftest")
    p.add_argument("--all", action="store_true", help="cả guard của gói chưa bật")
    p.set_defaults(fn=cmd_selftest)

    p = sub.add_parser("zone")
    p.add_argument("--base", required=True)
    p.add_argument("--rev", default="HEAD")
    p.set_defaults(fn=cmd_zone)

    p = sub.add_parser("ledger")
    p.add_argument("action", choices=["alloc", "check", "open", "roll"])
    p.add_argument("--lane")
    p.add_argument("--kind", choices=["L", "D", "C", "N"])
    p.add_argument("--count", type=int)
    p.add_argument("--owner")
    p.add_argument("--note")
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(fn=cmd_ledger)

    p = sub.add_parser("debt")
    p.add_argument("--strict", action="store_true", help="rc 1 khi có vấn đề")
    p.set_defaults(fn=cmd_debt)

    p = sub.add_parser("quota")
    p.add_argument("--since")
    p.add_argument("--last", type=int, default=10)
    p.set_defaults(fn=cmd_quota)

    p = sub.add_parser("hygiene")
    p.add_argument("action", choices=["report", "record"])
    p.add_argument("--kind", choices=["guard-catch", "incident"])
    p.add_argument("--subject")
    p.add_argument("--source", default="")
    p.add_argument("--description", default="")
    p.set_defaults(fn=cmd_hygiene)

    p = sub.add_parser("mutants")
    p.add_argument("action", choices=["anchors", "plan", "run"])
    p.add_argument("--changed", metavar="BASE", help="chỉ đột biến bị ảnh hưởng bởi diff BASE..HEAD")
    p.set_defaults(fn=cmd_mutants)

    p = sub.add_parser("migrations")
    p.add_argument("action", choices=["lock"])
    p.set_defaults(fn=cmd_migrations)

    p = sub.add_parser("hooks")
    p.add_argument("action", choices=["install"])
    p.set_defaults(fn=cmd_hooks)

    p = sub.add_parser("report")
    p.add_argument("--brief", action="store_true")
    p.set_defaults(fn=cmd_report)
    return ap


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.cmd == "hygiene" and args.action == "record" and not (args.kind and args.subject):
        _p("record cần --kind và --subject")
        return 2
    try:
        return args.fn(args)
    except ConfigError as e:
        _p(f"cấu hình: {e}")
        return 2
    except (KeyError, ValueError, RuntimeError) as e:
        _p(f"lỗi: {e}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
