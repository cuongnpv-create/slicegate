"""Đọc `gatekit.toml` — NGUỒN DUY NHẤT của mọi tham số dự án (vùng rủi ro, làn, ngân sách test, gói ngành).

Luật đổi nhiều lần ở dự án gốc (số lát song song, worktree hay trunk, ngân sách test…) là THAM SỐ ở đây, ⛔ chữ cứng trong tài liệu.
"""
from __future__ import annotations

import copy
import re
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from gatekit.messages import t

CONFIG_NAME = "gatekit.toml"
LEVELS = ("lite", "standard", "regulated")

DEFAULTS: dict[str, Any] = {
    "project": {
        "name": "Project",
        "level": "standard",
        "language": "vi",
        "docs_language": "",   # rỗng = theo language nếu có mẫu, ngược lại "en"
        "packs": [],
    },
    "paths": {
        # mã sản xuất — commit chạm 0 tệp khớp ⇒ lát QUẢN TRỊ (slice_quota)
        "prod": [r"^src/", r"^app/", r"^backend/src/", r"^frontend/src/"],
        "code_ext": [".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".java", ".kt", ".rs", ".cs"],
        "exclude": [r"(^|/)node_modules/", r"(^|/)\.venv/", r"(^|/)vendor/", r"(^|/)dist/", r"(^|/)build/",
                    r"^\.claude/worktrees/"],
    },
    "session": {
        "max_code_slices": 5,
        "max_agents": 8,
        "worktree_per_slice": True,
        "governance_slice_max": 1,
        "code_slices_after_governance": 2,
    },
    "slices": {
        # mã lát trong tiêu đề commit, vd "feat(auth): đăng nhập [S-12]"
        "id_regex": r"\[(?P<id>[A-Za-z][\w.\-]*)\]",
    },
    "ledger": {
        "lanes": [{"name": "core", "prefix": "P", "dir": "docs/ledger"}],
        "range_primary": 20,
        "range_co": 10,
        "roll_keep_days": 60,
    },
    "zones": {
        "T": {"label": "thao tác KHÔNG đảo ngược được: gửi lệnh, ghi tiền, xoá dữ liệu người dùng",
              "paths": [], "grep": []},
        "K": {"label": "bí mật · khoá · xác thực · quyền xem",
              "paths": [r"(^|/)(auth|identity|secrets?|permissions?)/"], "grep": [r"\b(GRANT|REVOKE|POLICY)\b"]},
        "F": {"label": "công thức · quy tắc quyết định nghiệp vụ",
              "paths": [], "grep": []},
    },
    "tests": {
        "manifests": ["tests/manifest.tsv"],
        # test_*.py chỉ tính trong thư mục test (src/…/test_wiring.py là mã, ⛔ test); *_test.go, *.test.ts tính mọi nơi
        "test_globs": [r"(^|/)tests?/(.*/)?test_[^/]*\.py$", r"(^|/)tests?/(.*/)?[^/]*_test\.py$",
                       r"_test\.go$", r"\.(test|spec)\.(ts|tsx|js|jsx)$"],
        "budget": {"tier1_seconds": 180, "mutant_seconds": 6, "mutants_total_seconds": 600},
    },
    "mutants": {"dir": "mutants", "max_one_off": 3},
    "hotpath": {"paths": [], "ratio": 1.25, "runs": 5, "max_seconds": 180},
    "naming": {"baseline": ".gatekit/naming_baseline.txt"},
    "secrets": {
        "name_regex": r"(?i)(secret|passw(or)?d|pwd|token|api_?key|private_?key|mnemonic|seed_phrase|cipher_key)",
        "allowlist": ".gatekit/secret_allowlist.txt",
    },
    "guard_log": "docs/governance/GUARD_CATCH_LOG.tsv",
    "packs": {
        "i18n": {"dir": "locales", "langs": ["vi", "en"]},
        "multi_provider": {"adapter_dir": "src/providers/{name}", "providers": {},
                           "partition_column": "provider", "sql_globs": [r"\.sql$"]},
        "legacy_upgrade": {"legacy_modules": [], "label_prefix": "source: LEGACY@"},
        "ecommerce": {
            "money_words": ["price", "prices", "amount", "amounts", "total", "subtotal", "tax", "vat", "fee", "fees",
                            "discount", "balance", "cost", "refund", "charge", "payout", "tip", "shipping"],
            "non_money_words": ["weight", "qty", "quantity", "count", "rate", "percent", "pct", "ratio", "score",
                                "items", "pages", "size", "length", "width", "height", "days", "seconds", "ms"],
            "card_names": r"(?i)(card_?number|card_?no|pan|cvv2?|cvc2?|card_?cvc|card_?cvv|track_?data|track[12]|magstripe)",
        },
        "healthcare": {
            "phi_words": ["patient", "patients", "dob", "birth", "birthdate", "birthday", "ssn", "mrn", "diagnosis",
                          "diagnoses", "icd", "prescription", "prescriptions", "medication", "medications", "allergy",
                          "allergies", "insurance", "symptom", "symptoms", "treatment", "treatments", "clinical", "lab",
                          "vitals", "pregnancy", "hiv", "genetic", "genome"],
            "non_phi_words": ["id", "ids", "uuid", "count", "counts", "ref", "version", "flag", "enabled", "type"],
        },
        "logistics": {
            "quantity_words": ["weight", "mass", "distance", "width", "height", "depth", "girth", "volume", "temperature",
                               "payload"],
            "unit_words": ["kg", "g", "gram", "grams", "mg", "lb", "lbs", "oz", "t", "ton", "tons", "tonne", "tonnes",
                           "mm", "cm", "m", "km", "in", "inch", "inches", "ft", "yd", "mi", "mile", "miles", "nmi",
                           "l", "ml", "liter", "liters", "litre", "litres", "m3", "cbm", "cuft", "gal",
                           "c", "f", "k", "celsius", "fahrenheit", "kelvin", "px", "pt", "em", "rem", "dp", "chars", "bytes"],
            "non_quantity_words": ["pct", "percent", "ratio", "factor", "divisor", "unit", "units", "uom", "class",
                                   "type", "id", "label", "name", "band", "tier", "mode", "items", "count", "len",
                                   "line", "text", "string", "list", "array", "queue", "buffer", "key"],
            "unit_skip": [r"\.(tsx|jsx)$"],
        },
        "saas_multitenant": {
            "tenant_column": "tenant_id",
            "migrations_regex": r"(^|/)migrations?/",
            "require_rls": False,
        },
        "postgres": {"migrations_dir": "db/migrations", "lock_file": "db/migrations.lock",
                     "pattern": r"^(?P<n>\d{4})_[\w\-]+\.sql$"},
    },
}

LEVEL_AGENTS = {
    "lite": ["chief-architect", "qa-lead"],
    "standard": ["chief-architect", "qa-lead", "security-lead", "product-director", "design-director", "ux-gate"],
    "regulated": ["chief-architect", "qa-lead", "security-lead", "product-director", "design-director", "ux-gate",
                  "compliance-officer"],
}


def _merge(base: dict, over: dict) -> dict:
    out = copy.deepcopy(base)
    for k, v in over.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _merge(out[k], v)
        else:
            out[k] = copy.deepcopy(v)
    return out


class ConfigError(ValueError):
    pass


@dataclass
class Config:
    root: Path
    data: dict = field(default_factory=dict)

    def __getitem__(self, key: str) -> Any:
        return self.data[key]

    @property
    def level(self) -> str:
        return self.data["project"]["level"]

    @property
    def packs(self) -> list[str]:
        return list(self.data["project"]["packs"])

    def pack(self, name: str) -> dict:
        return self.data["packs"].get(name, {})

    def excluded(self, rel: str) -> bool:
        return any(re.search(p, rel) for p in self.data["paths"]["exclude"])

    def is_prod(self, rel: str) -> bool:
        return any(re.search(p, rel) for p in self.data["paths"]["prod"])

    def lanes(self) -> list[dict]:
        return list(self.data["ledger"]["lanes"])

    def agents(self) -> list[str]:
        return list(LEVEL_AGENTS[self.level])


def validate(data: dict) -> None:
    lvl = data["project"]["level"]
    if lvl not in LEVELS:
        raise ConfigError(t("config.level", value=lvl, allowed=LEVELS))
    dl = data["project"].get("docs_language", "")
    if dl not in ("", "vi", "en"):
        raise ConfigError(t("config.docs_language", value=dl))
    prefixes = [ln["prefix"] for ln in data["ledger"]["lanes"]]
    if len(set(prefixes)) != len(prefixes):
        raise ConfigError(t("config.dup_prefix", prefixes=prefixes))
    for z, spec in data["zones"].items():
        for rx in list(spec.get("paths", [])) + list(spec.get("grep", [])):
            try:
                re.compile(rx)
            except re.error as e:
                raise ConfigError(t("config.bad_regex", zone=z, rx=rx, err=e)) from e
    known = set(DEFAULTS["packs"]) | {"fintech", "data_pipeline"}
    for p in data["project"]["packs"]:
        if p not in known:
            raise ConfigError(t("config.unknown_pack", pack=p, known=sorted(known)))


def load(root: Path | str = ".", *, required: bool = True) -> Config:
    root = Path(root).resolve()
    path = root / CONFIG_NAME
    over: dict = {}
    if path.exists():
        with path.open("rb") as f:
            over = tomllib.load(f)
    elif required:
        raise ConfigError(t("config.missing", path=path))
    data = _merge(DEFAULTS, over)
    validate(data)
    return Config(root=root, data=data)


def from_dict(root: Path | str, over: dict) -> Config:
    data = _merge(DEFAULTS, over)
    validate(data)
    return Config(root=Path(root).resolve(), data=data)
