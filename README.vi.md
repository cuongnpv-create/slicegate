# slicegate

[English](README.md) · **Tiếng Việt**

*Every slice of AI-written code passes a gate.* — mỗi lát mã do AI viết đều phải qua cổng.

Bộ quy trình phát triển phần mềm **có cổng duyệt (gate)** cho đội agent AI (Claude Code): lát nhỏ, gate độc lập,
sổ phán append-only, máy gác chạy ở hook, **đột biến theo vùng rủi ro** để chứng minh test thật sự canh luật.

Rút ra từ một dự án thật — nền tảng giao dịch đa sàn, nhiều agent chạy song song — rồi tách phần **cơ chế** (dùng
chung) khỏi phần **nội dung** riêng dự án. Mọi tham số dự án nằm ở một tệp `slicegate.toml`.

> Trạng thái: `0.3.0` (trước đây tên **gatekit**) — bộ LÕI + 10 gói ngành. Tài liệu mẫu, thông báo dòng lệnh và guard: **tiếng Việt và tiếng Anh**; định danh trong mã tiếng Anh.

## Vì sao

Agent AI viết mã nhanh nhưng hay mắc 4 lỗi: khai "đã xong" không có bằng chứng · test so mã với chính mã (test rỗng) ·
hai phiên song song giẫm nhau · quy trình phình to hơn phần mã. slicegate chặn từng lỗi bằng thứ **đo được**:

| Lỗi | Cơ chế |
|---|---|
| Khai không bằng chứng | gói G-IN/G-OUT bắt buộc lệnh đo + toạ độ; gate nhận diff, ⛔ nhận kết luận |
| Test rỗng | đột biến trên bản sao theo vùng rủi ro T/K/F; `test_wiring` bắt test không ai chạy |
| Giẫm nhau | phiên điều phối là người ghi sổ duy nhất; cấp dải số trước; mỗi lát một worktree; commit xếp hàng |
| Quy trình phình | "điều kiện có răng" (mỗi điều kiện phải nêu khuyết tật mã nó chặn) · `quota` tỷ lệ lát quản trị : lát mã · cuộn sổ |

## Cài và dựng

### Cách 1 — plugin Claude Code (khuyên dùng)

```
/plugin marketplace add cuongnpv-create/slicegate
/plugin install slicegate@slicegate
```
Claude Code 2.1.275 trở lên cài được một bước: `/plugin install slicegate --marketplace cuongnpv-create/slicegate`
(ngoài phiên: `claude plugin marketplace add cuongnpv-create/slicegate && claude plugin install slicegate@slicegate`).
Plugin mang theo:

| Thành phần | Dùng |
|---|---|
| `/slicegate:init` | hỏi mức, gói, ngôn ngữ, làn ⇒ chạy `slicegate init` ⇒ tự điền `CLAUDE.md`, `[zones]`, manifest test từ mã thật ⇒ `check --full` xanh |
| `/slicegate:check` | chạy mọi guard, sửa từng chỗ đỏ ngay trong mã (⛔ nới guard) |
| `/slicegate:gate G-IN\|G-OUT\|G-DECIDE <lát>` | đo · cấp số · chọn gate · gửi gói · ghi phán vào sổ |
| `/slicegate:coordinator` | mở phiên điều phối theo `SESSION_PROTOCOL` |
| lệnh `slicegate` | có sẵn trên PATH của Bash trong Claude Code — ⛔ cần pip (chỉ cần Python ≥ 3.11) |
| hook `SessionStart` | in tóm tắt trạng thái khi mở phiên trong dự án đã cài slicegate |

`slicegate hooks install` chạy từ plugin ghi đường dẫn lệnh vào git hook, nên `pre-commit` / `pre-push` vẫn chạy được
khi commit ngoài Claude Code. Cập nhật plugin xong (đường dẫn đổi) thì chạy lại `slicegate hooks install`.
Lưu ý: claude.ai và Cowork không cài plugin có thư mục `bin/` — plugin này dành cho Claude Code.

### Cách 2 — gói pip

```bash
pip install slicegate                                               # hoặc: pipx install slicegate · uvx slicegate
cd du-an-cua-ban && git init        # nếu chưa là repo
slicegate init --name "MyApp" --level standard --pack i18n --pack postgres
slicegate hooks install
slicegate check --full
```

Dự án tiếng Anh: `slicegate init --name "MyApp" --language en` (hoặc giữ agent nói tiếng Việt nhưng tài liệu tiếng Anh:
`--language vi --docs-language en`).

Sau `init`: điền `CLAUDE.md §1/§2/§7`, khai `[zones]` trong `slicegate.toml` theo mã thật, rồi mở phiên điều phối bằng
`docs/governance/COORDINATOR_PROMPT.md`.

## Ngôn ngữ

| Tham số | Nghĩa |
|---|---|
| `project.language` | ngôn ngữ agent giao tiếp (bất kỳ, vd `vi`, `en`, `ja`) |
| `project.docs_language` | ngôn ngữ bộ mẫu tài liệu: `vi` · `en`; để trống = theo `language` nếu có mẫu, ngược lại `en` |

Thông báo của dòng lệnh, guard và công cụ dùng cùng ngôn ngữ ấy (`src/slicegate/messages.py`); ghi đè một lần chạy bằng
biến môi trường `SLICEGATE_LANG=vi|en`.

Bộ mẫu nằm ở `templates/<vi|en>/` và `packs/<gói>/<vi|en>/`. Test `test_template_parity` và `test_messages` bắt buộc
hai ngôn ngữ song song: cùng tập tệp / khoá, cùng chỗ giữ / tham số, bản `en` không sót tiếng Việt.

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
| `postgres` | guard `migration_scope` (ghim sha, số liên tục) · `slicegate migrations lock` |
| `fintech` | agent `execution-lead` (vùng T), `quant-lead` (vùng F), `domain-auditor` |
| `data_pipeline` | agent `data-integrity` |
| `ecommerce` | guard `money_float` (tiền ⛔ float — Python, SQL, `parseFloat`), `pci_scope` (⛔ lưu số thẻ / CVV) · agent `checkout-lead` (vùng T: đơn, thanh toán, webhook, hoàn tiền, tồn kho), `pricing-lead` (vùng F: giá, khuyến mãi, thuế, làm tròn) · `ECOMMERCE_GUIDE.md` (vùng gợi ý, luật cứng, bộ đột biến mẫu) · Điều 12 "Tiền là chính xác" |
| `saas_multitenant` | guard `tenant_scope` (bảng có cột tenant; mọi câu SQL trong mã chạm bảng tenant phải lọc tenant — Python, JS/TS, Go, Java…, tệp `.sql`), `tenant_rls` (bật `require_rls`: bảng tenant phải bật Row Level Security + có policy) · agent `tenancy-lead` (vùng K: ngữ cảnh tenant, cache, job, đăng nhập hộ, xuất/xoá dữ liệu), `billing-lead` (vùng T/F: đăng ký, pro-rata, đo lượng dùng, giới hạn gói) · `SAAS_GUIDE.md` (mô hình cách ly, vùng gợi ý, test chéo tenant, bộ đột biến mẫu) · Điều 13 "Khách thuê là tường minh" |
| `healthcare` | guard `phi_log` (dữ liệu sức khoẻ ⛔ vào print / log / raise / analytics / công cụ bắt lỗi — Python, JS/TS), `phi_tag` (cột SQL chứa dữ liệu sức khoẻ phải khai `-- phi` ⇒ bản đồ dữ liệu) · agent `privacy-lead` (vùng K: quyền xem tối thiểu, nhật ký mọi lần đọc, truy cập khẩn cấp, đồng ý, khử định danh), `clinical-safety-lead` (vùng F: liều, đơn vị, khoảng tham chiếu, cảnh báo) · `HEALTHCARE_GUIDE.md` · Điều 14 "Dữ liệu sức khoẻ là tối thiểu và có dấu vết" |
| `logistics` | guard `unit_suffix` (tên đại lượng — weight, distance, volume, temperature… — phải mang đơn vị: `weight_kg`, `distanceKm`, `temp_c` — Python, JS/TS, SQL), `naive_time` (mốc thời gian ⛔ ngây thơ: `datetime.utcnow()`, `now()` không tz, SQL `timestamp`, JS `new Date("… hh:mm")`) · agent `fulfillment-lead` (vùng T: đặt chỗ hãng, nhãn, máy trạng thái chuyến hàng, webhook, tồn kho, COD), `routing-lead` (vùng F: cước, trọng lượng quy đổi, ETA, giờ cắt, SLA) · `LOGISTICS_GUIDE.md` · Điều 15 "Đại lượng và thời gian không mơ hồ" |

## Lệnh

```
slicegate init        dựng quy trình vào repo (⛔ ghi đè tệp đã có trừ --force)
slicegate check       guard đang bật · --fast (pre-commit) · --full (+ neo đột biến + số sổ trùng)
slicegate selftest    ca âm/dương của mọi guard (--all: cả gói chưa bật)
slicegate zone        vùng rủi ro của diff + hình thức kiểm bắt buộc; tệp T/K thiếu bộ đột biến thường trực ⇒ ĐỎ
slicegate mutants     anchors · plan · run [--changed BASE]   (MUT_ONLY=id,… để chọn)
slicegate ledger      alloc (cấp dải số) · check (trùng) · open (điều kiện OPEN) · roll (cuộn sổ)
slicegate debt        nợ thiếu cột / quá hạn
slicegate quota       tỷ lệ lát quản trị : lát mã
slicegate hygiene     report · record — guard nào bắt được gì, lớp lỗi nào đủ 3 lần để đẻ guard
slicegate report      tổng hợp (hook SessionStart dùng bản --brief)
slicegate migrate     chuyển dự án cài từ thời tên gatekit (xem dưới)
```

## Chuyển từ gatekit

Công cụ này trước bản `0.3.0` tên là **gatekit**. Dự án đã cài vẫn chạy: `gatekit.toml` và thư mục `.gatekit/` vẫn được
đọc (kèm lời nhắc), lệnh `gatekit` vẫn có khi cài qua pip (kèm lời nhắc), `GATEKIT_LANG` vẫn được nhận. Chuyển hẳn một
lần:

```bash
slicegate migrate     # git mv gatekit.toml → slicegate.toml, .gatekit/ → .slicegate/, viết lại hook, cài lại git hook
git commit -m "chore: chuyển gatekit → slicegate"
```

Lệnh `gatekit` và việc đọc tên cũ sẽ bị gỡ ở một bản sau.

## slicegate tự gác chính nó

Repo này chạy chính slicegate (`slicegate.toml` mức lite, `tests/manifest.tsv`, `mutants/`):
`slicegate check --full` XANH · 271 test pytest · **25/25 đột biến bị giết** trên các guard và luật quyết định
(vùng rủi ro, tỷ lệ lát, cấp số sổ, cuộn sổ, bộ chạy đột biến).

Khi dựng bộ đột biến này, lượt chạy đầu báo 11/11 "sống" — lệnh test trong bản sao import gói đã cài `pip -e` trỏ về
checkout gốc, nên đột biến không có tác dụng. Lỗi ấy giờ được `slicegate mutants run` cảnh báo khi mọi đột biến đều sống.

## Ca thử nghiệm

[`docs/case-studies/itsdangerous.md`](docs/case-studies/itsdangerous.md) — cài lên `pallets/itsdangerous`: 6 đột biến vùng
K chỉ ra một lỗ hổng test thật ở cơ chế xoay khoá (297 test vẫn xanh khi bộ ký chỉ thử khoá cũ nhất); 3 chỗ vướng
của slicegate tìm được và sửa ngay (lượt `check` đầu từ 12 ĐỎ oan xuống 0).

## Cấu trúc

```
.claude-plugin/        plugin.json · marketplace.json · icon.png (repo vừa là plugin vừa là marketplace)
bin/slicegate          lệnh của plugin (chạy src/ trực tiếp)
skills/                /slicegate:init · check · gate · coordinator
hooks/                 SessionStart của plugin
src/slicegate/
  config.py            slicegate.toml → mặc định + kiểm hợp lệ
  messages.py          catalog thông báo vi · en, một hàm t()
  guards/              máy gác (lõi + gói), mỗi guard: check() · selftest() · DEFECT
  tools/               ledger · debt · slice_quota · risk_zone · guard_hygiene
  qa/mutants.py        đột biến trên bản sao, chọn theo diff, kiểm neo
  scaffold.py          slicegate init (mẫu {{KEY}}, {{#level …}}, {{#pack …}})
  templates/<vi|en>/   CLAUDE.md · governance/ · ledger theo làn · agent lõi · hook
  packs/<gói>/<vi|en>/ agent + tài liệu của gói ngành
tests/                 pytest
mutants/               bộ đột biến của chính slicegate
```

## Phát hành

Tăng phiên bản ở `pyproject.toml`, `.claude-plugin/plugin.json` và `.claude-plugin/marketplace.json` (workflow chặn nếu
lệch), gộp vào `main`, rồi chọn một trong hai: tạo GitHub Release với tag `vX.Y.Z`, hoặc chạy **Actions → release → Run
workflow** trên `main` và nhập phiên bản. Cả hai đường đều test, đóng gói, đẩy lên PyPI qua trusted publishing và đính gói
vào GitHub Release.

## Lộ trình

- Thêm gói: `mobile`.
- Bảng điều khiển đọc sổ phán / điều kiện OPEN / nhật ký guard.

## Giấy phép

[MIT](LICENSE).
