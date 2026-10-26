# LOGISTICS_GUIDE — luật ngành logistics ({{PROJECT}})

Bổ sung cho `GATE_PROTOCOL`. Gate chủ: `fulfillment-lead` (đặt chỗ, nhãn, trạng thái chuyến hàng, vùng T),
`routing-lead` (cước, đơn vị, ETA, giờ cắt, vùng F). Ghép với `multi_provider` khi tích hợp nhiều hãng vận chuyển, với
`ecommerce` khi có thu hộ (COD).

## 1. Vùng rủi ro gợi ý (khai trong `slicegate.toml`)

| Vùng | Mã điển hình | Regex ví dụ |
|---|---|---|
| T | đặt chỗ hãng, nhãn, lấy hàng, máy trạng thái chuyến hàng, webhook hãng, giữ tồn kho, COD | `'^src/(booking|labels?|shipments?|carriers?|webhooks?|inventory|cod)/'` |
| F | tính cước, trọng lượng quy đổi, đổi đơn vị, ETA, giờ cắt, SLA, sức chở, tối ưu tuyến | `'^src/(rating|rates?|units|eta|sla|capacity|routing)/'` |
| K | khoá API hãng, địa chỉ và số điện thoại khách, vị trí tài xế | `'^src/(auth|secrets|addresses|tracking/location)/'` |

## 2. Guard của gói

| Guard | Chặn |
|---|---|
| `unit_suffix` | tên đại lượng (weight, distance, length, volume, temperature…) thiếu từ đơn vị (`kg`, `km`, `cbm`, `c`…) — Python, JS/TS, SQL |
| `naive_time` | mốc thời gian không múi giờ: `datetime.utcnow()`, `datetime.now()` không tz, `datetime(…)` thiếu `tzinfo`; SQL `timestamp` / `datetime`; JS `new Date("… hh:mm")` không có `Z` / độ lệch |

Miễn từng chỗ, kèm lý do: `units: ignore <lý do>`, `naive-time: ignore <lý do>`. Nếu mã của bạn dùng từ khác (vd `gw`
cho trọng lượng cả bì), mở rộng `[packs.logistics]` thay vì miễn.

`length` không nằm trong từ đại lượng mặc định (độ dài chuỗi / danh sách sẽ át tín hiệu); kiện hàng vẫn bị bắt qua
`width` / `height` / `depth`. Thêm vào nếu mã của bạn không bao giờ dùng `length` để đếm. Tệp thành phần giao diện
(`.tsx` / `.jsx`) mặc định được bỏ qua (`unit_skip`): `width` / `height` ở đó là pixel bố cục.

## 3. Luật cứng

1. **Đơn vị trong tên, đổi đơn vị ở một module**, hằng số chính xác, mỗi phép đổi một test.
2. **Lưu UTC kèm múi giờ**; giờ địa phương chỉ ở rìa (hiển thị, nhập liệu), theo múi giờ IANA của nơi đó (`Asia/Ho_Chi_Minh`), ⛔ độ lệch cố định.
3. **Khoá chống lặp** suy từ chuyến hàng trên mọi lời gọi GHI tới hãng; thử lại ⛔ đặt chỗ hai lần.
4. **Máy trạng thái chuyến hàng tường minh**; sự kiện của hãng lọc trùng theo id và áp theo thứ tự thời điểm xảy ra.
5. **Bảng cước là dữ liệu có phiên bản** và ngày hiệu lực; mỗi phụ phí có số vàng lấy từ bảng cước của hãng.
6. **Trọng lượng tính cước = max(thực, quy đổi)** theo hệ số và luật làm tròn của hãng.
7. **Địa chỉ và số điện thoại là dữ liệu cá nhân**: ⛔ vào log; vị trí tài xế chỉ giữ trong thời gian cần.
8. **Mỗi hãng một adapter**; thiếu năng lực ⇒ từ chối có tên.

## 4. Bộ đột biến mẫu

```toml
zone = "F"
cmd = "PYTHONPATH=src python -m pytest -q tests/rating tests/units"

[[mutant]]
id = "lb-kg-01"
file = "src/units/convert.py"
find = "KG_PER_LB = Decimal(\"0.45359237\")"
replace = "KG_PER_LB = Decimal(\"0.5\")"
why = "hằng số đổi đơn vị bị làm tròn ⇒ mọi cước tính bằng lb lệch 10%"

[[mutant]]
id = "dimweight-01"
file = "src/rating/chargeable.py"
find = "return max(actual_kg, dimensional_kg)"
replace = "return actual_kg"
why = "kiện cồng kềnh nhẹ bị tính theo trọng lượng thực ⇒ thu thiếu có hệ thống"

[[mutant]]
id = "cutoff-01"
file = "src/sla/cutoff.py"
find = "now_utc = datetime.now(timezone.utc)"
replace = "now_utc = datetime.now()"
why = "giờ cắt so bằng giờ máy chủ ⇒ đơn bị dồn sang sai ngày"
```
