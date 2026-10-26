# THỦ TỤC GATE — {{PROJECT}}

> Luật hiện hành, viết sạch. Lịch sử thay đổi luật ở `docs/CHANGELOG.md`, ⛔ ở đây.
> Tham số (vùng rủi ro, ngân sách test, số lát song song, làn sổ) ở `slicegate.toml` — nguồn DUY NHẤT.

## §1 — Khi nào phải qua gate

**Mặc định là LÀM.** Việc thường trong phạm vi đã mở (vá lỗi, thêm test, dọn cục bộ) ⇒ làm → đo → ghi 1 dòng STATUS.
Gate chỉ cho việc **có hậu quả**:

| Việc | Gate chủ | Đồng gác |
|---|---|---|
| Mở pha / lát đầu của pha · đổi kiến trúc · dịch vụ mới hoặc đổi bản đang chạy | `chief-architect` | gate miền |
| Lát chạm vùng **T** (thao tác không đảo ngược: tiền, lệnh, xoá dữ liệu) | gate miền của vùng (gói ngành) ∨ `chief-architect` | `chief-architect` |
| Lát chạm vùng **K** (bí mật · khoá · xác thực · quyền) | `security-lead` | `chief-architect` khi chạm kiến trúc |
| Lát chạm vùng **F** (công thức · quy tắc quyết định) | gate miền công thức (gói ngành) ∨ `qa-lead` | — |
| DDL / DCL / DML tay lên DB có dữ liệu | `chief-architect` | gate miền của bảng |
| Giao diện chạm tiền / rủi ro / xoá | `ux-gate` | gate miền tương ứng |
| Điều kiện pháp lý, consent, ToS, giấy phép thư viện | `compliance-officer` (mức regulated) | — |
| Sửa chính bộ quy trình (`CLAUDE.md`, tệp này, agent, hook, guard) | `chief-architect` | — |
| Kết phiên | `chief-architect` | — |

**Khuôn gate chủ theo loại lát** — lát chạm nhiều loại ⇒ gate của loại NẶNG nhất làm chủ, các gate còn lại làm đồng:
`dịch vụ/DDL/vùng T` > `cổng main/CI/hook` > `công cụ QA/guard` > `thuần miền (công thức, UI)`.

**Lệnh nới PHẠM VI ⛔ nới THẨM QUYỀN:** "làm luôn" của owner không bỏ được cổng của việc có hậu quả.

## §2 — Gói báo cáo (người làm lát gửi gate)

```
GÓI <G-IN | G-OUT | G-DECIDE | G-OUT KẾT PHIÊN> — <mã lát>
Số giao: <P>-L<n> · <P>-C<a>…<b> [· <P>-D<n>]     ← điều phối cấp dải TRƯỚC (slicegate ledger alloc); gate ⛔ tự chọn số
Rev: <git rev-parse --short HEAD> · nhánh <tên>
1. Việc / phạm vi — tệp · hàm · bảng · dịch vụ, toạ độ lấy bằng `grep -n` (⛔ đếm mắt)
2. Người dùng nay làm được gì mà trước chưa làm được
3. Bằng chứng: mỗi con số = lệnh đo + mốc UTC + phạm vi đã quét
4. Vùng rủi ro: đầu ra `slicegate zone --base <base>` + hình thức kiểm đã nộp theo §4
5. DoD + ca âm (kỳ vọng từ nguồn NGOÀI mã: đặc tả, hợp đồng, sách, hệ cũ có dòng) — chạy trên BẢN SAO
6. Rủi ro · giới hạn gọi API ngoài (nếu có) · đường lui
7. Điều kiện gate trước còn mở chạm lát này
8. Đồng hồ: ĐỎ n/2 · VÀNG m/6
```

Gate nhận **tệp, diff, toạ độ, lệnh đo** — ⛔ nhận kết luận của người làm. Gate tự mở tệp, tự đo lại khi rẻ.

## §3 — Phán quyết

`APPROVE` · `APPROVE-WITH-CONDITIONS` · `REJECT` · `NEEDS-INFO`. REJECT phải có đủ 7 dòng:
`SCOPE · BLOCKING-INVARIANT · EVIDENCE (tệp:dòng / số) · REMEDIATION-REQUIRED · RETEST · UNBLOCK-AUTHORITY · DECISION-NEXT`.

- **Phán trong MỘT lượt**, kèm đường đi thi hành được. Vế khó ⇒ trả lời bằng CÁCH LÀM, ⛔ bằng lý do không làm được.
- **Thiếu tham số / nguồn** ⇒ gate TỰ đề xuất kèm căn cứ; owner duyệt 1 dòng. ⛔ treo lát để hỏi.
- **DoD phải đo bằng nguồn ĐỘC LẬP.** Bác DoD tự đồng ý với chính nó (test so mã với chính mã — ca vòng tròn).
- Gate `chief-architect` mỗi G-OUT kèm khối **GIAO VIỆC**: ≥ 2 lát kế theo ưu tiên, ≥ 1 lát chạy được khi các trục khác
  bị chặn (chờ dữ liệu, chờ người). ⛔ "chờ owner quyết lát kế".

### §3.1 — Điều kiện gate phải có RĂNG

Mỗi điều kiện `<P>-C<n>` ghi đủ 3 vế:

1. **Khuyết tật MÃ nó chặn** — hành vi sai cụ thể mà người dùng / tiền / dữ liệu sẽ gặp;
2. **Phép đo** — lệnh hoặc test chứng minh đã đóng;
3. **Vùng rủi ro** — T / K / F / khác.

Luật kèm theo:
- Thiếu vế 1 ⇒ điều kiện không hợp lệ: người làm xin bỏ tại G-OUT kèm 1 dòng lý do. Ở vùng T/K, gate PHẢI trả lời bằng chữ
  (bổ vế ∨ bỏ có lý do); không trả lời ⇒ điều kiện GIỮ (fail-closed).
- Hai điều kiện chặn CÙNG một khuyết tật ⇒ gộp làm một. ⛔ trần, ⛔ sàn số điều kiện. Dải số là chỗ giữ số, ⛔ chỉ tiêu.
- Lo ngại không quy được về khuyết tật cụ thể ("phòng khi", "cho chắc") ⇒ ghi là NHẬN XÉT trong thân phán, ⛔ thành điều kiện.
- **Điều kiện phải ĐÓNG trong lát.** ⛔ `post-merge`, ⛔ "chờ lát sau" cho thứ giải được ngay. Gate đặt điều kiện nào
  thì điều kiện ấy đóng trước khi lát khép — ∨ gate ⛔ đặt nó.
- Ghi điều kiện trong LEDGER: `- **<P>-C<n>** [OPEN|CLOSED] <khuyết tật> · đo: <lệnh> · vùng: <T/K/F/khác>`.

### §3.2 — Nợ

⛔ mở nợ cho vấn đề giải được trong lát. Mở nợ CHỈ khi **bất khả giải trong lát** (phải chờ một lát mã khác); nợ khai
khuyết tật còn ngỏ · điều kiện đóng đo được · lát sẽ đóng · hạn — và **đóng ngay khi thoả**. `slicegate debt` đo.

## §4 — Vùng rủi ro T · K · F (hình thức kiểm)

Lát thuộc vùng nếu tệp trong diff khớp `zones.<V>.paths` ∨ dòng thêm khớp `zones.<V>.grep` (`slicegate zone --base <base>`).
Vùng nặng nhất quyết. Tệp mới mang tiền / khoá / công thức nằm ngoài regex ⇒ gate miền xếp vùng TẠI G-IN và lát sửa
`slicegate.toml` trong CÙNG commit. Gate đồng chỉ được THÊM vào vùng; bớt = `chief-architect` G-DECIDE.

| Vùng | Bắt buộc ở G-OUT |
|---|---|
| **T** | bộ đột biến THƯỜNG TRỰC (khai manifest); đột biến gỡ từng cổng **tại từng chỗ gọi** ⇒ ĐỎ; ca âm mọi đường từ chối |
| **K** | bộ đột biến THƯỜNG TRỰC; thiếu quyền ⇒ từ chối có tên; bí mật ⛔ ra log (`secret_leak` XANH) |
| **F** | số vàng nguồn ĐỘC LẬP (sách, bảng công bố, đáp án giải tích) là test thường trực + ≥ 1 đột biến đánh lõi công thức; sửa test vàng ⇒ chạy lại đột biến của cột/quy tắc ấy |
| **khác** | test hành vi + ≥ 1 ca âm kỳ vọng NGOÀI mã. Đột biến ⛔ bắt buộc; gate ĐƯỢC đòi khi nghi test rỗng — nêu TÊN test + lý do, ≤ {{MAX_ONE_OFF}} đột biến, chạy MỘT LẦN |

- Bộ T/K ⛔ được gỡ khỏi manifest, ⛔ được đưa vào danh sách "neo lệch đã biết" — lệch ⇒ sửa trong lát.
- **Chỉ owner nới:** đột biến theo chỗ gọi ở vùng T · bộ thường trực T/K · số vàng nguồn độc lập · ca âm mọi lát.
- Gỡ bộ đột biến cũ ngoài T/K: chạy bộ MỘT lần ở `<base>`, có đột biến SỐNG ⇒ ⛔ gỡ, thêm test bắt nó trước.

## §5 — Hiệu năng đường nóng

Đường nóng = `hotpath.paths`. Lát chạm đường nóng ĐÃ có bench: chạy bench ở `<base>` rồi `<rev>`, cùng máy, `{{HOT_RUNS}}`
lượt mỗi bên, ghi p50/p99. ĐỎ khi ⒜ vượt ngân sách tuyệt đối đã khai ∨ ⒝ p50`<rev>` ≥ `{{HOT_RATIO}}×` p50`<base>` và
khoảng hai bên không chồng nhau. ⛔ tệp mốc lưu sẵn (máy dao động). Tổng thời gian đo ≤ `{{HOT_MAX}}` giây/lát.
Chưa có bench ⇒ ⛔ ĐỎ; gate miền quyết lát nào dựng bench đầu. Đúng trước, nhanh sau — hiệu năng ⛔ thay test đúng.

## §6 — Ngân sách test mỗi lát

Tầng 1 (thuần) ≤ `{{T1}}` s · một đột biến ≤ `{{MUT1}}` s (đo lệnh TRƯỚC khi chạy bộ) · tổng đột biến ≤ `{{MUTALL}}` s.
Vượt ⇒ dừng, sửa NGUYÊN NHÂN chỉ bằng cắt chi phí (thu hẹp lệnh, test-double rẻ kèm ca ghim thứ thật, tách ca đắt);
⛔ bỏ test, ⛔ hạ ngưỡng sản xuất. Người làm chạy ĐỦ bộ MỘT lần trên sha ứng viên và nộp log; gate chạy `--check` + đọc
log + ≤ 3 đột biến tự chọn (`MUT_ONLY=<id,…>`). Chạy lại ĐỦ chỉ khi log thiếu / sha lệch / có SỐNG.

## §7 — Mã số

| Mã | Nghĩa | Nơi định nghĩa |
|---|---|---|
| `<P>-L<n>` | entry phán | `## <P>-L<n> — <tiêu đề> · <YYYY-MM-DD>` trong `LEDGER.md` của làn |
| `<P>-D<n>` | ruling bền | `## <P>-D<n> — …` trong `DECISIONS.md` |
| `<P>-C<n>` | điều kiện gate | `- **<P>-C<n>** [OPEN\|CLOSED] …` trong entry |
| `<P>-N<n>` | nợ | dòng bảng trong `DEBT.md` |

Làn và tiền tố: {{LANES_INLINE}}. Số do **điều phối** cấp bằng `slicegate ledger alloc` — gate CHỦ ≥ `{{RANGE_PRIMARY}}`
mã C, gate ĐỒNG `{{RANGE_CO}}`. Số dư của dải là bình thường. `slicegate ledger check` bắt số trùng.

## §8 — Đồng hồ phiên

Khai mỗi lượt `ĐỎ n/2 · VÀNG m/6` (ĐỎ = sai lầm nặng: lời khai sai, phá cổng; VÀNG = trượt nhỏ). Chạm trần ⇒
**⛔ mở lát MỚI · ⛔ nhận việc mới; lát ĐANG DỞ phải HOÀN THÀNH TRỌN VẸN** (sửa điều kiện gate → G-OUT → vào main) →
CUỐI CÙNG G-OUT kết phiên → STATUS bàn giao đủ (lát nào xong, SHA, điều kiện còn mở) → commit → push. ⛔ dừng giữa lát.

## §9 — Byte ở đâu

- Mã chỉ vào `main` sau G-OUT. `main` = byte đã duyệt.
- Byte CHẠY = byte ĐÃ KÝ: triển khai từ rev ∈ `main`, ⛔ từ cây làm việc; mã chưa G-OUT ⛔ có mặt ở nơi đang chạy.
- Đột biến / thử phá chạy trên BẢN SAO (`slicegate mutants run` tự chép), ⛔ trên checkout làm việc.
