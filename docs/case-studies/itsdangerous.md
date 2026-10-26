# Ca thử nghiệm: gatekit trên `itsdangerous`

Ngày 2026-10-26 · `pallets/itsdangerous` @ `672971d` (bản clone nông) · 1 176 dòng mã · 5 tệp test, 297 test pytest XANH.
Mục tiêu: cài gatekit lên một dự án thật nhỏ, đi hết luồng `/gatekit:init`, tìm chỗ vướng của chính gatekit.

## Quy trình đã chạy

| Bước | Lệnh | Kết quả |
|---|---|---|
| Cài | `gatekit init --name itsdangerous --level standard` | 25 tệp, 0,1 s |
| Kiểm lượt đầu | `gatekit check --full` | ĐỎ 12 chỗ (xem phát hiện ①②) |
| Khai vùng | `[zones.K]` = `signer.py`, `timed.py`, `serializer.py` · `[zones.F]` = `encoding.py` | — |
| Bộ đột biến vùng K | `mutants/signing.toml`, 6 đột biến (kiểm chữ ký, xoay khoá, thiếu dấu phân cách, biên hết hạn, dấu thời gian tương lai) | **5/6 bị giết · 5,3 s** |
| Lát giả lập | sửa docstring `signer.py`, commit `[S-1]` | `gatekit zone` ⇒ vùng K, có bộ thường trực ⇒ XANH |
| Sổ | `gatekit ledger alloc` | `P-L1`, `P-C1…P-C20` |
| Tỷ lệ lát | `gatekit quota` | XANH (sau phát hiện ③) |

## Phát hiện về DỰ ÁN (giá trị gatekit mang lại)

**Lỗ hổng test ở cơ chế xoay khoá.** Đột biến `sig-03` — vòng thử khoá chỉ còn khoá CŨ NHẤT
(`reversed(self.secret_keys)` → `reversed(self.secret_keys[:1])`) — **SỐNG**: 297 test vẫn XANH.
Nguyên nhân: `test_signer.py::test_secret_keys` chỉ thử token ký bằng khoá cũ (`Signer("a")`) rồi xác minh bằng
`Signer(["a", "b"])`; không test nào xác minh token ký bằng khoá MỚI NHẤT khi có nhiều khoá. Hậu quả nếu mã bị sửa sai
như đột biến: sau khi xoay khoá, mọi token vừa ký đều bị từ chối, CI không báo.

Test đề xuất (chưa chạy trong ca này — môi trường thử không cho chạy lại mã bên ngoài; việc đột biến sống đã đo được):

```python
def test_secret_keys_newest_key_verifies(self):
    signer = Signer(["a", "b"])
    assert signer.unsign(signer.sign("my string")) == b"my string"
```

## Phát hiện về GATEKIT (đã sửa trong cùng lát)

| # | Vướng | Sửa | Test ghim |
|---|---|---|---|
| ① | `secret_leak` báo nhầm 7/7: `secret_key="secret-key"` trong fixture test | luật "gán hằng" bỏ qua tệp test và giá trị giữ chỗ; PEM / khoá AWS / token thật vẫn ĐỎ mọi nơi | selftest `secret_leak` (3 ca mới) |
| ② | `init` để manifest rỗng ⇒ 5 tệp test có sẵn ĐỎ `test_wiring` | `init` tự khai test đang có (mỗi thư mục × mẫu tên một glob) | `test_init_seeds_manifest_from_existing_tests` |
| ③ | `quota` tính cả lịch sử trước khi cài ⇒ commit tài liệu cũ liền nhau thành "lát quản trị liền nhau" | mặc định tính từ commit thêm `gatekit.toml` | `test_slice_quota_ignores_history_before_install` |

Sau ba sửa: lượt `gatekit check --full` đầu tiên trên bản clone sạch **XANH ngay** (trước: 12 ĐỎ oan).

## Bài học cho sản phẩm

- Thời gian cài + khai vùng + viết 6 đột biến: dưới 15 phút cho thư viện cỡ này; chạy đủ bộ đột biến 5,3 s.
- Giá trị thấy được ngay là **đột biến vùng K** — chỉ ra một lỗ hổng test thật ở thư viện được dùng rộng rãi, mà
  độ phủ dòng (coverage) không thấy (dòng ấy vẫn được chạy, chỉ không bị kiểm đúng nhánh).
- Cài lên dự án có sẵn phải "xanh ngay lượt đầu" — mọi ĐỎ oan ở lượt đầu làm người dùng tắt guard.
