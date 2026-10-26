# SESSION_PROTOCOL — buổi làm việc, vai, phiên điều phối ({{PROJECT}})

## 1. Sơ đồ vai

```
Owner — ra lệnh, quyết điều chỉ owner quyết; lời owner ghi NGUYÊN VĂN vào docs/governance/OWNER_WORDS.md
  └─ PHIÊN ĐIỀU PHỐI (một phiên) — lập gói, cấp số, gọi gate/agent, đo lại, ghi sổ, đưa lát vào main; ⛔ tự viết mã lát
       ├─ VAI TẠO RA (⛔ phán): product-director (BE: làm gì, quy tắc, hợp đồng API) · design-director (FE: trông ra sao)
       ├─ AGENT LÀM LÁT — mỗi lát MÃ một agent, một worktree
       └─ GATE (⛔ viết thay): {{GATES_INLINE}}
```

- **Người TẠO ≠ người GÁC.** Giám đốc viết đặc tả, ⛔ phán; gate phán, ⛔ viết thay.
- **Ranh giới BE ↔ FE:** BE viết tính năng, quy tắc, máy trạng thái, hợp đồng API, mã từ chối có tên; FE đọc hợp đồng ấy
  để vẽ màn — thiếu trường ⇒ ghi "yêu cầu cho BE", ⛔ tự nghĩ API.
- Agent làm lát ⛔ gọi giám đốc; cần đặc tả mà chưa có ⇒ báo điều phối ⇒ điều phối gọi (theo lời owner).

## 2. Một buổi

| # | Ai | Việc | Đầu ra |
|---|---|---|---|
| 1 | điều phối | đọc `CLAUDE.md §0` | **Bản tin sáng**: hôm qua xong gì (SHA), ≤ 3 câu owner phải quyết, kế hoạch buổi |
| 2 | owner | trả lời / sửa kế hoạch; im ⇒ chạy theo kế hoạch | lời owner vào `OWNER_WORDS.md` |
| 3 | điều phối — **HỌP KẾ HOẠCH, CHỈ KHI CẦN** | mở pha · đổi lộ trình · đặc tả tồn < 2 lát · owner ra lệnh sản phẩm mới. Thứ tự: product-director → chief-architect → design-director | đặc tả + GIAO VIỆC |
| 4 | điều phối + agent + gate | lát theo `CLAUDE.md §3`; sau mỗi G-OUT: chief-architect GIAO VIỆC | sổ + `STATUS` |
| 5 | điều phối | G-OUT kết phiên | **Bản tin tối**: lát xong + SHA, việc dở, câu chờ owner |

## 3. Phiên điều phối

1. **Một phiên điều phối** mở ở cây `main`. Nó lập gói, cấp số, gọi gate/agent, đo lại, ghi sổ, commit. ⛔ tự viết mã lát.
2. **Người ghi sổ DUY NHẤT** cho mỗi làn sổ (`ledger.lanes`): gate và agent trả phán/báo cáo bằng chữ, điều phối nối
   nguyên văn vào sổ (`ghi sổ: điều phối`). Có nhiều phiên song song ⇒ chia làn, mỗi phiên chỉ ghi làn của mình;
   tệp chung (`STATUS`, `OWNER_WORDS`, `CLAUDE.md`) mỗi bên chỉ thêm khối của mình.
3. **Trần đồng thời:** ≤ `{{MAX_CODE_SLICES}}` lát MÃ đang viết · ≤ `{{MAX_AGENTS}}` agent tổng (gate, khảo sát chạy thêm
   trong giới hạn này). Bị giới hạn API cắt ⇒ hạ số agent, ⛔ dừng giữa lát. Việc chạy dài (đo 24 h, phát lại) chạy
   nền, ⛔ chiếm chỗ agent.
4. **Mỗi lát MÃ một worktree** (`worktree_per_slice = {{WORKTREE}}`): `.claude/worktrees/<mã-lát>`, nhánh `slice/<mã-lát>`.
   Ghi bộ ba **mã lát ↔ nhánh ↔ đường dẫn** vào `STATUS`. Agent chỉ sửa trong worktree của mình; ⛔ sửa tệp sổ.
   Lát vào main sau G-OUT: rebase lên `main` mới nhất → `gatekit check` + test phần bị ảnh hưởng → `merge --ff-only`
   (⛔ merge commit) → commit sổ + STATUS mang CÙNG mã lát → **gỡ ngay** worktree + nhánh.
5. **Commit xếp hàng:** mỗi lúc một lát vào `main`, thứ tự FIFO. Lát khai trước byte đầu danh sách **tệp chung** sẽ chạm
   (catalog i18n, mã lý do, manifest, số migration) để tránh hai lát va nhau. Tệp sinh máy ⛔ giải xung đột tay — sinh lại.
6. **Gate độc lập:** prompt gate giao tệp, diff, toạ độ, lệnh đo — ⛔ kết luận của điều phối. Báo cáo đầy đủ của agent
   ghi ra NGOÀI repo (vd `../meta/reports/<mã-lát>/<vai>-<n>.md`); điều phối giữ bản tóm tắt.
7. **Bộ nhớ = `docs/STATUS.md`.** Sau mỗi G-OUT ghi khối mới: SHA, mã sổ đã dùng, việc dở, GIAO VIỆC kế. Ngữ cảnh gần đầy
   ∨ chạm đồng hồ ⇒ kết phiên + bàn giao, ⛔ mở lát mới.
8. **Bước vào đo được:** `git status --porcelain` = 0 dòng (WIP của phiên khác ⇒ ⛔ dọn hộ, ⛔ stash; báo owner) ·
   `git worktree list` chỉ còn worktree có chủ ghi ở STATUS · đã đọc khối đầu STATUS.
9. ⛔ `--no-verify`. Hook ĐỎ ⇒ sửa trong worktree của lát.

## 4. Bộ test theo làn — CẤM GỘP

| Tầng | Nội dung | Chạy ở |
|---|---|---|
| 0 | guard toàn cây (`gatekit check`) | `pre-commit` (nhanh) + `pre-push` (đủ + neo đột biến) |
| 1 | test thuần của làn | mỗi lát, ≤ ngân sách |
| 2 | test DB / dịch vụ của làn (container dùng một lần, dọn sạch kể cả volume) | lát chạm DB |
| 3 | phát lại / E2E (đắt) | chỉ làn sở hữu |
| 4 | test HỢP ĐỒNG giữa làn (BE↔FE, dữ liệu↔BE) | bộ tầng 1 của CẢ hai làn ở ranh giới |

Mỗi làn một manifest (`tests.manifests`), cột: `đường dẫn · làn · tầng · ghi chú`. `test_wiring` bắt test tồn tại mà
không có manifest. Ngân sách: `GATE_PROTOCOL §6`.

## 5. Giới hạn cố định

- Họp kế hoạch **khi cần**, ⛔ mặc định mỗi sáng.
- Lát quản trị (0 tệp mã sản xuất) ≤ `{{GOV_MAX}}` liền nhau; sau đó ≥ `{{CODE_AFTER_GOV}}` lát MÃ (`gatekit quota`).
- Mọi đề xuất thêm thủ tục / sổ / guard phải khai **nó chặn khuyết tật MÃ nào**; ⛔ khai được ⇒ ⛔ làm.
