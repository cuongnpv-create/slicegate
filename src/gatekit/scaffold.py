"""`gatekit init` — dựng bộ quy trình vào một repo từ mẫu.

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

AGENT_ROLE = {
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
}
GATES = ["chief-architect", "qa-lead", "security-lead", "ux-gate", "compliance-officer",
         "execution-lead", "quant-lead", "data-integrity"]
LITE_SKIP = {"docs/governance/SESSION_PROTOCOL.md", "docs/governance/COORDINATOR_PROMPT.md"}


def _undot(rel: str) -> str:
    """Mẫu lưu `dot-x/` thay `.x/` — setuptools bỏ thư mục chấm khỏi wheel."""
    return "/".join("." + part[4:] if part.startswith("dot-") else part for part in rel.split("/"))


def _tpl() -> Path:
    return Path(str(resources.files("gatekit") / "templates"))


def _packs_root() -> Path:
    return Path(str(resources.files("gatekit") / "packs"))


def config_toml(name: str, level: str, packs: list[str], language: str, lanes: list[tuple[str, str]]) -> str:
    lane_lines = "\n".join(
        f'[[ledger.lanes]]\nname = "{n}"\nprefix = "{p}"\ndir = "docs/ledger{"" if i == 0 else "/" + n}"\n'
        for i, (n, p) in enumerate(lanes))
    packs_s = ", ".join(f'"{p}"' for p in packs)
    return f'''# gatekit.toml — NGUỒN DUY NHẤT của tham số quy trình. Sửa tệp này = sửa quy trình ⇒ qua gate chief-architect.

[project]
name = "{name}"
level = "{level}"          # lite | standard | regulated
language = "{language}"    # ngôn ngữ agent giao tiếp
packs = [{packs_s}]        # i18n · multi_provider · legacy_upgrade · postgres · fintech · data_pipeline

[paths]
# mã SẢN XUẤT — commit chạm 0 tệp khớp ⇒ lát QUẢN TRỊ
prod = ['^src/', '^app/']

[session]
max_code_slices = 5        # lát MÃ đang viết cùng lúc
max_agents = 8
worktree_per_slice = true
governance_slice_max = 1
code_slices_after_governance = 2

[slices]
id_regex = '\\[(?P<id>[A-Za-z][\\w.\\-]*)\\]'   # mã lát trong tiêu đề commit: "feat: … [S-12]"

[ledger]
range_primary = 20
range_co = 10
roll_keep_days = 60

{lane_lines}
# ── Vùng rủi ro: quyết HÌNH THỨC kiểm (GATE_PROTOCOL §4). Khai theo mã thật của dự án. ──
[zones.T]
label = "thao tác KHÔNG đảo ngược: gửi lệnh, ghi tiền, xoá dữ liệu người dùng"
paths = []                 # vd ['^src/(payments|orders)/', '^src/billing/ledger\\.py$']
grep = []                  # regex trên dòng THÊM của diff

[zones.K]
label = "bí mật · khoá · xác thực · quyền xem"
paths = ['(^|/)(auth|identity|secrets?|permissions?)/']
grep = ['\\b(GRANT|REVOKE|POLICY)\\b']

[zones.F]
label = "công thức · quy tắc quyết định nghiệp vụ"
paths = []                 # vd ['^src/pricing/', '^src/indicators/']
grep = []

[tests]
manifests = ["tests/manifest.tsv"]

[tests.budget]
tier1_seconds = 180
mutant_seconds = 6
mutants_total_seconds = 600

[hotpath]
paths = []                 # đường nóng có bench (GATE_PROTOCOL §5)
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
legacy_modules = []        # vd ["legacy_app", "@old/core"]
label_prefix = "source: LEGACY@"

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
    return names


def values_for(cfg: Config) -> dict[str, str]:
    d = cfg.data
    lanes = cfg.lanes()
    agents = agent_names(cfg)
    rows = "\n".join(f"| {AGENT_ROLE[a][0]} | `{a}` | {AGENT_ROLE[a][1]} |" for a in agents)
    ledger_rows = "" if cfg.level == "lite" else "".join(
        f"| `{ln['dir']}/{{LEDGER,DECISIONS,DEBT}}.md` | sổ làn `{ln['name']}` (`{ln['prefix']}-L/D/C/N`) | mỗi phán |\n"
        for ln in lanes)
    i18n = cfg.pack("i18n")
    common = (_tpl() / "partials" / "gate_common.md").read_text(encoding="utf-8")
    return {
        "PROJECT": d["project"]["name"],
        "LEVEL": cfg.level,
        "LANGUAGE": d["project"]["language"],
        "PACKS_SUFFIX": (" · gói " + ", ".join(cfg.packs)) if cfg.packs else "",
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


def plan(cfg: Config) -> dict[str, str]:
    """Đường dẫn đích → nội dung đã render."""
    out: dict[str, str] = {}
    files = _tpl() / "files"
    for p in sorted(files.rglob("*")):
        if not p.is_file():
            continue
        rel = _undot(p.relative_to(files).as_posix())
        if cfg.level == "lite" and rel in LITE_SKIP:
            continue
        out[rel] = render(p.read_text(encoding="utf-8"), cfg)
    for a in agent_names(cfg):
        src = _tpl() / "agents" / f"{a}.md"
        if not src.exists():
            src = next(_packs_root().glob(f"*/agents/{a}.md"))
        out[f".claude/agents/{a}.md"] = render(src.read_text(encoding="utf-8"), cfg)
    for pack in cfg.packs:
        pf = _packs_root() / pack / "files"
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
                out[f"{ln['dir']}/{f}"] = render((_tpl() / "lane" / f).read_text(encoding="utf-8"), cfg, extra)
    return out


def init(root: Path, *, name: str, level: str, packs: list[str], language: str = "vi",
         lanes: list[tuple[str, str]] | None = None, force: bool = False) -> tuple[list[str], list[str]]:
    root = root.resolve()
    lanes = lanes or [("core", "P")]
    written, skipped = [], []
    cfg_path = root / CONFIG_NAME
    if cfg_path.exists() and not force:
        skipped.append(CONFIG_NAME)
    else:
        cfg_path.write_text(config_toml(name, level, packs, language, lanes), encoding="utf-8")
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
