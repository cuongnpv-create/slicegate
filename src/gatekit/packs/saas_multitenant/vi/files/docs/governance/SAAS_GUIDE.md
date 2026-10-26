# SAAS_GUIDE — luật ngành SaaS nhiều khách thuê ({{PROJECT}})

Bổ sung cho `GATE_PROTOCOL`. Gate chủ: `tenancy-lead` (cách ly, vùng K), `billing-lead` (gói cước, vùng T/F).

## 1. Chọn mô hình cách ly (ghi vào `DECISIONS.md`)

| Mô hình | Cách ly | Chi phí vận hành | Máy chặn của gói |
|---|---|---|---|
| Chung bảng, cột `tenant_id` | thấp nhất — dựa vào truy vấn + RLS | rẻ | `tenant_scope` + `tenant_rls` (bật `require_rls`) |
| Schema riêng mỗi tenant | trung bình — dựa vào `search_path` | trung bình | test chéo tenant ở vùng K |
| DB riêng mỗi tenant | cao nhất | đắt | test định tuyến kết nối |

## 2. Vùng rủi ro gợi ý (khai trong `gatekit.toml`)

| Vùng | Mã điển hình | Ví dụ regex |
|---|---|---|
| K | ngữ cảnh tenant, xác thực, quyền, middleware, repository/DAO, cache | `'^src/(tenancy|auth|middleware|repositories?|cache)/'` |
| T | thu tiền định kỳ, webhook billing, xoá tenant | `'^src/(billing|webhooks?)/'`, `'^src/tenants/delete'` |
| F | pro-rata, đo lượng dùng, giới hạn gói | `'^src/(billing/proration|metering|entitlements?)/'` |

## 3. Luật cứng

1. Ngữ cảnh tenant chỉ từ phiên đã xác thực; ⛔ từ tham số/header/subdomain chưa đối chiếu.
2. Mọi bảng dữ liệu khách có `tenant_id NOT NULL` (đầu khoá chính hoặc có chỉ mục); bảng dùng chung khai `-- tenant: global <lý do>`.
3. Mọi truy vấn bảng tenant lọc `tenant_id`; Postgres bật RLS + policy theo `current_setting('app.tenant_id')`.
4. Khoá cache / hàng đợi / lưu trữ / tìm kiếm / kênh realtime / rate-limit mang tenant.
5. Job nền mang tenant trong payload, đặt lại ngữ cảnh trước khi chạy.
6. Đăng nhập hộ: lý do + hạn + nhật ký kiểm toán.
7. Xuất / xoá được toàn bộ dữ liệu một tenant.
8. Giới hạn theo gói kiểm ở máy chủ tại từng chỗ dùng.

## 4. Test chéo tenant bắt buộc (vùng K)

Dựng hai tenant A, B với dữ liệu giống hệt nhau; mọi endpoint đọc/sửa/xoá gọi bằng người dùng A với id của B ⇒ từ chối
có tên; danh sách / tìm kiếm / xuất của A ⛔ chứa bản ghi nào của B. Một test tham số hoá trên danh sách endpoint — thêm
endpoint mà quên khai vào danh sách ⇒ ĐỎ (so tập route thật với tập đã khai).

## 5. Bộ đột biến mẫu (vùng K)

```toml
zone = "K"
cmd = "PYTHONPATH=src python -m pytest -q tests/tenancy"

[[mutant]]
id = "tenant-q-01"
file = "src/repositories/invoices.py"
find = "WHERE tenant_id = %s AND id = %s"
replace = "WHERE id = %s"
why = "bỏ điều kiện tenant ⇒ tenant A đọc được hoá đơn của tenant B"

[[mutant]]
id = "tenant-cache-01"
file = "src/cache/keys.py"
find = "return f\"{tenant_id}:{name}:{key}\""
replace = "return f\"{name}:{key}\""
why = "khoá cache thiếu tenant ⇒ B nhận dữ liệu cache của A"

[[mutant]]
id = "tenant-ctx-01"
file = "src/tenancy/middleware.py"
find = "tenant_id = session.tenant_id"
replace = "tenant_id = request.headers.get(\"X-Tenant-Id\", session.tenant_id)"
why = "ngữ cảnh tenant lấy từ header tự khai ⇒ đổi header là sang tenant khác"
```
