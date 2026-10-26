"""Guard `provider_name_scope` (gói multi_provider) — tên nhà cung cấp CHỈ sống trong thư mục bộ chuyển (adapter) của nó.

`packs.multi_provider.providers = { stripe = ["stripe"], paypal = ["paypal", "braintree"] }` — mỗi nhà cung cấp một
tập chuỗi nhận dạng (tên, đường dẫn API riêng…). Chuỗi xuất hiện trong mã ngoài `adapter_dir` của chính nó ⇒ ĐỎ.
Khớp không phân biệt hoa/thường, theo chuỗi con, trong cả chuỗi và chú thích (chú thích nhắc tên sàn ngoài adapter
cũng là dấu hiệu logic rò ra ngoài).
"""
from __future__ import annotations

from gatekit.config import Config
from gatekit.guards._common import Finding, expect, fixture, iter_files, read
from gatekit.messages import t

NAME = "provider_name_scope"
PACK = "multi_provider"
FAST = True
DEFECT = {"vi": "logic riêng của một nhà cung cấp rò ra tầng chung ⇒ thêm nhà cung cấp thứ 2 phải sửa khắp nơi, nhánh if-provider bị quên",
          "en": "provider-specific logic leaks into the shared layer ⇒ adding a 2nd provider means edits everywhere, forgotten if-provider branches"}


def check(cfg: Config) -> list[Finding]:
    spec = cfg.pack("multi_provider")
    providers: dict[str, list[str]] = spec["providers"]
    if not providers:
        return []
    found: list[Finding] = []
    exts = tuple(cfg["paths"]["code_ext"]) + (".sql",)
    for rel in iter_files(cfg, exts=exts):
        if not cfg.is_prod(rel):
            continue
        low_lines = read(cfg, rel).lower().splitlines()
        for name, tokens in providers.items():
            home = spec["adapter_dir"].format(name=name).rstrip("/") + "/"
            if rel.startswith(home):
                continue
            for tok in tokens:
                needle = tok.lower()
                for i, line in enumerate(low_lines, 1):
                    if needle in line:
                        found.append(Finding(NAME, rel, i, t("provider.outside", token=tok, provider=name, home=home)))
                        break
    return found


def selftest() -> list[str]:
    errs: list[str] = []
    on = {"project": {"packs": ["multi_provider"]},
          "packs": {"multi_provider": {"providers": {"stripe": ["stripe"], "paypal": ["paypal"]}}}}
    with fixture({"src/providers/stripe/client.py": "STRIPE_URL = 'https://api.stripe.com'\n",
                  "src/billing/charge.py": "def charge(provider): return provider.charge()\n"}, on) as cfg:
        expect(errs, "tên trong adapter", check(cfg), red=False)
    with fixture({"src/billing/charge.py": "if name == 'stripe':\n    pass\n"}, on) as cfg:
        expect(errs, "tên ở tầng chung", check(cfg), red=True)
    with fixture({"src/providers/paypal/x.py": "import stripe\n"}, on) as cfg:
        expect(errs, "tên nhà khác trong adapter", check(cfg), red=True)
    with fixture({"tests/test_x.py": "'stripe'\n"}, on) as cfg:
        expect(errs, "test không phải mã sản xuất", check(cfg), red=False)
    return errs
