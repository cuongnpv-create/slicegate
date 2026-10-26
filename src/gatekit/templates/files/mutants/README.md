# Bộ đột biến

Mỗi tệp `*.toml` là một bộ (khai ở `tests/manifest.tsv`). Khuôn:

```toml
zone = "K"
cmd = "python -m pytest -q tests/test_auth.py"

[[mutant]]
id = "auth-01"
file = "src/auth/login.py"
find = "if not verify(password, user.hash):"   # neo: đúng 1 lần trong tệp
replace = "if False:"
why = "gỡ cổng kiểm mật khẩu ⇒ ai cũng đăng nhập được"
```

Lệnh chạy TRONG BẢN SAO: phải import mã của bản sao — gói cài `pip -e` trỏ về checkout gốc làm mọi đột biến
"sống" giả; Python thêm `PYTHONPATH=src` vào `cmd`.

Chạy: `gatekit mutants run` (đủ) · `gatekit mutants run --changed main` (theo diff) · `MUT_ONLY=auth-01 gatekit mutants run`.
Kiểm neo (rẻ, có trong pre-push): `gatekit mutants anchors`.
