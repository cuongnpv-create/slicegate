"""Guard `locale_parity` (gói i18n) — catalog bản dịch đủ và khớp giữa mọi ngôn ngữ.

Bố cục: `<packs.i18n.dir>/<lang>/<namespace>.json`, mỗi tệp là object PHẲNG `{"<namespace>.<key>": "chuỗi"}`.
Luật (baseline 0): đúng tập ngôn ngữ khai · cùng tập tệp · cùng tập khoá · khoá mang tiền tố namespace ·
⛔ chuỗi rỗng · tham số `{x}` giống nhau giữa các ngôn ngữ.
"""
from __future__ import annotations

import json
import re

from slicegate.config import Config
from slicegate.guards._common import Finding, expect, fixture
from slicegate.messages import t

NAME = "locale_parity"
PACK = "i18n"
FAST = True
DEFECT = {"vi": "người dùng thấy khoá thô / chuỗi rỗng / sai tham số ở ngôn ngữ chưa dịch đủ",
          "en": "users see raw keys / empty strings / wrong parameters in an incompletely translated language"}

_PARAM = re.compile(r"\{(\w+)\}")


def check(cfg: Config) -> list[Finding]:
    spec = cfg.pack("i18n")
    base = cfg.root / spec["dir"]
    langs = list(spec["langs"])
    found: list[Finding] = []
    if not base.is_dir():
        return [Finding(NAME, spec["dir"], 0, t("locale.no_dir"))]
    present = sorted(p.name for p in base.iterdir() if p.is_dir())
    for extra in sorted(set(present) - set(langs)):
        found.append(Finding(NAME, f"{spec['dir']}/{extra}", 0, t("locale.extra_lang", lang=extra)))
    cat: dict[str, dict[str, dict[str, str]]] = {}
    for lang in langs:
        d = base / lang
        if not d.is_dir():
            found.append(Finding(NAME, f"{spec['dir']}/{lang}", 0, t("locale.missing_lang")))
            continue
        cat[lang] = {}
        for f in sorted(d.glob("*.json")):
            rel = f"{spec['dir']}/{lang}/{f.name}"
            try:
                obj = json.loads(f.read_text(encoding="utf-8"))
            except json.JSONDecodeError as e:
                found.append(Finding(NAME, rel, e.lineno, t("locale.bad_json", msg=e.msg)))
                continue
            if not isinstance(obj, dict) or any(not isinstance(v, str) for v in obj.values()):
                found.append(Finding(NAME, rel, 0, t("locale.not_flat")))
                continue
            ns = f.stem
            for k, v in obj.items():
                if not k.startswith(ns + "."):
                    found.append(Finding(NAME, rel, 0, t("locale.prefix", key=k, ns=ns)))
                if not v.strip():
                    found.append(Finding(NAME, rel, 0, t("locale.empty", key=k)))
            cat[lang][ns] = obj
    if not cat:
        return found
    ref_lang = langs[0] if langs[0] in cat else next(iter(cat))
    for lang, nss in cat.items():
        if lang == ref_lang:
            continue
        ref = cat[ref_lang]
        for ns in sorted(set(ref) | set(nss)):
            rel = f"{spec['dir']}/{lang}/{ns}.json"
            if ns not in nss:
                found.append(Finding(NAME, rel, 0, t("locale.missing_file", ref=ref_lang)))
                continue
            if ns not in ref:
                found.append(Finding(NAME, rel, 0, t("locale.extra_file", ref=ref_lang)))
                continue
            for k in sorted(set(ref[ns]) ^ set(nss[ns])):
                key = "locale.missing_key" if k in ref[ns] else "locale.extra_key"
                found.append(Finding(NAME, rel, 0, t(key, key=k, ref=ref_lang)))
            for k in sorted(set(ref[ns]) & set(nss[ns])):
                if set(_PARAM.findall(ref[ns][k])) != set(_PARAM.findall(nss[ns][k])):
                    found.append(Finding(NAME, rel, 0, t("locale.params", key=k, ref=ref_lang)))
    return found


def selftest() -> list[str]:
    errs: list[str] = []
    on = {"project": {"packs": ["i18n"]}}
    good = {"locales/vi/auth.json": '{"auth.hello": "Chào {name}"}', "locales/en/auth.json": '{"auth.hello": "Hi {name}"}'}
    with fixture(good, on) as cfg:
        expect(errs, "khớp", check(cfg), red=False)
    with fixture({**good, "locales/en/auth.json": '{"auth.hello": "Hi"}'}, on) as cfg:
        expect(errs, "tham số lệch", check(cfg), red=True)
    with fixture({**good, "locales/en/auth.json": '{}'}, on) as cfg:
        expect(errs, "thiếu khoá", check(cfg), red=True)
    with fixture({**good, "locales/en/auth.json": '{"auth.hello": " "}'}, on) as cfg:
        expect(errs, "chuỗi rỗng", check(cfg), red=True)
    with fixture({"locales/vi/auth.json": '{"auth.hello": "Chào"}'}, on) as cfg:
        expect(errs, "thiếu ngôn ngữ", check(cfg), red=True)
    with fixture({"locales/vi/auth.json": '{"hello": "Chào"}', "locales/en/auth.json": '{"hello": "Hi"}'}, on) as cfg:
        expect(errs, "khoá thiếu namespace", check(cfg), red=True)
    return errs
