"""`gatekit init` — dựng bộ quy trình vào một repo từ mẫu.

Bộ mẫu theo ngôn ngữ: `templates/<vi|en>/`, `packs/<gói>/<vi|en>/` (chọn bởi `doc_lang`).

Mẫu dùng 3 cú pháp, ⛔ thư viện ngoài:
  {{KEY}}                          thay bằng giá trị
  {{#level lite standard}}…{{/level}}   giữ khi mức hiện tại thuộc danh sách
  {{#pack i18n}}…{{/pack}}               giữ khi gói bật
Tệp đã tồn tại ⇒ BỎ QUA (⛔ ghi đè việc của người dùng), trừ khi `force=True`.
"""
from __future__ import annotations

import datetime as dt
import re
from importlib import resources
from pathlib import Path

from gatekit.config import CONFIG_NAME, Config, from_dict

TEMPLATE_LANGS = ("vi", "en")

AGENT_ROLE = {
    "vi": {
        "chief-architect": ("Kiến trúc", "gate tổng: pha/lát, kiến trúc, dịch vụ, DDL, sửa quy trình, kết phiên, GIAO VIỆC"),
        "qa-lead": ("QA", "test có răng: ca âm, đột biến theo vùng, manifest, ngân sách"),
        "security-lead": ("Bảo mật", "vùng K: bí mật, khoá, xác thực, phân quyền, kiểm toán"),
        "ux-gate": ("Sản phẩm/UX", "thao tác an toàn, trạng thái màn, thuật ngữ, hợp đồng FE"),
        "compliance-officer": ("Tuân thủ", "quyền được phép, đồng ý, dữ liệu cá nhân, điều khoản bên thứ ba"),
        "product-director": ("Giám đốc sản phẩm (TẠO, ⛔ gate)", "BE: làm gì, quy tắc, máy trạng thái, hợp đồng API, nghiệm thu"),
        "design-director": ("Giám đốc thiết kế (TẠO, ⛔ gate)", "FE: hệ thiết kế, màn, trạng thái, câu chữ"),
        "execution-lead": ("Đường tiền (gói fintech)", "vùng T: ý định → định tuyến → bộ dịch, sổ lệnh, tiền"),
        "quant-lead": ("Công thức (gói fintech)", "vùng F: đúng sách, số vàng độc lập, tất định"),
        "domain-auditor": ("Kiểm toán công thức (gói fintech)", "chỉ đọc: tái hiện số độc lập, phân loại ĐÚNG/SAI/BỊA/CHẾT"),
        "data-integrity": ("Dữ liệu (gói data_pipeline)", "nguồn đã chốt, hổng/trùng, phân vùng, giới hạn gọi API"),
        "checkout-lead": ("Thanh toán & đơn hàng (gói ecommerce)", "vùng T: máy trạng thái đơn, thanh toán, webhook, hoàn tiền, giữ hàng"),
        "pricing-lead": ("Giá & khuyến mãi (gói ecommerce)", "vùng F: giá, giảm giá, thuế, phí ship, làm tròn, tiền tệ"),
    },
    "en": {
        "chief-architect": ("Architecture", "master gate: phases/slices, architecture, services, DDL, process changes, session close, ASSIGNMENT"),
        "qa-lead": ("QA", "tests with teeth: negative cases, mutants by zone, manifests, budgets"),
        "security-lead": ("Security", "zone K: secrets, keys, authentication, authorization, audit"),
        "ux-gate": ("Product/UX", "safe operation, screen states, terminology, FE contract"),
        "compliance-officer": ("Compliance", "what is permitted, consent, personal data, third-party terms"),
        "product-director": ("Product director (CREATOR, not a gate)", "BE: what, rules, state machines, API contracts, acceptance"),
        "design-director": ("Design director (CREATOR, not a gate)", "FE: design system, screens, states, copy"),
        "execution-lead": ("Money path (fintech pack)", "zone T: intent → routing → translator, order book, money"),
        "quant-lead": ("Formulas (fintech pack)", "zone F: true to the book, independent golden numbers, determinism"),
        "domain-auditor": ("Formula audit (fintech pack)", "read-only: independent recomputation, RIGHT/WRONG/INVENTED/DEAD"),
        "data-integrity": ("Data (data_pipeline pack)", "finalised sources, gaps/duplicates, partitioning, API rate limits"),
        "checkout-lead": ("Checkout & orders (ecommerce pack)", "zone T: order state machine, payments, webhooks, refunds, stock reservation"),
        "pricing-lead": ("Pricing & promotions (ecommerce pack)", "zone F: prices, discounts, tax, shipping fees, rounding, currency"),
    },
}
WORDS = {
    "vi": {"packs": " · gói ", "ledger_row": "sổ làn `{name}` (`{prefix}-L/D/C/N`) | mỗi phán"},
    "en": {"packs": " · packs ", "ledger_row": "lane `{name}` ledgers (`{prefix}-L/D/C/N`) | every verdict"},
}
GATES = ["chief-architect", "qa-lead", "security-lead", "ux-gate", "compliance-officer",
         "execution-lead", "quant-lead", "data-integrity", "checkout-lead", "pricing-lead"]
LITE_SKIP = {"docs/governance/SESSION_PROTOCOL.md", "docs/governance/COORDINATOR_PROMPT.md"}


def _undot(rel: str) -> str:
    """Mẫu lưu `dot-x/` thay `.x/` — setuptools bỏ thư mục chấm khỏi wheel."""
    return "/".join("." + part[4:] if part.startswith("dot-") else part for part in rel.split("/"))


def doc_lang(cfg: Config) -> str:
    """Ngôn ngữ bộ mẫu: `project.docs_language` nếu khai, ngược lại `project.language` nếu có mẫu, ngược lại `en`."""
    explicit = cfg.data["project"].get("docs_language") or ""
    if explicit:
        return explicit
    lang = cfg.data["project"]["language"]
    return lang if lang in TEMPLATE_LANGS else "en"


def _tpl(lang: str) -> Path:
    return Path(str(resources.files("gatekit") / "templates" / lang))


def _packs_root() -> Path:
    return Path(str(resources.files("gatekit") / "packs"))


TOML_TEXT = {
    "vi": {
        "head": "# gatekit.toml — NGUỒN DUY NHẤT của tham số quy trình. Sửa tệp này = sửa quy trình ⇒ qua gate chief-architect.",
        "language": "ngôn ngữ agent giao tiếp",
        "docs_language": "ngôn ngữ bộ mẫu tài liệu (vi | en); để trống = theo language",
        "prod": "mã SẢN XUẤT — commit chạm 0 tệp khớp ⇒ lát QUẢN TRỊ",
        "max_code_slices": "lát MÃ đang viết cùng lúc",
        "id_regex": 'mã lát trong tiêu đề commit: "feat: … [S-12]"',
        "zones": "Vùng rủi ro: quyết HÌNH THỨC kiểm (GATE_PROTOCOL §4). Khai theo mã thật của dự án.",
        "T": "thao tác KHÔNG đảo ngược: gửi lệnh, ghi tiền, xoá dữ liệu người dùng",
        "K": "bí mật · khoá · xác thực · quyền xem",
        "F": "công thức · quy tắc quyết định nghiệp vụ",
        "eg": "vd", "grep": "regex trên dòng THÊM của diff",
        "hotpath": "đường nóng có bench (GATE_PROTOCOL §5)",
        "eco_money": "từ đánh dấu TÊN TIỀN cho guard money_float (mặc định: price, amount, total, tax, fee…)",
        "eco_nonmoney": "từ loại trừ (weight, qty, rate, percent…)",
        "eco_card": "regex tên trường dữ liệu thẻ cho guard pci_scope",
    },
    "en": {
        "head": "# gatekit.toml — the SINGLE SOURCE of process parameters. Editing this file = changing the process ⇒ chief-architect gate.",
        "language": "language agents communicate in",
        "docs_language": "language of the document templates (vi | en); empty = follow language",
        "prod": "PRODUCTION code — a commit touching 0 matching files ⇒ GOVERNANCE slice",
        "max_code_slices": "CODE slices being written at the same time",
        "id_regex": 'slice id in the commit subject: "feat: … [S-12]"',
        "zones": "Risk zones: decide the FORM of testing (GATE_PROTOCOL §4). Declare them for the project's real code.",
        "T": "IRREVERSIBLE actions: sending orders, booking money, deleting user data",
        "K": "secrets · keys · authentication · data visibility",
        "F": "formulas · business decision rules",
        "eg": "e.g.", "grep": "regex over ADDED lines of the diff",
        "hotpath": "hot paths that have a bench (GATE_PROTOCOL §5)",
        "eco_money": "words marking a MONEY name for the money_float guard (default: price, amount, total, tax, fee…)",
        "eco_nonmoney": "words that exclude it (weight, qty, rate, percent…)",
        "eco_card": "regex of card-data field names for the pci_scope guard",
    },
}


def config_toml(name: str, level: str, packs: list[str], language: str, lanes: list[tuple[str, str]],
                docs_language: str = "") -> str:
    t = TOML_TEXT[docs_language or (language if language in TEMPLATE_LANGS else "en")]
    lane_lines = "\n".join(
        f'[[ledger.lanes]]\nname = "{n}"\nprefix = "{p}"\ndir = "docs/ledger{"" if i == 0 else "/" + n}"\n'
        for i, (n, p) in enumerate(lanes))
    packs_s = ", ".join(f'"{p}"' for p in packs)
    return f'''{t["head"]}

[project]
name = "{name}"
level = "{level}"          # lite | standard | regulated
language = "{language}"    # {t["language"]}
docs_language = "{docs_language}"   # {t["docs_language"]}
packs = [{packs_s}]        # i18n · multi_provider · legacy_upgrade · postgres · fintech · data_pipeline · ecommerce

[paths]
# {t["prod"]}
prod = ['^src/', '^app/']

[session]
max_code_slices = 5        # {t["max_code_slices"]}
max_agents = 8
worktree_per_slice = true
governance_slice_max = 1
code_slices_after_governance = 2

[slices]
id_regex = '\\[(?P<id>[A-Za-z][\\w.\\-]*)\\]'   # {t["id_regex"]}

[ledger]
range_primary = 20
range_co = 10
roll_keep_days = 60

{lane_lines}
# ── {t["zones"]} ──
[zones.T]
label = "{t["T"]}"
paths = []                 # {t["eg"]} ['^src/(payments|orders)/', '^src/billing/ledger\\.py$']
grep = []                  # {t["grep"]}

[zones.K]
label = "{t["K"]}"
paths = ['(^|/)(auth|identity|secrets?|permissions?)/']
grep = ['\\b(GRANT|REVOKE|POLICY)\\b']

[zones.F]
label = "{t["F"]}"
paths = []                 # {t["eg"]} ['^src/pricing/', '^src/indicators/']
grep = []

[tests]
manifests = ["tests/manifest.tsv"]

[tests.budget]
tier1_seconds = 180
mutant_seconds = 6
mutants_total_seconds = 600

[hotpath]
paths = []                 # {t["hotpath"]}
ratio = 1.25
runs = 5
max_seconds = 180

[packs.i18n]
dir = "locales"
langs = ["vi", "en"]

[packs.multi_provider]
adapter_dir = "src/providers/{{name}}"
partition_column = "provider"
# providers = {{ stripe = ["stripe"], paypal = ["paypal"] }}

[packs.legacy_upgrade]
legacy_modules = []        # {t["eg"]} ["legacy_app", "@old/core"]
label_prefix = "source: LEGACY@"

[packs.ecommerce]
# money_words = [...]       # {t["eco_money"]}
# non_money_words = [...]   # {t["eco_nonmoney"]}
# card_names = '…'          # {t["eco_card"]}

[packs.postgres]
migrations_dir = "db/migrations"
lock_file = "db/migrations.lock"
'''


def render(text: str, cfg: Config, extra: dict[str, str] | None = None) -> str:
    level, packs = cfg.level, set(cfg.packs)

    def lvl(m: re.Match) -> str:
        return m.group(2) if level in m.group(1).split() else ""

    def pk(m: re.Match) -> str:
        return m.group(2) if m.group(1) in packs else ""

    text = re.sub(r"\{\{#level ([^}]+)\}\}(.*?)\{\{/level\}\}", lvl, text, flags=re.S)
    text = re.sub(r"\{\{#pack (\w+)\}\}(.*?)\{\{/pack\}\}", pk, text, flags=re.S)
    values = values_for(cfg)
    values.update(extra or {})
    for k, v in values.items():
        text = text.replace("{{" + k + "}}", v)
    left = re.findall(r"\{\{[A-Z_#/][^}]*\}\}", text)
    if left:
        raise ValueError(f"mẫu còn chỗ giữ chưa thay: {sorted(set(left))}")
    return text


def agent_names(cfg: Config) -> list[str]:
    names = cfg.agents()
    if "fintech" in cfg.packs:
        names += ["execution-lead", "quant-lead", "domain-auditor"]
    if "data_pipeline" in cfg.packs:
        names += ["data-integrity"]
    if "ecommerce" in cfg.packs:
        names += ["checkout-lead", "pricing-lead"]
    return names


def values_for(cfg: Config) -> dict[str, str]:
    d = cfg.data
    lang = doc_lang(cfg)
    roles, words = AGENT_ROLE[lang], WORDS[lang]
    lanes = cfg.lanes()
    agents = agent_names(cfg)
    rows = "\n".join(f"| {roles[a][0]} | `{a}` | {roles[a][1]} |" for a in agents)
    ledger_rows = "" if cfg.level == "lite" else "".join(
        f"| `{ln['dir']}/{{LEDGER,DECISIONS,DEBT}}.md` | {words['ledger_row'].format(name=ln['name'], prefix=ln['prefix'])} |\n"
        for ln in lanes)
    i18n = cfg.pack("i18n")
    common = (_tpl(lang) / "partials" / "gate_common.md").read_text(encoding="utf-8")
    return {
        "PROJECT": d["project"]["name"],
        "LEVEL": cfg.level,
        "LANGUAGE": d["project"]["language"],
        "PACKS_SUFFIX": (words["packs"] + ", ".join(cfg.packs)) if cfg.packs else "",
        "DATE": dt.date.today().isoformat(),
        "MAX_CODE_SLICES": str(d["session"]["max_code_slices"]),
        "MAX_AGENTS": str(d["session"]["max_agents"]),
        "WORKTREE": "true" if d["session"]["worktree_per_slice"] else "false",
        "GOV_MAX": str(d["session"]["governance_slice_max"]),
        "CODE_AFTER_GOV": str(d["session"]["code_slices_after_governance"]),
        "RANGE_PRIMARY": str(d["ledger"]["range_primary"]),
        "RANGE_CO": str(d["ledger"]["range_co"]),
        "LANES_INLINE": " · ".join(f"`{ln['name']}` = `{ln['prefix']}` (`{ln['dir']}`)" for ln in lanes),
        "AGENTS_TABLE": rows,
        "GATES_INLINE": " · ".join(a for a in agents if a in GATES),
        "LEDGER_ROWS": ledger_rows,
        "MAX_ONE_OFF": str(d["mutants"]["max_one_off"]),
        "HOT_RUNS": str(d["hotpath"]["runs"]),
        "HOT_RATIO": str(d["hotpath"]["ratio"]),
        "HOT_MAX": str(d["hotpath"]["max_seconds"]),
        "T1": str(d["tests"]["budget"]["tier1_seconds"]),
        "MUT1": str(d["tests"]["budget"]["mutant_seconds"]),
        "MUTALL": str(d["tests"]["budget"]["mutants_total_seconds"]),
        "I18N_DIR": i18n["dir"],
        "I18N_LANGS": " · ".join(f"`{x}`" for x in i18n["langs"]),
        "LEGACY_LABEL": cfg.pack("legacy_upgrade")["label_prefix"],
        "GATE_COMMON": common.rstrip("\n"),
    }


SEED_PATTERNS = ("test_*.py", "*_test.py", "*_test.go", "*.test.ts", "*.test.tsx", "*.spec.ts", "*.spec.tsx",
                 "*.test.js", "*.spec.js", "*.test.jsx")


def seed_manifest(cfg: Config) -> str:
    """Dòng manifest cho test ĐANG CÓ trong repo (mỗi thư mục × mẫu tên một glob) — để lượt `check` đầu không ĐỎ
    `test_wiring` vì những test chạy được từ trước. Test thêm về sau vẫn phải khai tay (đó là việc của guard)."""
    import fnmatch
    from gatekit.guards._common import iter_files
    globs = [re.compile(g) for g in cfg["tests"]["test_globs"]]
    lane = cfg.lanes()[0]["name"]
    lines: list[str] = []
    for rel in iter_files(cfg):
        if not any(g.search(rel) for g in globs):
            continue
        d, _, name = rel.rpartition("/")
        pat = next((x for x in SEED_PATTERNS if fnmatch.fnmatchcase(name, x)), name)
        entry = f"{d}/{pat}" if d else pat
        line = f"{entry}\t{lane}\t1\tgatekit init\n"
        if line not in lines:
            lines.append(line)
    return "".join(lines)


def plan(cfg: Config) -> dict[str, str]:
    """Đường dẫn đích → nội dung đã render."""
    out: dict[str, str] = {}
    lang = doc_lang(cfg)
    files = _tpl(lang) / "files"
    for p in sorted(files.rglob("*")):
        if not p.is_file():
            continue
        rel = _undot(p.relative_to(files).as_posix())
        if cfg.level == "lite" and rel in LITE_SKIP:
            continue
        out[rel] = render(p.read_text(encoding="utf-8"), cfg)
        if rel == "tests/manifest.tsv":
            out[rel] += seed_manifest(cfg)
    for a in agent_names(cfg):
        src = _tpl(lang) / "agents" / f"{a}.md"
        if not src.exists():
            src = next(_packs_root().glob(f"*/{lang}/agents/{a}.md"))
        out[f".claude/agents/{a}.md"] = render(src.read_text(encoding="utf-8"), cfg)
    for pack in cfg.packs:
        pf = _packs_root() / pack / lang / "files"
        if pf.is_dir():
            for p in sorted(pf.rglob("*")):
                if p.is_file():
                    out[p.relative_to(pf).as_posix()] = render(p.read_text(encoding="utf-8"), cfg)
    if "i18n" in cfg.packs:
        spec = cfg.pack("i18n")
        for lang in spec["langs"]:
            out[f"{spec['dir']}/{lang}/common.json"] = '{\n  "common.ok": "OK"\n}\n'
    if cfg.level != "lite":
        for ln in cfg.lanes():
            extra = {"LANE_NAME": ln["name"], "LANE_PREFIX": ln["prefix"]}
            for f in ("LEDGER.md", "DECISIONS.md", "DEBT.md"):
                out[f"{ln['dir']}/{f}"] = render((_tpl(lang) / "lane" / f).read_text(encoding="utf-8"), cfg, extra)
    return out


def init(root: Path, *, name: str, level: str, packs: list[str], language: str = "vi",
         lanes: list[tuple[str, str]] | None = None, force: bool = False,
         docs_language: str = "") -> tuple[list[str], list[str]]:
    root = root.resolve()
    lanes = lanes or [("core", "P")]
    written, skipped = [], []
    cfg_path = root / CONFIG_NAME
    if cfg_path.exists() and not force:
        skipped.append(CONFIG_NAME)
    else:
        cfg_path.write_text(config_toml(name, level, packs, language, lanes, docs_language), encoding="utf-8")
        written.append(CONFIG_NAME)
    import tomllib
    with cfg_path.open("rb") as f:
        cfg = from_dict(root, tomllib.load(f))
    for rel, body in plan(cfg).items():
        dst = root / rel
        if dst.exists() and not force:
            skipped.append(rel)
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(body, encoding="utf-8")
        if rel.startswith(".gatekit/hooks/"):
            dst.chmod(0o755)
        written.append(rel)
    return written, skipped
