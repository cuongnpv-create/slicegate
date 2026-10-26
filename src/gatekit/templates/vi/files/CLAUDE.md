# CLAUDE.md — {{PROJECT}}

Hướng dẫn cho agent làm việc trong repo này. **Giao tiếp bằng ngôn ngữ: {{LANGUAGE}}.**
Quy trình: gatekit (mức `{{LEVEL}}`{{PACKS_SUFFIX}}). Tham số ở `gatekit.toml` — nguồn duy nhất.

---

## §0 — Đầu mỗi phiên: đọc theo thứ tự

1. `CLAUDE.md` (tệp này) — luật, quy trình, bản đồ tài liệu.
2. `docs/STATUS.md` — trạng thái sống DUY NHẤT + bàn giao phiên kế.
3. `docs/governance/GATE_PROTOCOL.md` — khi xin / nhận phán gate.
{{#level standard regulated}}4. `docs/governance/SESSION_PROTOCOL.md` — khi điều phối nhiều agent.
{{/level}}

Hook `SessionStart` in sẵn: khối đầu STATUS, điều kiện còn mở, trạng thái git.

---

## §1 — Dự án này là gì

<!-- Điền: sản phẩm, người dùng, phạm vi, hệ cũ (nếu có), nơi chạy. Một đoạn. -->

---

## §2 — Ràng buộc kiến trúc cứng

<!-- Điền các luật MÁY KIỂM ĐƯỢC của dự án; mỗi luật ghi guard chặn nó. Ví dụ đã bật theo gói: -->
- **Đặt tên:** định danh trong mã (tệp, hàm, lớp, biến) tiếng Anh/ASCII; ngôn ngữ người viết ở chú thích, tài liệu, chuỗi hiển thị. Máy chặn: `naming_scope`.
- **Bí mật:** ⛔ hằng bí mật trong repo, ⛔ bí mật ra log / stdout / thông báo lỗi. Máy chặn: `secret_leak`.
- **Thiếu năng lực ⇒ từ chối có tên** (mã lý do), ⛔ `return None`, ⛔ giả vờ làm được.
{{#pack i18n}}- **Bản địa hoá từ đầu:** mọi chữ người dùng đọc đi qua catalog `{{I18N_DIR}}/` đủ {{I18N_LANGS}} trong CÙNG lát. Máy trả `{code, message_key, params}`, ⛔ trả câu. Máy chặn: `locale_parity`.
{{/pack}}{{#pack multi_provider}}- **Đa nhà cung cấp:** tên nhà cung cấp chỉ trong bộ chuyển của nó; mọi bảng mang cột phân vùng. Máy chặn: `provider_name_scope`, `partition_key_scope`.
{{/pack}}{{#pack legacy_upgrade}}- **Nâng cấp hệ cũ:** ⛔ import mã hệ cũ; mang sang = chép có ghi nguồn `{{LEGACY_LABEL}}<rev>:<tệp>:<dòng>` ngay trên khối chép + test ở hệ mới. Máy chặn: `legacy_import_ban`. Hướng dẫn: `docs/governance/LEGACY_UPGRADE_GUIDE.md`.
{{/pack}}{{#pack postgres}}- **Migration:** migration đã ghim ⛔ sửa — viết migration mới; số thứ tự liên tục. Máy chặn: `migration_scope`.
{{/pack}}

---

## §3 — Quy trình mỗi lát (BẮT BUỘC)

```
khảo sát (grep -n, toạ độ thật) ─► G-IN gate chủ ─► mã + test + ca âm + đột biến theo VÙNG RỦI RO trên BẢN SAO
   ─► gatekit check ─► G-OUT gate chủ (+ đồng gác) ─► vào main ─► sổ + STATUS trong CÙNG commit ─► báo owner ─► lát kế DO CA GIAO
```

- **Mặc định là làm.** Cổng chỉ cho việc có hậu quả (`GATE_PROTOCOL §1`).
- **Mỗi lát nêu:** *người dùng nay làm được gì mà trước chưa làm được*.
- **Vùng rủi ro quyết hình thức kiểm** (`gatekit zone --base main`, `GATE_PROTOCOL §4`).
- **Vấn đề phát hiện trên đường ⇒ xử dứt điểm TRONG lát.** Nợ chỉ khi bất khả giải trong lát (`GATE_PROTOCOL §3.2`).
- **Quản trị để mã chạy đúng, ⛔ để hệ quản trị đẹp:** thêm thủ tục / sổ / guard phải khai nó chặn khuyết tật MÃ nào.
- Lát quản trị (0 tệp mã sản xuất) ≤ `{{GOV_MAX}}` liền nhau, sau đó ≥ `{{CODE_AFTER_GOV}}` lát MÃ (`gatekit quota`).
- **Chief-architect giao việc CHỦ ĐỘNG** sau mỗi G-OUT — ⛔ hỏi owner "làm gì tiếp".
- **Mọi con số kèm lệnh đo + mốc UTC + phạm vi đã quét.**
- **Đồng hồ:** khai `ĐỎ n/2 · VÀNG m/6` mỗi lượt; chạm trần ⇒ hoàn tất lát dở, ⛔ mở lát mới (`GATE_PROTOCOL §8`).
- Commit: tiêu đề mang mã lát trong ngoặc vuông, vd `feat(auth): đăng nhập 2 bước [S-12]`.

---

## §4 — Luật owner (hiện hành)

Nguồn: `docs/governance/OWNER_WORDS.md` (nguyên văn, append-only). Bảng dưới là luật HIỆN HÀNH viết sạch — lệnh mới
thay lệnh cũ thì sửa dòng, lịch sử ở `OWNER_WORDS.md`.

| Mã | Luật | Từ |
|---|---|---|
| — | <!-- thêm dòng khi owner ra lệnh --> | — |

---

## §5 — Gate và vai

| Vai | Agent | Gác / sở hữu |
|---|---|---|
{{AGENTS_TABLE}}

Agent sống trong `.claude/agents/`. Người TẠO (giám đốc) ≠ người GÁC (gate).

---

## §6 — Bản đồ tài liệu (mỗi sự thật đúng 1 chủ)

| Tệp | Sở hữu | Cập nhật |
|---|---|---|
| `CLAUDE.md` | luật, quy trình, bản đồ | hiếm |
| `gatekit.toml` | mọi tham số quy trình (vùng rủi ro, ngân sách, làn, gói) | khi đổi tham số — qua gate |
| `docs/governance/CONSTITUTION.md` | điều luật tối cao + nơi máy chặn | hiếm |
| `docs/governance/GATE_PROTOCOL.md` | thủ tục gate | khi đổi thủ tục |
{{#level standard regulated}}| `docs/governance/SESSION_PROTOCOL.md` | buổi làm việc, phiên điều phối, test theo làn | khi đổi thủ tục |
| `docs/governance/OWNER_WORDS.md` | lời owner nguyên văn (append-only) | mỗi lệnh owner |
{{/level}}| `docs/governance/GUARD_CATCH_LOG.tsv` | lần guard bắt lỗi thật · sự cố theo lớp lỗi | `gatekit hygiene record` |
| `docs/STATUS.md` | trạng thái sống + bàn giao | mỗi lát |
| `docs/CHANGELOG.md` | mốc + thay đổi luật | mỗi mốc |
{{LEDGER_ROWS}}| `tests/manifest.tsv` | test nào chạy ở làn/tầng nào | mỗi test mới |
| `mutants/*.toml` | bộ đột biến | lát vùng T/K/F |

**Kết phiên — cập nhật đúng:** `docs/STATUS.md` · `docs/CHANGELOG.md`{{#level standard regulated}} · `DEBT.md` của làn{{/level}}; xin `chief-architect` G-OUT kết phiên; commit; push.

---

## §7 — Vùng bảo vệ

<!-- Điền: thư mục / dịch vụ / DB chỉ được đọc; hệ cũ; môi trường đang chạy thật. -->
- Mã chưa G-OUT ⛔ có mặt ở nơi đang chạy; triển khai chỉ từ rev ∈ `main`.
