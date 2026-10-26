# HIẾN PHÁP — {{PROJECT}} (Tầng 0)

Điều luật tối cao. Mỗi điều ghi nơi máy chặn; điều chưa có máy chặn là **DỰ THẢO** (Điều 7).

## Điều 1 — Một nguồn sự thật
Mỗi sự thật có đúng một chủ (một tệp, một bảng, một hằng). Bản sao chỉ được sinh máy từ chủ, kèm kiểm khớp.

## Điều 2 — Mọi thứ là thực thể có định danh
Thực thể nghiệp vụ có định danh ổn định, vòng đời rõ ràng (máy trạng thái), ⛔ suy ra từ chuỗi hiển thị.

## Điều 3 — Năng lực, ⛔ vai trò cứng
Quyền thao tác kiểm theo năng lực được cấp, ⛔ theo tên vai viết cứng trong mã. Thiếu năng lực ⇒ **từ chối có tên**
(mã lý do), ⛔ `return None`, ⛔ giả vờ làm được.

## Điều 4 — Mọi thao tác rủi ro đều kiểm toán được
Thao tác chạm tiền, quyền, dữ liệu người dùng ghi nhật ký: ai · lúc nào · cái gì · kết quả. Công tắc chế độ nguy hiểm
mặc định ĐÓNG (fail-closed).

## Điều 5 — Mỗi màn hình có một khuôn
Màn hình thuộc một trong các khuôn trang đã định nghĩa (tổng quan · danh sách · chi tiết · thao tác); trạng thái trống,
lỗi, đang tải là bắt buộc, ⛔ dữ liệu giả.

## Điều 6 — Miền dẫn dắt hiện thực
Luật nghiệp vụ sống ở tầng miền phía máy chủ; giao diện ⛔ tính nghiệp vụ, ⛔ gọi thẳng dịch vụ ngoài.

## Điều 7 — Quản trị phải máy thi hành được
Luật quan trọng có máy gác (`gatekit check`), có selftest ca âm, chạy ở hook và CI. Guard mới chỉ đẻ khi lớp lỗi đã nổ
≥ 3 lần thật (`GUARD_CATCH_LOG.tsv`) và phải khai khuyết tật mã nó chặn. Guard 0 lần bắt lâu ngày = ứng viên gỡ.
{{#pack i18n}}

## Điều 8 — Bản địa hoá từ đầu
Mọi chữ người dùng đọc đi qua catalog, đủ mọi ngôn ngữ trong CÙNG lát thêm chữ ấy. Máy chủ trả
`{code, message_key, params}`, ⛔ trả câu. Số / tiền / ngày theo locale và múi giờ người dùng. ⛔ hiện nguyên văn lỗi của
dịch vụ ngoài — quy về mã lý do rồi dịch. Máy chặn: `locale_parity`.
{{/pack}}
{{#pack multi_provider}}

## Điều 9 — Nhà cung cấp là tường minh
Tên nhà cung cấp chỉ sống trong bộ chuyển của nó; mọi khoá / bảng / kênh mang chiều nhà cung cấp (hoặc tenant).
Máy chặn: `provider_name_scope`, `partition_key_scope`.

## Điều 10 — Ý định → định tuyến → bộ dịch
Tầng nghiệp vụ phát ý định không biết nhà cung cấp; tầng định tuyến kiểm năng lực; bộ dịch của từng nhà cung cấp làm
phần còn lại. So NGHĨA (mã lý do), ⛔ so mã lỗi thô của nhà cung cấp.

## Điều 11 — Chưa biết ≠ Không
Năng lực có 4 giá trị `YES · NO · UNKNOWN · EMULATED`; `UNKNOWN ≠ NO`. Ghi đè khai báo của thư viện chỉ khi có phép đo
kèm ngày.
{{/pack}}
{{#pack ecommerce}}

## Điều 12 — Tiền là chính xác
Tiền là số nguyên đơn vị nhỏ nhất hoặc thập phân chính xác, luôn đi kèm tiền tệ; ⛔ số thực dấu phẩy động. Tổng các
dòng = tổng đơn = số thu = số ghi sổ. Dữ liệu thẻ không nằm trong hệ (chỉ token). Máy chặn: `money_float`, `pci_scope`.
{{/pack}}
{{#pack saas_multitenant}}

## Điều 13 — Khách thuê là tường minh
Mỗi request, mỗi job, mỗi khoá cache và mỗi dòng dữ liệu khách thuộc đúng một tenant, lấy từ phiên đã xác thực. Truy vấn
không lọc tenant là lỗi, kể cả khi id khó đoán. Máy chặn: `tenant_scope`, `tenant_rls`.
{{/pack}}
