"""Dòng lệnh gatekit.

  gatekit init [--name N] [--level lite|standard|regulated] [--pack P …] [--lane name:PREFIX …]
               [--language L] [--docs-language vi|en] [--force]
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
Mã thoát: 0 XANH · 1 ĐỎ · 2 lỗi dùng lệnh. Thông báo theo ngôn ngữ dự án (`messages.py`; ghi đè: GATEKIT_LANG=vi|en).
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
from gatekit.messages import lang_for, pick, set_lang, t


def _p(*a: object) -> None:
    print(*a, flush=True)


def cmd_init(args: argparse.Namespace) -> int:
    from gatekit.scaffold import init
    lanes = []
    for spec in args.lane or ["core:P"]:
        name, _, prefix = spec.partition(":")
        if not name or not prefix:
            _p(t("cli.lane_format", spec=spec))
            return 2
        lanes.append((name, prefix))
    root = Path(args.root)
    written, skipped = init(root, name=args.name or root.resolve().name, level=args.level,
                            packs=args.pack or [], language=args.language, lanes=lanes, force=args.force,
                            docs_language=args.docs_language)
    for w in written:
        _p(f"  + {w}")
    for s in skipped:
        _p(t("cli.init_skipped", path=s))
    _p(t("cli.init_done", written=len(written), skipped=len(skipped)))
    return 0


def _run_guards(cfg, *, fast: bool) -> int:
    from gatekit.guards import enabled_guards
    red = 0
    for g in enabled_guards(cfg, fast_only=fast):
        try:
            found = g.check(cfg)
        except Exception:  # fail-closed
            _p(t("cli.guard_crashed", name=g.NAME) + "\n" + traceback.format_exc())
            red += 1
            continue
        if found:
            red += 1
            _p(t("cli.guard_red", name=g.NAME, n=len(found), defect=pick(g.DEFECT)))
            for f in found[:50]:
                _p(f"   {f}")
            if len(found) > 50:
                _p(t("cli.more", n=len(found) - 50))
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
    from gatekit.tools.risk_zone import OTHER, classify, requirement
    cfg = load(args.root)
    rep = classify(cfg, args.base, args.rev)
    _p(t("cli.zone_heaviest", zone=t("zone.other") if rep.heaviest == OTHER else rep.heaviest))
    for z in ("T", "K", "F"):
        for f in rep.files.get(z, []):
            _p(f"  {z}  {f}")
        for h in rep.grep_hits.get(z, []):
            _p(f"  {z}  {t('cli.zone_content')} {h}")
    for z in rep.zones():
        _p(t("cli.zone_required", zone=t("zone.other") if z == OTHER else z, req=requirement(z)))
    # T/K: mỗi tệp trong vùng phải có bộ đột biến THƯỜNG TRỰC canh nó
    import fnmatch
    suites = load_suites(cfg)
    missing = []
    for z in ("T", "K"):
        for f in rep.files.get(z, []):
            if not (cfg.root / f).exists():
                continue
            if not any(s.zone in ("T", "K") and any(fnmatch.fnmatchcase(f, tgt) or f == tgt
                                                     for m in s.mutants for tgt in m.targets) for s in suites):
                missing.append(f"{z}  {f}")
    if missing:
        _p(t("cli.zone_missing_suite"))
        for x in missing:
            _p(f"   {x}")
        return 1
    return 0


def cmd_ledger(args: argparse.Namespace) -> int:
    from gatekit.tools import ledger
    cfg = load(args.root)
    if args.action == "alloc":
        if not (args.lane and args.kind and args.count and args.owner):
            _p(t("cli.alloc_args"))
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
            _p(t("cli.ledger_unique"))
        return 1 if d else 0
    if args.action == "open":
        n = 0
        for ln in cfg.lanes():
            for c in ledger.open_conditions(cfg, ln["name"]):
                _p(f"[{ln['name']}] {c}")
                n += 1
        _p(t("cli.open_count", n=n))
        return 0
    if args.action == "roll":
        if not args.lane:
            _p(t("cli.roll_args"))
            return 2
        ids = ledger.roll(cfg, args.lane, dry_run=args.dry_run)
        _p(t("cli.roll_done", dry=t("cli.dry_run") if args.dry_run else "", n=len(ids), ids=", ".join(ids) or "—"))
        return 0
    return 2


def cmd_debt(args: argparse.Namespace) -> int:
    from gatekit.tools.debt import problems
    probs = problems(load(args.root))
    for x in probs:
        _p(f"🔴 {x}")
    if not probs:
        _p(t("cli.debt_ok"))
    return 1 if probs and args.strict else 0


def cmd_quota(args: argparse.Namespace) -> int:
    from gatekit.tools.slice_quota import slices, violations
    cfg = load(args.root)
    seq = slices(cfg, args.since)
    for s in seq[-args.last:]:
        _p(f"  {s.kind:<10} {s.id}  ({len(s.commits)} commit)" + (f"  {t('cli.exempt')}" if s.exempt else ""))
    v = violations(cfg, seq)
    for x in v:
        _p(f"🔴 {x}")
    if not v:
        _p(t("cli.quota_ok"))
    return 1 if v else 0


def cmd_hygiene(args: argparse.Namespace) -> int:
    from gatekit.guards import all_guards
    from gatekit.tools import guard_hygiene as gh
    cfg = load(args.root)
    if args.action == "record":
        gh.record(cfg, args.kind, args.subject, args.source, args.description)
        _p(t("cli.recorded"))
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
            _p(t("cli.anchors_ok", mutants=sum(len(s.mutants) for s in suites), suites=len(suites)))
        return 1 if probs else 0
    only = [x.strip() for x in os.environ.get("MUT_ONLY", "").split(",") if x.strip()] or None
    files = changed(cfg, args.changed)[0] if args.changed else None
    picked = mq.select(suites, files, only)
    if args.action == "plan":
        for m in picked:
            _p(f"  {m.id:<20} {m.suite}  {m.why}")
        _p(t("cli.plan_count", n=len(picked), full="" if files is not None or only else t("cli.plan_full")))
        return 0
    if not picked:
        _p(t("cli.no_mutants"))
        return 0
    res = mq.run(cfg, picked, log=_p)
    bad = [r for r in res if r.status != "KILLED"]
    total = sum(r.seconds for r in res)
    _p(t("cli.mut_summary", killed=len(res) - len(bad), total=len(res), secs=total))
    if total > cfg["tests"]["budget"]["mutants_total_seconds"]:
        _p(t("cli.mut_budget", total=total, limit=cfg["tests"]["budget"]["mutants_total_seconds"]))
    for r in bad:
        _p(f"🔴 {r.status}: {r.mutant.id} ({r.mutant.suite}) — {r.mutant.why}")
    if res and all(r.status == "SURVIVED" for r in res):
        _p(t("cli.all_survived"))
    return 1 if bad else 0


def cmd_migrations(args: argparse.Namespace) -> int:
    from gatekit.guards.migration_scope import write_lock
    added = write_lock(load(args.root))
    _p(t("cli.migrations_locked", n=len(added), names=", ".join(added) or "—"))
    return 0


def cmd_hooks(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    src = root / ".gatekit" / "hooks"
    dst = root / ".git" / "hooks"
    if not dst.is_dir():
        _p(t("cli.no_git_hooks"))
        return 2
    for name in ("pre-commit", "pre-push"):
        if not (src / name).exists():
            _p(t("cli.missing_hook", path=src / name))
            return 2
        body = (src / name).read_text(encoding="utf-8")
        entry = os.environ.get("GATEKIT_ENTRY")   # chạy từ plugin: ghi đường dẫn lệnh vào hook (git không có PATH plugin)
        if entry:
            body = body.replace('GATEKIT_BIN="${GATEKIT_BIN:-}"', f'GATEKIT_BIN="${{GATEKIT_BIN:-{entry}}}"')
        (dst / name).write_text(body, encoding="utf-8")
        (dst / name).chmod(0o755)
        _p(t("cli.hook_installed", name=name))
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
        quota = t("cli.quota_pass") if not v else t("cli.quota_fail", n=len(v))
    except Exception:
        pass
    _p(t("cli.report_header", name=cfg["project"]["name"], level=cfg.level))
    _p(t("cli.report_line", opens=len(opens), debt=len(probs), dups=len(dups), quota=quota))
    if not args.brief:
        for lane, c in opens:
            _p(f"   [{lane}] {c}")
        for x in probs + dups:
            _p(f"   🔴 {x}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="gatekit", description=t("cli.desc"))
    ap.add_argument("--version", action="version", version=f"gatekit {__version__}")
    ap.add_argument("--root", default=".", help=t("cli.help_root"))
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("init")
    p.add_argument("--name")
    p.add_argument("--level", default="standard", choices=["lite", "standard", "regulated"])
    p.add_argument("--pack", action="append", choices=["i18n", "multi_provider", "legacy_upgrade", "postgres",
                                                       "fintech", "data_pipeline"])
    p.add_argument("--lane", action="append", help=t("cli.help_lane"))
    p.add_argument("--language", default="vi", help=t("cli.help_language"))
    p.add_argument("--docs-language", default="", choices=["", "vi", "en"],
                   help=t("cli.help_docs_language"))
    p.add_argument("--force", action="store_true")
    p.set_defaults(fn=cmd_init)

    p = sub.add_parser("check")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--fast", action="store_true")
    g.add_argument("--full", action="store_true")
    p.set_defaults(fn=cmd_check)

    p = sub.add_parser("selftest")
    p.add_argument("--all", action="store_true", help=t("cli.help_all"))
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
    p.add_argument("--strict", action="store_true", help=t("cli.help_strict"))
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
    p.add_argument("--changed", metavar="BASE", help=t("cli.help_changed"))
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


def _choose_lang(argv: list[str] | None) -> None:
    """Chọn ngôn ngữ thông báo TRƯỚC khi dựng parser (để cả --help cũng đúng ngôn ngữ)."""
    pre = argparse.ArgumentParser(add_help=False)
    pre.add_argument("--root", default=".")
    pre.add_argument("--language")
    pre.add_argument("--docs-language")
    known, _ = pre.parse_known_args(argv)
    try:
        cfg = load(known.root, required=False)
    except ConfigError:
        return
    if (cfg.root / "gatekit.toml").exists():
        set_lang(lang_for(cfg))
    elif known.docs_language or known.language:   # `gatekit init` trên repo chưa có cấu hình
        cfg.data["project"]["docs_language"] = known.docs_language or ""
        cfg.data["project"]["language"] = known.language or cfg.data["project"]["language"]
        set_lang(lang_for(cfg))
    else:
        set_lang(lang_for(cfg))


def main(argv: list[str] | None = None) -> int:
    _choose_lang(argv)
    args = build_parser().parse_args(argv)
    if args.cmd == "hygiene" and args.action == "record" and not (args.kind and args.subject):
        _p(t("cli.record_args"))
        return 2
    try:
        return args.fn(args)
    except ConfigError as e:
        _p(t("cli.config_error", e=e))
        return 2
    except (KeyError, ValueError, RuntimeError) as e:
        _p(t("cli.error", e=e))
        return 2


if __name__ == "__main__":
    sys.exit(main())
