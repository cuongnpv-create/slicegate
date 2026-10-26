# ECOMMERCE_GUIDE — luật ngành thương mại điện tử ({{PROJECT}})

Bổ sung cho `GATE_PROTOCOL`. Gate chủ: `checkout-lead` (vùng T), `pricing-lead` (vùng F).

## 1. Vùng rủi ro gợi ý (khai trong `slicegate.toml`)

| Vùng | Mã điển hình | Ví dụ regex |
|---|---|---|
| T | đặt hàng, thanh toán, webhook, hoàn tiền, trừ kho | `'^src/(orders?|checkout|payments?|refunds?|inventory|webhooks?)/'` |
| K | tài khoản, phiên, quyền quản trị cửa hàng, khoá cổng thanh toán | `'^src/(auth|accounts?|admin)/'` |
| F | giá, khuyến mãi, mã giảm giá, thuế, phí ship | `'^src/(pricing|promotions?|coupons?|tax|shipping)/'` |

## 2. Máy chặn của gói

| Guard | Chặn |
|---|---|
| `money_float` | tiền khai kiểu float / ép float / cột FLOAT·REAL·DOUBLE / `parseFloat` tên tiền |
| `pci_scope` | cột hoặc trường lưu số thẻ, CVV, dải từ |

## 3. Luật cứng

1. **Tiền chính xác:** số nguyên đơn vị nhỏ nhất (`amount_minor BIGINT` + `currency CHAR(3)`) hoặc `Decimal` /
   `NUMERIC(p,s)`. Tiền luôn đi kèm tiền tệ.
2. **Một nơi tính giá:** giá, giảm giá, thuế, phí tính ở máy chủ trong một mô-đun; giao diện chỉ hiển thị.
3. **Máy trạng thái đơn tường minh**, chuyển qua một hàm; chuyển sai ⇒ từ chối có tên.
4. **Idempotency** cho mọi lệnh thu tiền và hoàn tiền; webhook xác minh chữ ký + chống phát lại + chịu trùng/sai thứ tự.
5. **Tổng khớp:** tổng các dòng = tổng đơn = số thu = số ghi sổ; tổng hoàn ≤ tổng thu.
6. **Tồn kho nguyên tử**, giữ hàng có hạn.
7. **PCI:** ⛔ lưu số thẻ / CVV; chỉ token + last4 + hãng.
8. **Dữ liệu cá nhân** (địa chỉ, điện thoại): thu tối thiểu, có hạn lưu, ⛔ ra log.

## 4. Bộ đột biến mẫu (vùng T)

```toml
zone = "T"
cmd = "PYTHONPATH=src python -m pytest -q tests/checkout"

[[mutant]]
id = "pay-idem-01"
file = "src/payments/capture.py"
find = "idempotency_key=order.payment_key"
replace = "idempotency_key=None"
why = "bỏ khoá idempotency ⇒ thử lại sau lỗi mạng trừ tiền khách hai lần"

[[mutant]]
id = "refund-cap-01"
file = "src/refunds/service.py"
find = "if refunded + amount > captured:"
replace = "if False:"
why = "bỏ trần hoàn tiền ⇒ hoàn nhiều hơn số đã thu"

[[mutant]]
id = "webhook-sig-01"
file = "src/webhooks/provider.py"
find = "if not verify_signature(raw_body, header_sig, secret):"
replace = "if False:"
why = "bỏ kiểm chữ ký webhook ⇒ ai cũng giả được sự kiện 'đã thanh toán'"
```
