"""Sổ đăng ký máy gác: lõi + gói ngành."""
from __future__ import annotations

import importlib
import pkgutil
from types import ModuleType

from slicegate.config import Config


def all_guards() -> list[ModuleType]:
    mods = []
    for info in pkgutil.iter_modules(__path__):
        if info.name.startswith("_"):
            continue
        mods.append(importlib.import_module(f"{__name__}.{info.name}"))
    return sorted(mods, key=lambda m: m.NAME)


def enabled_guards(cfg: Config, *, fast_only: bool = False) -> list[ModuleType]:
    out = []
    for m in all_guards():
        if m.PACK is not None and m.PACK not in cfg.packs:
            continue
        if fast_only and not m.FAST:
            continue
        out.append(m)
    return out
