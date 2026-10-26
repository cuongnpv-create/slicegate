# gatekit

Bộ quy trình phát triển phần mềm **có cổng duyệt (gate)** cho đội agent AI (Claude Code): lát nhỏ, gate độc lập,
sổ phán append-only, máy gác chạy ở hook, **đột biến theo vùng rủi ro** để chứng minh test thật sự canh luật.

Rút ra từ một dự án thật — nền tảng giao dịch đa sàn, nhiều agent chạy song song — rồi tách phần **cơ chế** (dùng
chung) khỏi phần **nội dung** riêng dự án. Mọi tham số dự án nằm ở một tệp `gatekit.toml`.

> Trạng thái: `0.1.0` — bộ LÕI + 6 gói ngành. Bộ mẫu tài liệu **tiếng Việt và tiếng Anh**; định danh trong mã tiếng Anh.

## Vì sao

Agent AI viết mã nhanh nhưng hay mắc 4 lỗi: khai "đã xong" không có bằng chứng · test so mã với chính mã (test rỗng) ·
hai phiên song song giẫm nhau · quy trình phình to hơn phần mã. gatekit chặn từng lỗi bằng thứ **đo được**:

| Lỗi | Cơ chế |
|---|---|
| Khai không bằng chứng | gói G-IN/G-OUT bắt buộc lệnh đo + toạ độ; gate nhận diff, ⛔ nhận kết luận |
| Test rỗng | đột biến trên bản sao theo vùng rủi ro T/K/F; `test_wiring` bắt test không ai chạy |
| Giẫm nhau | phiên điều phối là người ghi sổ duy nhất; cấp dải số trước; mỗi lát một worktree; commit xếp hàng |
| Quy trình phình | "điều kiện có răng" (mỗi điều kiện phải nêu khuyết tật mã nó chặn) · `quota` tỷ lệ lát quản trị : lát mã · cuộn sổ |

## Cài và dựng

```bash
pip install git+https://github.com/<owner>/gatekit        # hoặc: pip install -e . trong bản sao repo
cd du-an-cua-ban && git init        # nếu chưa là repo
gatekit init --name "MyApp" --level standard --pack i18n --pack postgres
gatekit hooks install
gatekit check --full
```

Dự án tiếng Anh: `gatekit init --name "MyApp" --language en` (hoặc giữ agent nói tiếng Việt nhưng tài liệu tiếng Anh:
`--language vi --docs-language en`).

Sau `init`: điền `CLAUDE.md §1/§2/§7`, khai `[zones]` trong `gatekit.toml` theo mã thật, rồi mở phiên điều phối bằng
`docs/governance/COORDINATOR_PROMPT.md`.

## Ngôn ngữ

| Tham số | Nghĩa |
|---|---|
| `project.language` | ngôn ngữ agent giao tiếp (bất kỳ, vd `vi`, `en`, `ja`) |
| `project.docs_language` | ngôn ngữ bộ mẫu tài liệu: `vi` · `en`; để trống = theo `language` nếu có mẫu, ngược lại `en` |

Bộ mẫu nằm ở `templates/<vi|en>/` và `packs/<gói>/<vi|en>/`. Test `test_template_parity` bắt buộc hai bộ song song:
cùng tập tệp, cùng chỗ giữ `{{…}}`, bản `en` không sót tiếng Việt.

## Mức dùng

| Mức | Agent | Sổ phán | Hợp |
|---|---|---|---|
| `lite` | chief-architect · qa-lead | — (chỉ STATUS + CHANGELOG) | app nhỏ, 1 người |
| `standard` | + security-lead · ux-gate · product-director · design-director | theo làn | đội, nhiều agent song song |
| `regulated` | + compliance-officer | theo làn | tài chính, y tế, dữ liệu nhạy cảm |

## Gói ngành

| Gói | Thêm |
|---|---|
| `i18n` | guard `locale_parity` (catalog đủ, khớp khoá, khớp tham số) · Điều "bản địa hoá từ đầu" |
| `multi_provider` | guard `provider_name_scope`, `partition_key_scope` · Điều "nhà cung cấp tường minh", "ý định → định tuyến → bộ dịch", "chưa biết ≠ không" |
| `legacy_upgrade` | guard `legacy_import_ban` · `LEGACY_UPGRADE_GUIDE.md` (nhãn CHÉP/NÂNG/REPLACE/MỚI, ghi nguồn, test chụp hành vi) |
| `postgres` | guard `migration_scope` (ghim sha, số liên tục) · `gatekit migrations lock` |
| `fintech` | agent `execution-lead` (vùng T), `quant-lead` (vùng F), `domain-auditor` |
| `data_pipeline` | agent `data-integrity` |

## Lệnh

```
gatekit init        dựng quy trình vào repo (⛔ ghi đè tệp đã có trừ --force)
gatekit check       guard đang bật · --fast (pre-commit) · --full (+ neo đột biến + số sổ trùng)
gatekit selftest    ca âm/dương của mọi guard (--all: cả gói chưa bật)
gatekit zone        vùng rủi ro của diff + hình thức kiểm bắt buộc; tệp T/K thiếu bộ đột biến thường trực ⇒ ĐỎ
gatekit mutants     anchors · plan · run [--changed BASE]   (MUT_ONLY=id,… để chọn)
gatekit ledger      alloc (cấp dải số) · check (trùng) · open (điều kiện OPEN) · roll (cuộn sổ)
gatekit debt        nợ thiếu cột / quá hạn
gatekit quota       tỷ lệ lát quản trị : lát mã
gatekit hygiene     report · record — guard nào bắt được gì, lớp lỗi nào đủ 3 lần để đẻ guard
gatekit report      tổng hợp (hook SessionStart dùng bản --brief)
```

## gatekit tự gác chính nó

Repo này chạy chính gatekit (`gatekit.toml` mức lite, `tests/manifest.tsv`, `mutants/`):
`gatekit check --full` XANH · 76 test pytest · **11/11 đột biến bị giết** trên các guard và luật quyết định
(vùng rủi ro, tỷ lệ lát, cấp số sổ, cuộn sổ, bộ chạy đột biến).

Khi dựng bộ đột biến này, lượt chạy đầu báo 11/11 "sống" — lệnh test trong bản sao import gói đã cài `pip -e` trỏ về
checkout gốc, nên đột biến không có tác dụng. Lỗi ấy giờ được `gatekit mutants run` cảnh báo khi mọi đột biến đều sống.

## Cấu trúc

```
src/gatekit/
  config.py            gatekit.toml → mặc định + kiểm hợp lệ
  guards/              máy gác (lõi + gói), mỗi guard: check() · selftest() · DEFECT
  tools/               ledger · debt · slice_quota · risk_zone · guard_hygiene
  qa/mutants.py        đột biến trên bản sao, chọn theo diff, kiểm neo
  scaffold.py          gatekit init (mẫu {{KEY}}, {{#level …}}, {{#pack …}})
  templates/<vi|en>/   CLAUDE.md · governance/ · ledger theo làn · agent lõi · hook
  packs/<gói>/<vi|en>/ agent + tài liệu của gói ngành
tests/                 pytest
mutants/               bộ đột biến của chính gatekit
```

## Lộ trình

- Thông báo của dòng lệnh và guard theo ngôn ngữ dự án (hiện vẫn tiếng Việt).
- Đóng gói thành plugin Claude Code (agent + hook + lệnh) bên cạnh gói pip.
- Thêm gói: `mobile`, `saas_multitenant`, `ecommerce` (vùng T: thanh toán, hoàn tiền), `healthcare`.
- Bảng điều khiển đọc sổ phán / điều kiện OPEN / nhật ký guard.

## Giấy phép

Chưa chọn — mặc định giữ toàn quyền tác giả.
