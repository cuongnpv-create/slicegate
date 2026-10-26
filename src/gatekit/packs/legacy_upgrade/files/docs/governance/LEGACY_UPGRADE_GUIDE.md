# LEGACY_UPGRADE_GUIDE — nâng cấp từ hệ cũ ({{PROJECT}})

Nguyên tắc nghiệm thu: **hệ cũ làm được thì hệ mới làm được; hệ cũ không làm được thì hệ mới làm được.**
Mặc định **GIỮ + NÂNG CẤP** mã cũ (chép có ghi nguồn rồi sửa). Viết lại chỉ khi có bằng chứng thuộc danh sách đóng §2.

## 1. Năm nguyên tắc (thứ tự ưu tiên khi xung đột)
1. Không mất luật nghiệp vụ / ca biên của hệ cũ khi chuyển — mỗi chức năng có quyết định có tên.
2. ⛔ import mã hệ cũ (`legacy_import_ban`); mang sang = CHÉP có ghi nguồn + test ở hệ mới.
3. Hành vi cũ được chụp bằng test (characterization) TRƯỚC khi sửa.
4. Nâng cấp là MỤC CÓ TÊN (vd "U-03 thêm chiều tenant vào khoá"), ⛔ "viết lại cho đẹp".
5. Đo tiến độ bằng số: tệp có nhãn nguồn / tổng tệp; chức năng có quyết định / tổng chức năng.

## 2. Nhãn phán cho mỗi tệp hệ mới
| Nhãn | Nghĩa | Bằng chứng ở G-OUT |
|---|---|---|
| `CHÉP` | mang nguyên | dòng nguồn ngay trên khối chép |
| `NÂNG` | mang + sửa | dòng nguồn + mã mục nâng cấp |
| `REPLACE` | viết lại | bằng chứng thuộc danh sách đóng dưới + mã phán |
| `MỚI` | hệ cũ không có | lệnh `grep` trên hệ cũ chứng minh không có |

**Danh sách ĐÓNG cho REPLACE:** ⒜ mã cũ vi phạm ràng buộc cứng của hệ mới có bằng chứng (vd giao diện gọi thẳng dịch vụ
ngoài, tính nghiệp vụ ở client, dữ liệu giả) · ⒝ công thức cũ sai sách (kiểm toán có số) · ⒞ phụ thuộc đã chết / không
vá được bảo mật · ⒟ owner phán viết lại phần ấy.

**Quyết định chức năng:** MANG · MANG-SỬA · GỘP · HOÃN (điều kiện) · BỎ (lý do).

## 3. Nhãn nguồn
```
# {{LEGACY_LABEL}}<rev hoặc nogit-md5:<8 ký tự>>:<tệp>:<dòng-đầu>-<dòng-cuối>
# nâng: U-<n> <mô tả mục nâng cấp>
```
(TS/JS dùng `//`). Đặt NGAY trên khối chép. G-OUT đo: tệp nhãn `CHÉP`/`NÂNG` mà `grep -c "{{LEGACY_LABEL}}"` = 0 ⇒ ĐỎ.

## 4. Bảng "Mang hệ cũ" trong G-IN
| Tệp hệ mới | Nhãn | Nguồn hệ cũ (tệp:dòng) | Mục nâng cấp | Test chụp hành vi |
|---|---|---|---|---|

## 5. Một lát nâng cấp
1. Kiểm kê chức năng của phân hệ cũ (tệp:dòng) → quyết định có tên cho từng chức năng.
2. Viết test chụp hành vi cũ (đầu vào → đầu ra thật của hệ cũ) — kỳ vọng nguồn NGOÀI mã mới.
3. Chép có nhãn → chạy test chụp (XANH) → áp từng mục nâng cấp → test của mục.
4. G-OUT: bảng "Mang hệ cũ" + đo nhãn + chức năng không mang có quyết định BỎ/HOÃN.
