# LEDGER — làn `{{LANE_NAME}}` (tiền tố `{{LANE_PREFIX}}`) · {{PROJECT}}

Phán gate, append-only. Người ghi DUY NHẤT: phiên điều phối của làn. Số do `gatekit ledger alloc` cấp.
Entry ĐÓNG và cũ hơn `ledger.roll_keep_days` được `gatekit ledger roll` chuyển sang `archive/` — sổ sống chỉ còn việc đang mở.

Khuôn entry:

```
## {{LANE_PREFIX}}-L<n> — <G-IN|G-OUT|G-DECIDE> <mã lát> · <YYYY-MM-DD>
Trạng thái: OPEN | CLOSED
Vai: <gate> · rev đo: <sha> · ghi sổ: điều phối
VERDICT: APPROVE | APPROVE-WITH-CONDITIONS | REJECT | NEEDS-INFO
Thẩm định: …
Điều kiện:
- **{{LANE_PREFIX}}-C<n>** [OPEN] <khuyết tật MÃ nó chặn> · đo: <lệnh/test> · vùng: <T|K|F|khác>
Nhận xét (không phải điều kiện): …
LỆNH KẾ / GIAO VIỆC: ① … ② …
```

---
