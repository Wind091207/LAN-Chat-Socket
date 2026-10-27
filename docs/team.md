# Team & Git workflow (3 thành viên)

> Chưa điền tên thành viên; không mặc định leader là owner của tất cả công việc.

## 1. Thành viên

| Vai trò | Tên / GitHub | Owned modules | Review chính |
|---|---|---|---|
| **A — Discovery & CLI** | **[Điền]** | `discovery.py`, `peer_registry.py`, `cli.py` | C review A |
| **B — TCP & Protocol** | **[Điền]** | `protocol.py`, `connections.py`, `chat.py` | A review B |
| **C — File & QA** | **[Điền]** | `file_transfer.py`, test evidence coordination | B review C |
| **Shared** | **A+B+C** | `app.py`, `state.py`, `config.py`, entrypoint, report, integration | Cross-review |

**Nhìn rubric:** A điều phối UDP 15 + UI 15; B điều phối TCP 20 + framing 10; C điều phối File 15 + test stability 10. Report 10 và demo/code 5 **chung**, không giao hết cho C. Số điểm này không phải điểm riêng của từng sinh viên.

## 2. Owner vs reviewer

- **Owner** (người chịu trách nhiệm đầu việc): làm rõ yêu cầu, thiết kế, code, viết test, chạy test, bổ sung tài liệu và phản hồi nhận xét trên PR.
- **Reviewer** (người kiểm tra): đọc diff, đối chiếu DOCX, xem test/evidence, kiểm tra interface chung, `Approve` hoặc `Request changes`.
- Reviewer **không tự động có trách nhiệm viết code thay owner**. Nếu cần hỗ trợ, mở pair-programming commit và ghi công sức trong Issue/PR.
- **Protocol/Shared API/Shared state:** A, B, C cùng duyệt trước khi chốt vì ảnh hưởng mọi module.

## 3. GitHub repository setup (chỉ làm một lần)

**Đường dễ nhất với bộ starter này:**

1. Tạo **private repository rỗng** trên GitHub (không thêm README/.gitignore nếu dự định push nguyên bộ starter từ máy).
2. Giải nén starter. Vào thư mục chứa `README.md`.
3. Chạy:

```bash
git init -b main
git add .
git commit -m "docs: initialize requirements and team workflow"
git remote add origin https://github.com/OWNER/LAN-Chat-Socket.git
git push -u origin main
```

4. Mời hai thành viên làm **collaborators** và yêu cầu họ clone.

**Nếu GitHub repo đã được tạo sẵn cùng README/.gitignore:** clone repo trước, **copy các file starter vào repo đã clone rồi ghi đè/đối chiếu nội dung phù hợp**, không chạy `git init` lại hay tạo repo Git thứ hai lồng nhau. Khi GitHub tự tạo `.gitignore` Python, có thể merge các quy tắc bổ sung thay vì xóa template hữu ích.

## 4. Quy trình cho mỗi chức năng

```bash
git switch main
git pull origin main
git switch -c feature/ten-chuc-nang
# code và tự kiểm thử
git status
git diff
# git add tên các file thật đã sửa
git commit -m "feat: short meaningful change"
git push -u origin feature/ten-chuc-nang
```

- Tạo Issue trước khi code, đặt owner + reviewer, requirement IDs, test IDs và checklist.
- PR phải có link Issue, ảnh hưởng protocol/interface, test passed/failed, evidence và tài liệu đã cập nhật.
- Review xong, giải quyết nhận xét rồi mới merge `main`.
- Branch chính thức trên `main` không được nhận merge chỉ vì “chạy trên máy owner”.
- Không sửa/làm lại merge conflict bằng `git push --force` lên `main`.
- Nếu mở branch khác cần cập nhật thường xuyên từ `main` và giải quyết xung đột có chủ đích.

## 5. Trình tự phân chia thực tế theo milestones

| Mốc | A | B | C | Checkpoint review |
|---|---|---|---|---|
| M0 (nội bộ) | Draft UX và peer data | Draft protocol + socket choices | Draft test plan + report matrix | Cả ba duyệt docs |
| M1 (đề) | UDP send/recv + network setup | TCP echo client/server | Thread/CLI demo + test recording | A/B/C đều giải thích được TCP và UDP |
| M2 | UDP implementation | Hoàn thiện contract peer ↔ TCP | Test 2 máy, soát tài liệu | A PR, C review |
| M3 | UI integration + peer selection | TCP chat, framing, unread | Test nhiều peer, lỗi kết nối | B PR, A review |
| M4 | Input redraw | Tích hợp chat/file protocol | File transfer + progress | A/C PR, C/B review |
| M5 | Wireshark UDP, UI demo | Wireshark TCP, protocol section | Gom test, report QA | Cả nhóm demo và duyệt report |

## 6. Quy tắc chất lượng nhóm

- Mỗi người **tự ghi `docs/devlog.md`**, không viết báo cáo bằng hồi ức cuối kỳ.
- Mỗi tính năng phải có **Test ID + kết quả + evidence** trước khi gắn `VERIFIED`.
- Ít nhất một người khác phải đọc PR; thay đổi giao thức luôn có review cả ba.
- Sau một lần sửa shared contract, tất cả module phụ thuộc phải kiểm thử lại.
- Cả ba đều phải hiểu peer-to-peer, TCP/UDP, threading, framing để trả lời khi demo.
- Đừng đưa tài liệu giảng viên hoặc dữ liệu thật/private lên public repository khi chưa được phép.
