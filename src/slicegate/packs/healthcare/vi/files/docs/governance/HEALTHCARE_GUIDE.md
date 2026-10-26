# HEALTHCARE_GUIDE — luật ngành y tế ({{PROJECT}})

Bổ sung cho `GATE_PROTOCOL`. Gate chủ: `privacy-lead` (dữ liệu sức khoẻ, vùng K), `clinical-safety-lead` (số liệu lâm
sàng, vùng F). Nên dùng mức `regulated` để có `compliance-officer`. Tài liệu này là luật kỹ thuật, ⛔ tư vấn pháp lý.

## 1. Vùng rủi ro gợi ý (khai trong `slicegate.toml`)

| Vùng | Mã điển hình | Ví dụ regex |
|---|---|---|
| K | hồ sơ bệnh nhân, quyền xem, nhật ký truy cập, chia sẻ, xuất dữ liệu | `'^src/(patients?|records?|access|audit|sharing|exports?)/'` |
| F | liều thuốc, quy đổi đơn vị, khoảng tham chiếu, điểm nguy cơ, cảnh báo | `'^src/(dosing|units|labs?|risk|alerts?)/'` |
| T | kê đơn gửi đi, đặt lịch / huỷ lịch, thanh toán bảo hiểm | `'^src/(prescriptions?|scheduling|claims?)/'` |

## 2. Máy chặn của gói

| Guard | Chặn |
|---|---|
| `phi_log` | dữ liệu sức khoẻ vào print / log / raise / analytics / công cụ bắt lỗi (Python, JS/TS) |
| `phi_tag` | cột SQL chứa dữ liệu sức khoẻ thiếu nhãn `-- phi` (bản đồ dữ liệu: `grep -rn -- "-- phi" db/`) |

## 3. Luật cứng

1. **Tối thiểu cần thiết:** quyền xem theo vai + quan hệ điều trị; API trả đúng trường cần.
2. **Ghi nhật ký mọi lần đọc** hồ sơ (ai · lúc nào · bệnh nhân · trường · lý do), chỉ ghi thêm.
3. **Truy cập khẩn cấp** có lý do bắt buộc, cảnh báo, rà lại.
4. **PHI ⛔ ra khỏi vùng được bảo vệ:** log, analytics, công cụ bắt lỗi, thông báo đẩy, email chỉ mang id nội bộ.
5. **Cột PHI có nhãn và mã hoá** theo chính sách; khoá mã hoá tách khỏi DB.
6. **Không dữ liệu thật trong dev/test**; dùng dữ liệu tổng hợp hoặc đã khử định danh.
7. **Đơn vị tường minh** cho mọi đại lượng lâm sàng; quy đổi qua một mô-đun.
8. **Công thức lâm sàng có nguồn + số vàng từ nguồn**; giá trị ngoài miền ⇒ từ chối có tên.

## 4. Bộ đột biến mẫu

```toml
zone = "K"
cmd = "PYTHONPATH=src python -m pytest -q tests/access tests/clinical"

[[mutant]]
id = "care-rel-01"
file = "src/access/policy.py"
find = "if not has_care_relationship(user, patient):"
replace = "if False:"
why = "bỏ kiểm quan hệ điều trị ⇒ mọi bác sĩ đọc được mọi hồ sơ"

[[mutant]]
id = "read-audit-01"
file = "src/records/service.py"
find = "audit.record_read(user, patient, fields, reason)"
replace = "pass"
why = "đọc hồ sơ không để lại dấu vết"

[[mutant]]
id = "units-01"
file = "src/units/convert.py"
find = "MCG_PER_MG = 1000"
replace = "MCG_PER_MG = 1"
why = "nhầm mg ↔ mcg ⇒ liều sai 1000 lần"
```
