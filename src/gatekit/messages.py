"""Catalog thông báo của dòng lệnh, guard và công cụ — `vi` · `en`.

Một cách truy cập DUY NHẤT: `t("khoá", **tham_số)`. Ngôn ngữ chọn một lần cho cả tiến trình (`set_lang`), theo thứ tự:
biến môi trường `GATEKIT_LANG` → `project.docs_language` → `project.language` nếu có catalog → `en`.
Thiếu khoá ⇒ KeyError (⛔ in khoá thô cho người dùng); test `test_messages` ghim hai catalog cùng khoá, cùng tham số.
"""
from __future__ import annotations

import os
from typing import Any

LANGS = ("vi", "en")
_lang = "vi"
if os.environ.get("GATEKIT_LANG"):
    _lang = os.environ["GATEKIT_LANG"] if os.environ["GATEKIT_LANG"] in LANGS else "en"


def set_lang(lang: str) -> None:
    global _lang
    _lang = lang if lang in LANGS else "en"


def get_lang() -> str:
    return _lang


def lang_for(cfg: Any) -> str:
    env = os.environ.get("GATEKIT_LANG", "")
    if env:
        return env if env in LANGS else "en"
    project = cfg.data["project"]
    explicit = project.get("docs_language") or ""
    if explicit:
        return explicit
    lang = project.get("language", "vi")
    return lang if lang in LANGS else "en"


def t(msg_key: str, /, **params: Any) -> str:
    return CATALOG[_lang][msg_key].format(**params)


def pick(texts: dict[str, str]) -> str:
    """Chọn bản theo ngôn ngữ hiện tại từ một dict {lang: chữ} (vd DEFECT của guard)."""
    return texts.get(_lang) or texts["en"]


CATALOG: dict[str, dict[str, str]] = {
    "vi": {
        # ── cli ──
        "cli.desc": "Quy trình có cổng duyệt cho đội agent AI.",
        "cli.help_root": "gốc repo (mặc định thư mục hiện tại)",
        "cli.help_lane": "name:PREFIX, lặp lại cho nhiều làn (làn đầu = sổ chung)",
        "cli.help_language": "ngôn ngữ agent giao tiếp",
        "cli.help_docs_language": "ngôn ngữ bộ mẫu tài liệu (mặc định: theo --language nếu có mẫu, ngược lại en)",
        "cli.help_all": "cả guard của gói chưa bật",
        "cli.help_strict": "rc 1 khi có vấn đề",
        "cli.help_changed": "chỉ đột biến bị ảnh hưởng bởi diff BASE..HEAD",
        "cli.lane_format": "--lane phải dạng name:PREFIX (nhận {spec!r})",
        "cli.init_skipped": "  = {path} (đã có, bỏ qua)",
        "cli.init_done": "gatekit init: {written} tệp mới, {skipped} bỏ qua. Kế: điền CLAUDE.md §1/§2/§7, khai [zones], `gatekit hooks install`.",
        "cli.guard_crashed": "🔴 {name}: guard lỗi khi chạy",
        "cli.guard_red": "🔴 {name} — {n} vi phạm (chặn: {defect})",
        "cli.more": "   … còn {n}",
        "cli.zone_heaviest": "Vùng nặng nhất: {zone}",
        "cli.zone_content": "(nội dung)",
        "cli.zone_required": "Bắt buộc [{zone}]: {req}",
        "cli.zone_missing_suite": "🔴 tệp vùng T/K chưa có bộ đột biến thường trực canh:",
        "cli.alloc_args": "alloc cần --lane --kind --count --owner",
        "cli.roll_args": "roll cần --lane",
        "cli.record_args": "record cần --kind và --subject",
        "cli.ledger_unique": "🟢 số sổ duy nhất",
        "cli.open_count": "{n} điều kiện OPEN",
        "cli.dry_run": "(thử) ",
        "cli.roll_done": "{dry}cuộn {n} entry: {ids}",
        "cli.debt_ok": "🟢 nợ: đủ cột, chưa quá hạn",
        "cli.exempt": "[miễn]",
        "cli.quota_ok": "🟢 tỷ lệ lát đạt",
        "cli.recorded": "đã ghi",
        "cli.anchors_ok": "🟢 neo đột biến: {mutants} đột biến, {suites} bộ",
        "cli.plan_count": "{n} đột biến được chọn{full}",
        "cli.plan_full": " (ĐỦ)",
        "cli.no_mutants": "không có đột biến nào bị ảnh hưởng",
        "cli.mut_summary": "{killed}/{total} bị giết · {secs:.1f}s",
        "cli.mut_budget": "⚠ ngân sách: tổng {total:.0f}s > {limit}s",
        "cli.all_survived": "⚠ MỌI đột biến đều SỐNG — kiểm lệnh có chạy mã của BẢN SAO không (gói cài `pip -e` / đường dẫn tuyệt đối trỏ về checkout gốc ⇒ đột biến không có tác dụng). Python: thêm `PYTHONPATH=src` vào cmd.",
        "cli.migrations_locked": "ghim {n} migration mới: {names}",
        "cli.no_git_hooks": "không thấy .git/hooks — chạy trong gốc repo git",
        "cli.missing_hook": "thiếu {path} — chạy gatekit init",
        "cli.hook_installed": "  cài {name}",
        "cli.report_header": "── 📋 gatekit · {name} · mức {level} ──",
        "cli.report_line": "   điều kiện OPEN: {opens} · nợ có vấn đề: {debt} · số sổ trùng: {dups} · tỷ lệ lát: {quota}",
        "cli.quota_pass": "🟢 đạt",
        "cli.quota_fail": "🔴 {n} vi phạm",
        "cli.config_error": "cấu hình: {e}",
        "cli.error": "lỗi: {e}",
        # ── config ──
        "config.level": "project.level = {value!r} — chỉ nhận {allowed}",
        "config.docs_language": "project.docs_language = {value!r} — chỉ nhận '', 'vi', 'en'",
        "config.dup_prefix": "ledger.lanes trùng prefix: {prefixes}",
        "config.bad_regex": "zones.{zone}: regex hỏng {rx!r}: {err}",
        "config.unknown_pack": "project.packs: gói lạ {pack!r} — có: {known}",
        "config.missing": "thiếu {path} — chạy `gatekit init` trước",
        # ── guard: chung ──
        "selftest.want_red": "{label}: kỳ vọng ĐỎ nhưng XANH",
        "selftest.want_green": "{label}: kỳ vọng XANH nhưng ĐỎ: {first}",
        # ── test_wiring ──
        "test_wiring.bad_line": "dòng manifest phải là `path<TAB>làn<TAB>tầng(0-4)[<TAB>ghi chú]`",
        "test_wiring.no_manifest": "có {n} tệp test nhưng thiếu manifest",
        "test_wiring.not_wired": "test/bộ đột biến chưa khai ở manifest nào — không có nơi chạy nó",
        "test_wiring.glob_empty": "glob `{pat}` không khớp tệp nào",
        "test_wiring.stale": "`{pat}` không tồn tại (manifest cũ)",
        # ── naming_scope ──
        "naming.file_ascii": "tên tệp mã phải ASCII",
        "naming.ident": "định danh không phải ASCII `{name}` — đặt tên tiếng Anh",
        "naming.baseline_stale": "mục baseline `{key}` không còn trong mã — xoá dòng (baseline chỉ co lại)",
        # ── secret_leak ──
        "secret.pem": "khối private key PEM",
        "secret.aws": "khoá AWS",
        "secret.slack": "token Slack",
        "secret.github": "token GitHub",
        "secret.literal": "{what} dán thẳng trong repo",
        "secret.assign": "gán hằng cho `{name}` — đọc bí mật từ tệp/biến môi trường, ⛔ chữ cứng",
        "secret.sink": "bí mật có đường ra: `{name}` đi vào {where}",
        # ── locale_parity ──
        "locale.no_dir": "thiếu thư mục catalog",
        "locale.extra_lang": "ngôn ngữ `{lang}` không khai trong packs.i18n.langs",
        "locale.missing_lang": "thiếu ngôn ngữ",
        "locale.bad_json": "JSON hỏng: {msg}",
        "locale.not_flat": "phải là object phẳng {{khoá: chuỗi}}",
        "locale.prefix": "khoá `{key}` phải bắt đầu bằng `{ns}.`",
        "locale.empty": "khoá `{key}` rỗng",
        "locale.missing_file": "thiếu tệp (có ở `{ref}`)",
        "locale.extra_file": "tệp thừa (không có ở `{ref}`)",
        "locale.missing_key": "thiếu khoá `{key}` so với `{ref}`",
        "locale.extra_key": "thừa khoá `{key}` so với `{ref}`",
        "locale.params": "khoá `{key}`: tham số {{…}} lệch `{ref}`",
        # ── provider_name_scope · partition_key_scope ──
        "provider.outside": "chuỗi `{token}` của `{provider}` ngoài `{home}`",
        "partition.missing": "bảng `{table}` thiếu cột `{column}` (∨ chú thích `-- partition: global <lý do>`)",
        # ── legacy_import_ban ──
        "legacy.import": "import `{name}` từ hệ cũ `{legacy}` — chép có ghi nguồn thay vì import",
        # ── money_float · pci_scope ──
        "money.annotation": "`{name}` khai kiểu float — tiền dùng Decimal hoặc số nguyên đơn vị nhỏ nhất",
        "money.returns": "hàm `{name}` trả float — tiền dùng Decimal hoặc số nguyên đơn vị nhỏ nhất",
        "money.cast": "`float({name})` — ép tiền sang số thực làm lệch xu khi cộng/làm tròn",
        "money.sql": "cột tiền `{name}` kiểu {type} — dùng NUMERIC(p,s) hoặc BIGINT đơn vị nhỏ nhất",
        "money.parse_float": "`parseFloat({name})` — tiền dùng thư viện thập phân hoặc số nguyên đơn vị nhỏ nhất",
        "pci.column": "cột `{name}` lưu dữ liệu thẻ — chỉ lưu token + last4 + hãng thẻ; CVV ⛔ bao giờ lưu",
        "pci.field": "trường `{name}` ({cls}) giữ dữ liệu thẻ — chỉ lưu token + last4 + hãng thẻ; CVV ⛔ bao giờ lưu",
        # ── tenant_scope · tenant_rls ──
        "tenant.ddl": "bảng `{table}` thiếu cột `{column}` (∨ chú thích `-- tenant: global <lý do>` cho bảng dùng chung)",
        "tenant.query": "truy vấn chạm bảng tenant `{tables}` mà không lọc `{column}` (∨ `tenant-scope: ignore <lý do>`)",
        "rls.not_enabled": "bảng tenant `{table}` chưa `ENABLE ROW LEVEL SECURITY`",
        "rls.no_policy": "bảng tenant `{table}` chưa có `CREATE POLICY` nào",
        # ── migration_scope ──
        "migration.unpinned": "migration chưa ghim — `gatekit migrations lock` sau khi gate duyệt",
        "migration.edited": "migration ĐÃ GHIM bị sửa byte — viết migration mới thay vì sửa",
        "migration.stale_lock": "dòng khoá `{name}` trỏ tệp không còn",
        "migration.duplicate": "trùng số migration {n}",
        "migration.gap": "đứt quãng số migration {a} → {b}",
        # ── ledger ──
        "ledger.unknown_lane": "làn lạ `{name}` — có: {known}",
        "ledger.unknown_kind": "loại lạ `{kind}` — có {known}",
        "ledger.count": "count ≥ 1",
        "ledger.duplicate": "{id} định nghĩa {n} lần (làn {lane})",
        "ledger.archive_title": "# LEDGER lưu trữ {quarter} — làn {lane}",
        # ── debt ──
        "debt.columns": "{id}: dòng thiếu cột (cần Nợ · Khuyết tật · Điều kiện đóng · Lát đóng · Hạn · TT)",
        "debt.missing": "{id}: nợ MỞ thiếu {what}",
        "debt.what_defect": "khuyết tật còn ngỏ",
        "debt.what_condition": "điều kiện đóng",
        "debt.what_slice": "lát đóng",
        "debt.bad_date": "{id}: hạn `{due}` không phải YYYY-MM-DD",
        "debt.overdue": "{id}: QUÁ HẠN {due}",
        # ── slice_quota ──
        "quota.kind_code": "MÃ",
        "quota.kind_gov": "QUẢN TRỊ",
        "quota.no_id": "(không mã) {sha}",
        "quota.too_soon": "{id}: lát QUẢN TRỊ khi mới có {have}/{need} lát MÃ sau chuỗi quản trị trước",
        "quota.run": "{id}: {run} lát QUẢN TRỊ liền nhau (trần {max})",
        # ── guard_hygiene ──
        "hygiene.bad_kind": "kind ∈ {kinds}",
        "hygiene.bad_field": "trường không được chứa tab/xuống dòng",
        "hygiene.catches": "Guard — số lần bắt lỗi thật:",
        "hygiene.incidents": "Lớp lỗi — số lần nổ (≥ {n} ⇒ đủ điều kiện đề xuất guard):",
        "hygiene.eligible": "  ⇐ ĐỦ ĐIỀU KIỆN",
        # ── risk_zone ──
        "zone.req_T": "bộ đột biến THƯỜNG TRỰC trong manifest; đột biến gỡ từng cổng tại TỪNG chỗ gọi ⇒ ĐỎ; ca âm cho mọi đường từ chối",
        "zone.req_K": "bộ đột biến THƯỜNG TRỰC trong manifest; ca âm: thiếu quyền ⇒ từ chối có tên; bí mật ⛔ ra log",
        "zone.req_F": "số vàng nguồn ĐỘC LẬP (sách/bảng công bố/đáp án giải tích) là test thường trực + ≥ 1 đột biến đánh lõi công thức",
        "zone.req_other": "test hành vi + ≥ 1 ca âm có kỳ vọng từ nguồn NGOÀI mã; đột biến chỉ khi gate nêu TÊN test nghi rỗng (≤ 3, một lần)",
        "zone.other": "khác",
        # ── mutants ──
        "mutants.no_cmd": "{suite}: đột biến {id} thiếu cmd",
        "mutants.dup_id": "{suite}: id `{id}` trùng với {other}",
        "mutants.no_file": "{suite}:{id}: tệp `{file}` không tồn tại",
        "mutants.anchor_count": "{suite}:{id}: neo xuất hiện {n} lần trong `{file}` (phải đúng 1)",
        "mutants.no_why": "{suite}:{id}: thiếu `why` — đột biến phải nói khuyết tật nó mô phỏng",
        "mutants.unknown_only": "MUT_ONLY có mã lạ: {ids}",
        "mutants.baseline_red": "lệnh `{cmd}` ĐỎ trên bản sao CHƯA đột biến (rc={rc}) — sửa test trước",
        "mutants.slow": "⚠ ngân sách: `{cmd}` mất {secs:.1f}s > {per:.0f}s/đột biến — thu hẹp lệnh (-k, test-double rẻ)",
        "mutants.anchor_drift": "  ANCHOR    {id}  neo lệch trong {file}",
    },
    "en": {
        # ── cli ──
        "cli.desc": "Gated development process for teams of AI agents.",
        "cli.help_root": "repository root (default: current directory)",
        "cli.help_lane": "name:PREFIX, repeat for several lanes (first lane = shared ledger)",
        "cli.help_language": "language agents communicate in",
        "cli.help_docs_language": "language of the document templates (default: follow --language if templates exist, else en)",
        "cli.help_all": "also guards of packs that are not enabled",
        "cli.help_strict": "exit code 1 when there are problems",
        "cli.help_changed": "only mutants affected by the diff BASE..HEAD",
        "cli.lane_format": "--lane must be name:PREFIX (got {spec!r})",
        "cli.init_skipped": "  = {path} (exists, skipped)",
        "cli.init_done": "gatekit init: {written} new files, {skipped} skipped. Next: fill in CLAUDE.md §1/§2/§7, declare [zones], `gatekit hooks install`.",
        "cli.guard_crashed": "🔴 {name}: guard crashed",
        "cli.guard_red": "🔴 {name} — {n} violation(s) (blocks: {defect})",
        "cli.more": "   … {n} more",
        "cli.zone_heaviest": "Heaviest zone: {zone}",
        "cli.zone_content": "(content)",
        "cli.zone_required": "Required [{zone}]: {req}",
        "cli.zone_missing_suite": "🔴 zone T/K files without a permanent mutant suite guarding them:",
        "cli.alloc_args": "alloc needs --lane --kind --count --owner",
        "cli.roll_args": "roll needs --lane",
        "cli.record_args": "record needs --kind and --subject",
        "cli.ledger_unique": "🟢 ledger ids are unique",
        "cli.open_count": "{n} OPEN condition(s)",
        "cli.dry_run": "(dry run) ",
        "cli.roll_done": "{dry}rolled {n} entr(y/ies): {ids}",
        "cli.debt_ok": "🟢 debt: all columns present, nothing overdue",
        "cli.exempt": "[exempt]",
        "cli.quota_ok": "🟢 slice ratio OK",
        "cli.recorded": "recorded",
        "cli.anchors_ok": "🟢 mutant anchors: {mutants} mutants, {suites} suites",
        "cli.plan_count": "{n} mutant(s) selected{full}",
        "cli.plan_full": " (FULL)",
        "cli.no_mutants": "no mutant is affected",
        "cli.mut_summary": "{killed}/{total} killed · {secs:.1f}s",
        "cli.mut_budget": "⚠ budget: total {total:.0f}s > {limit}s",
        "cli.all_survived": "⚠ EVERY mutant SURVIVED — check that the command runs the COPY's code (a package installed with `pip -e` / an absolute path pointing back to the original checkout ⇒ mutants have no effect). Python: add `PYTHONPATH=src` to cmd.",
        "cli.migrations_locked": "pinned {n} new migration(s): {names}",
        "cli.no_git_hooks": ".git/hooks not found — run at the root of a git repository",
        "cli.missing_hook": "missing {path} — run gatekit init",
        "cli.hook_installed": "  installed {name}",
        "cli.report_header": "── 📋 gatekit · {name} · level {level} ──",
        "cli.report_line": "   OPEN conditions: {opens} · debt problems: {debt} · duplicate ledger ids: {dups} · slice ratio: {quota}",
        "cli.quota_pass": "🟢 OK",
        "cli.quota_fail": "🔴 {n} violation(s)",
        "cli.config_error": "config: {e}",
        "cli.error": "error: {e}",
        # ── config ──
        "config.level": "project.level = {value!r} — must be one of {allowed}",
        "config.docs_language": "project.docs_language = {value!r} — must be '', 'vi' or 'en'",
        "config.dup_prefix": "ledger.lanes has duplicate prefixes: {prefixes}",
        "config.bad_regex": "zones.{zone}: invalid regex {rx!r}: {err}",
        "config.unknown_pack": "project.packs: unknown pack {pack!r} — available: {known}",
        "config.missing": "{path} is missing — run `gatekit init` first",
        # ── guard: shared ──
        "selftest.want_red": "{label}: expected RED but got GREEN",
        "selftest.want_green": "{label}: expected GREEN but got RED: {first}",
        # ── test_wiring ──
        "test_wiring.bad_line": "a manifest line must be `path<TAB>lane<TAB>tier(0-4)[<TAB>note]`",
        "test_wiring.no_manifest": "{n} test file(s) exist but the manifest is missing",
        "test_wiring.not_wired": "test/mutant suite not declared in any manifest — nothing runs it",
        "test_wiring.glob_empty": "glob `{pat}` matches no file",
        "test_wiring.stale": "`{pat}` does not exist (stale manifest)",
        # ── naming_scope ──
        "naming.file_ascii": "code file names must be ASCII",
        "naming.ident": "non-ASCII identifier `{name}` — use an English name",
        "naming.baseline_stale": "baseline entry `{key}` no longer in the code — delete the line (the baseline only shrinks)",
        # ── secret_leak ──
        "secret.pem": "PEM private key block",
        "secret.aws": "AWS key",
        "secret.slack": "Slack token",
        "secret.github": "GitHub token",
        "secret.literal": "{what} pasted into the repository",
        "secret.assign": "literal assigned to `{name}` — read secrets from a file/environment variable, never hard-code them",
        "secret.sink": "secret has a way out: `{name}` flows into {where}",
        # ── locale_parity ──
        "locale.no_dir": "catalog directory missing",
        "locale.extra_lang": "language `{lang}` is not declared in packs.i18n.langs",
        "locale.missing_lang": "language missing",
        "locale.bad_json": "invalid JSON: {msg}",
        "locale.not_flat": "must be a flat object {{key: string}}",
        "locale.prefix": "key `{key}` must start with `{ns}.`",
        "locale.empty": "key `{key}` is empty",
        "locale.missing_file": "file missing (present in `{ref}`)",
        "locale.extra_file": "extra file (not in `{ref}`)",
        "locale.missing_key": "key `{key}` missing compared to `{ref}`",
        "locale.extra_key": "extra key `{key}` compared to `{ref}`",
        "locale.params": "key `{key}`: {{…}} parameters differ from `{ref}`",
        # ── provider_name_scope · partition_key_scope ──
        "provider.outside": "string `{token}` of `{provider}` outside `{home}`",
        "partition.missing": "table `{table}` lacks column `{column}` (∨ comment `-- partition: global <reason>`)",
        # ── legacy_import_ban ──
        "legacy.import": "import `{name}` from the legacy system `{legacy}` — copy with a source label instead of importing",
        # ── money_float · pci_scope ──
        "money.annotation": "`{name}` is typed float — use Decimal or integer minor units for money",
        "money.returns": "function `{name}` returns float — use Decimal or integer minor units for money",
        "money.cast": "`float({name})` — casting money to floating point drifts cents when summing/rounding",
        "money.sql": "money column `{name}` is {type} — use NUMERIC(p,s) or BIGINT minor units",
        "money.parse_float": "`parseFloat({name})` — use a decimal library or integer minor units for money",
        "pci.column": "column `{name}` stores card data — store only token + last4 + card brand; never store CVV",
        "pci.field": "field `{name}` ({cls}) holds card data — store only token + last4 + card brand; never store CVV",
        # ── tenant_scope · tenant_rls ──
        "tenant.ddl": "table `{table}` lacks column `{column}` (∨ comment `-- tenant: global <reason>` for a shared table)",
        "tenant.query": "query touches tenant table `{tables}` without filtering on `{column}` (∨ `tenant-scope: ignore <reason>`)",
        "rls.not_enabled": "tenant table `{table}` does not `ENABLE ROW LEVEL SECURITY`",
        "rls.no_policy": "tenant table `{table}` has no `CREATE POLICY`",
        # ── migration_scope ──
        "migration.unpinned": "migration not pinned — `gatekit migrations lock` after the gate approves",
        "migration.edited": "a PINNED migration was edited — write a new migration instead",
        "migration.stale_lock": "lock line `{name}` points to a file that no longer exists",
        "migration.duplicate": "duplicate migration number {n}",
        "migration.gap": "gap in migration numbers {a} → {b}",
        # ── ledger ──
        "ledger.unknown_lane": "unknown lane `{name}` — available: {known}",
        "ledger.unknown_kind": "unknown kind `{kind}` — available: {known}",
        "ledger.count": "count ≥ 1",
        "ledger.duplicate": "{id} defined {n} times (lane {lane})",
        "ledger.archive_title": "# LEDGER archive {quarter} — lane {lane}",
        # ── debt ──
        "debt.columns": "{id}: row is missing columns (needs Debt · Defect · Close condition · Closing slice · Due · ST)",
        "debt.missing": "{id}: OPEN debt lacks {what}",
        "debt.what_defect": "the defect left open",
        "debt.what_condition": "a close condition",
        "debt.what_slice": "a closing slice",
        "debt.bad_date": "{id}: due `{due}` is not YYYY-MM-DD",
        "debt.overdue": "{id}: OVERDUE {due}",
        # ── slice_quota ──
        "quota.kind_code": "CODE",
        "quota.kind_gov": "GOVERNANCE",
        "quota.no_id": "(no id) {sha}",
        "quota.too_soon": "{id}: GOVERNANCE slice after only {have}/{need} CODE slices since the previous governance run",
        "quota.run": "{id}: {run} GOVERNANCE slices in a row (limit {max})",
        # ── guard_hygiene ──
        "hygiene.bad_kind": "kind ∈ {kinds}",
        "hygiene.bad_field": "fields may not contain tabs/newlines",
        "hygiene.catches": "Guards — real catches:",
        "hygiene.incidents": "Defect classes — times fired (≥ {n} ⇒ eligible to propose a guard):",
        "hygiene.eligible": "  ⇐ ELIGIBLE",
        # ── risk_zone ──
        "zone.req_T": "a PERMANENT mutant suite in the manifest; a mutant removing each gate at EACH call site ⇒ RED; negative cases for every refusal path",
        "zone.req_K": "a PERMANENT mutant suite in the manifest; negative cases: missing permission ⇒ named refusal; secrets never in logs",
        "zone.req_F": "INDEPENDENT golden numbers (book/published table/analytic answer) as a permanent test + ≥ 1 mutant hitting the formula core",
        "zone.req_other": "behaviour tests + ≥ 1 negative case with an expectation from OUTSIDE the code; mutants only when the gate names a TEST suspected empty (≤ 3, once)",
        "zone.other": "other",
        # ── mutants ──
        "mutants.no_cmd": "{suite}: mutant {id} has no cmd",
        "mutants.dup_id": "{suite}: id `{id}` duplicates {other}",
        "mutants.no_file": "{suite}:{id}: file `{file}` does not exist",
        "mutants.anchor_count": "{suite}:{id}: anchor occurs {n} times in `{file}` (must be exactly 1)",
        "mutants.no_why": "{suite}:{id}: missing `why` — a mutant must state the defect it simulates",
        "mutants.unknown_only": "MUT_ONLY has unknown ids: {ids}",
        "mutants.baseline_red": "command `{cmd}` is RED on the UNMUTATED copy (rc={rc}) — fix the tests first",
        "mutants.slow": "⚠ budget: `{cmd}` took {secs:.1f}s > {per:.0f}s/mutant — narrow the command (-k, cheap test-double)",
        "mutants.anchor_drift": "  ANCHOR    {id}  anchor drifted in {file}",
    },
}
