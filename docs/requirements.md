# Requirement Traceability Matrix (RTM)

**Nguồn bắt buộc:** `LAN_Chat_Socket_Project.docx` (5 trang). **Trạng thái khởi đầu tất cả yêu cầu: NOT STARTED / NOT TESTED.**

## 0. Cách dùng

- Mỗi ID gắn với điều khoản **trong DOCX gốc**, owner, reviewer, test và PR.
- **Status:** `NS` = not started; `IP` = in progress; `RV` = in review; `TEST` = awaiting test; `VERIFIED` = test đã chạy thành công và có evidence; `BLOCKED` = bị chặn.
- `TBD` nghĩa là chưa có PR/bằng chứng. Khi hoàn thành: sửa status, thêm `PR #...`, `Test: ...`, `Evidence: evidence/...`, tham chiếu phần báo cáo.
- Không dùng `VERIFIED` chỉ vì đã viết code hoặc chạy một ví dụ độc lập.

## A. Chức năng §3.1 — Peer Discovery (UDP) và §3.2 — Online Status (15 điểm chung)

| ID | Nguồn | Yêu cầu và điều kiện nghiệm thu | Owner / Reviewer | Test | Status / Evidence |
|---|---|---|---|---|---|
| UDP-01 | §3.1 | Mỗi peer broadcast presence **mỗi 3 giây**, cổng UDP cố định (ví dụ 9999) | A / C | T-UDP-01 | NS / TBD |
| UDP-02 | §3.1 | Mỗi peer **lắng nghe** cổng đó | A / C | T-UDP-01 | NS / TBD |
| UDP-03 | §3.1 | Quản lý peer: **name, IP, TCP port, status** | A / C | T-UDP-01 | NS / TBD |
| UDP-04 | §3.1 | Sau **10s không nghe thấy peer**, loại khỏi danh sách | A / C | T-UDP-02 | NS / TBD |
| UDP-05 | §3.1 | Console thông báo **peer online** | A / C | T-UDP-01 | NS / TBD |
| UDP-06 | §3.1 | Console thông báo **peer offline** | A / C | T-UDP-02 | NS / TBD |
| STATUS-01 | §3.2 | Người dùng đổi được **online/away** | A / C | T-UDP-03 | NS / TBD |
| STATUS-02 | §3.2 | Presence broadcast **chứa status** | A / C | T-UDP-03 | NS / TBD |
| STATUS-03 | §3.2 | `/list` **hiển thị status** đã cập nhật | A / C | T-UDP-03 | NS / TBD |

## B. Chức năng §3.3 — Chat (TCP), 20 điểm

| ID | Nguồn | Yêu cầu và điều kiện nghiệm thu | Owner / Reviewer | Test | Status / Evidence |
|---|---|---|---|---|---|
| CHAT-01 | §3.3 | Chọn peer **đang online** và TCP `connect()` tới peer đó | B / A | T-TCP-01 | NS / TBD |
| CHAT-02 | §3.3 | Gửi tin **mỗi dòng một message**, nhiều dòng | B / A | T-TCP-01 | NS / TBD |
| CHAT-03 | §3.3 | Gửi tin **bất kỳ lúc nào**, không theo lượt chờ nhau | B / A | T-TCP-01 | NS / TBD |
| CHAT-04 | §3.3 | Tin tới hiển thị **ngay cả khi đang gõ** | B + A UI / A + C | T-UI-01 | NS / TBD |
| CHAT-05 | §3.3 | Tin từ peer **không phải active partner** được **lưu** | B / A | T-TCP-02 | NS / TBD |
| CHAT-06 | §3.3 | Thông báo số **unread** của peer không active | B / A | T-TCP-02 | NS / TBD |
| CHAT-07 | §3.3, §8 | Có thể xử lý **nhiều peer** đồng thời | B / A | T-TCP-02 | NS / TBD |

## C. Chức năng §3.4 — File Transfer (TCP), 15 điểm

| ID | Nguồn | Yêu cầu và điều kiện nghiệm thu | Owner / Reviewer | Test | Status / Evidence |
|---|---|---|---|---|---|
| FILE-01 | §3.4 | Gửi file cho **current chat partner** | C / B | T-FILE-01 | NS / TBD |
| FILE-02 | §3.4 | Có **progress (%)** trong khi gửi | C / B | T-FILE-01 | NS / TBD |
| FILE-03 | §3.4 | File nhận lưu trong **`downloads/`** | C / B | T-FILE-01 | NS / TBD |
| FILE-04 | §3.4 | **Chat vẫn hoạt động khi truyền file**; transfer theo thread riêng | C / B | T-FILE-02 | NS / TBD |

## D. §4.1 — Giao diện lệnh (tất cả 8 mục)

| ID | Nguồn | Lệnh/hành vi | Owner / Reviewer | Test | Status / Evidence |
|---|---|---|---|---|---|
| CMD-01 | §4.1 | `/list` → **số thứ tự, name, IP, status** | A / C | T-CLI-01 | NS / TBD |
| CMD-02 | §4.1 | `/chat <name\|number>` → chọn peer bằng tên hoặc số | B + A CLI / A + C | T-CLI-01 | NS / TBD |
| CMD-03 | §4.1 | `<any text>` (không có `/`) → chat cho partner hiện tại | B + A CLI / A + C | T-CLI-01 | NS / TBD |
| CMD-04 | §4.1 | `/send <file>` → truyền cho partner hiện tại | C + A CLI / B + C | T-CLI-01 | NS / TBD |
| CMD-05 | §4.1 | `/leave` → đóng chat hiện tại | B + A CLI / A + C | T-CLI-01 | NS / TBD |
| CMD-06 | §4.1 | `/status <online\|away>` → đổi status qua UDP | A / C | T-CLI-01 | NS / TBD |
| CMD-07 | §4.1 | `/help` → hiển thị tất cả lệnh | A / C | T-CLI-01 | NS / TBD |
| CMD-08 | §4.1 | `/quit` → thoát ứng dụng | A+B+C / cross-review | T-CLI-01, T-ERR-05 | NS / TBD |

## E. §4.3 — Khi tin đến lúc đang nhập (UI, 15 điểm)

| ID | Nguồn | Yêu cầu và điều kiện nghiệm thu | Owner / Reviewer | Test | Status / Evidence |
|---|---|---|---|---|---|
| UI-01 | §4.3 | Dòng cuối là dòng nhập, thông điệp mới hiển thị ở trên trong phương án console | A / C | T-UI-01 | NS / TBD |
| UI-02 | §4.3 | Khi tin đến: **xóa dòng nhập, in thông điệp, vẽ lại prompt + phần đang gõ**, hoặc GUI cho hành vi tương đương | A / C | T-UI-01 | NS / TBD |
| UI-03 | §4.3 | Dùng lock bảo vệ screen output (các thread không in chồng) | A / C | T-UI-02 | NS / TBD |
| UI-04 | §4.3 | Không mất/kẹt text đang gõ trong tình huống thực tế | A / C | T-UI-01 | NS / TBD |

Đề nêu **2 hướng minh họa** cho console: (a) `prompt_toolkit + patch_stdout()`; (b) đọc từng phím + manual redraw (`option_b_manual_redraw.py`, `chat_redraw.cpp`). Đây là lựa chọn triển khai; không bắt buộc dùng cả hai.

## F. §5.1 — Concurrency / thread model

| ID | Nguồn | Tác vụ và/hoặc dữ liệu | Owner / Reviewer | Test | Status / Evidence |
|---|---|---|---|---|---|
| CONC-01 | §5.1 | Main đọc bàn phím, chạy lệnh, gửi tin | A / C | T-UI-01 | NS / TBD |
| CONC-02 | §5.1 | UDP broadcaster chờ chu kỳ **3s** | A / C | T-UDP-01 | NS / TBD |
| CONC-03 | §5.1 | UDP listener chờ datagram | A / C | T-UDP-01 | NS / TBD |
| CONC-04 | §5.1 | TCP acceptor chờ connection, khởi tạo receiver | B / A | T-TCP-02 | NS / TBD |
| CONC-05 | §5.1 | TCP receiver theo từng peer/socket | B / A | T-TCP-02 | NS / TBD |
| CONC-06 | §5.1 | File sender theo từng lần truyền, không chặn chat | C / B | T-FILE-02 | NS / TBD |
| CONC-07 | §5.1 | Đồng bộ **online list, chat histories, unread counters** | A+B / C | T-RACE-01 | NS / TBD |

> Mô hình thread ở §5.1 là ví dụ cụ thể của đề; §2 và §6 cũng cho phép concurrency bằng `select/poll`. Nếu đổi mô hình, báo cáo phải giải thích rõ thiết kế thực tế và vẫn đáp ứng responsiveness.

## G. §5.2 — Application-layer protocol / TCP framing (10 điểm)

| ID | Nguồn | Yêu cầu | Owner / Reviewer | Test | Status / Evidence |
|---|---|---|---|---|---|
| PROTO-01 | §5.2 | Nhóm **tự thiết kế giao thức**; ghi rõ wire format | B / A+C | T-PROTO-01 | NS / TBD |
| PROTO-02 | §5.2 | UDP presence là **một datagram** chứa name/port/status (ví dụ `HELLO\|...`) | A+B / C | T-UDP-01 | NS / TBD |
| PROTO-03 | §5.2 | TCP frame có header xác định **type và length** | B / A+C | T-PROTO-01 | NS / TBD |
| PROTO-04 | §5.2 | Receiver lặp `recv()` để đọc **đúng số byte** của text/file | B+C / A | T-PROTO-01, T-FILE-01 | NS / TBD |

## H. §5.3 — Error handling & stability (10 điểm)

| ID | Nguồn | Tình huống | Owner / Reviewer | Test | Status / Evidence |
|---|---|---|---|---|---|
| ERR-01 | §5.3 | Peer closes/crashes → notice + main prompt | B / A | T-ERR-01 | NS / TBD |
| ERR-02 | §5.3 | Connect đến peer offline → báo lỗi, **không crash** | B + A / C | T-ERR-02 | NS / TBD |
| ERR-03 | §5.3 | File not found / interrupted → báo lỗi, **xóa partial file** | C / B | T-ERR-03 | NS / TBD |
| ERR-04 | §5.3 | Invalid commands → short help | A / C | T-ERR-04 | NS / TBD |

## I. §6 — Milestones (checkpoint bắt buộc)

| ID | Nguồn | Công việc | Checkpoint | Owner | Status |
|---|---|---|---|---|---|
| M1 | §6 | TCP echo client/server + UDP send/receive | Demo cả hai chương trình | A+B+C | NS |
| M2 | §6 | UDP discovery, `/list`, `/status` | Peer hiện/mất trên **≥2 máy** | A | NS |
| M3 | §6 | TCP chat `/chat`, `/leave`, framing, threading (hoặc select/poll) | Hai người chat **hai chiều** | B | NS |
| M4 | §6 | Typing-while-receiving UI; file transfer + progress | **Gửi file trong lúc chat** | A+C | NS |
| M5 | §6 | Errors, testing, report, demo | Final submission | A+B+C | NS |

## J. §7 — Deliverables và §9 — Hints

| ID | Nguồn | Tiêu chí | Owner | Status |
|---|---|---|---|---|
| SUB-01 | §7 | Source code **và README** có hướng dẫn **install, run, test** | Cả ba | NS |
| SUB-02 | §7 | Report **5–10 trang**: architecture, thread model, protocol, problems & solutions | Cả ba | NS |
| SUB-03 | §7 | **Wireshark screenshots**: UDP broadcast và TCP 3-way handshake, giải thích ngắn | A (UDP) + B (TCP) | NS |
| SUB-04 | §7 | Live demo **10 phút**, **ít nhất 2 máy tính** | Cả ba | NS |
| HINT-01 | §9 | Có thể thử local với TCP port khác nhau (`--port 5001`, `--port 5002`) | Cả ba | N/A — hint |
| HINT-02 | §9 | `netcat` dùng làm test client; lưu ý quy tắc SO_REUSEADDR/REUSEPORT có thể khác theo OS | Cả ba | N/A — hint |
| HINT-03 | §9 | Kiểm tra Python Windows Firewall khi không nhận broadcast | Cả ba | N/A — hint |

## K. §8 — Grading rubric, không được bỏ mục nào

| Criterion | Điểm | Nơi lưu evidence |
|---|---:|---|
| UDP Discovery/Online/Status | 15 | `docs/testing.md`, `evidence/` |
| TCP Chat/Multiple Peers | 20 | `docs/testing.md`, `evidence/` |
| File Transfer/Progress | 15 | `docs/testing.md`, `evidence/` |
| Console input hoặc GUI | 15 | `docs/testing.md`, `evidence/` |
| Protocol/Framing | 10 | `docs/protocol.md`, framing tests |
| Error/Stable | 10 | `docs/testing.md`, failure tests |
| Report | 10 | `docs/report-plan.md`, final report |
| Demo/Code Quality | 5 | 10-minute script, PR review & code |
| **TOTAL** | **100** | |

## L. Nguyên tắc về yêu cầu và gợi ý

1. Tên file/module, `HELLO|...`, tách TCP file connection, sơ đồ thread, quy trình Git, các test ID đều có thể là **lựa chọn triển khai**.
2. Những thứ như 3s broadcast, 10s timeout, unread count, progress, `downloads/`, 5–10 trang, Wireshark, hai máy demo là **ràng buộc từ đề**.
3. Khi một yêu cầu thiếu chi tiết (username trùng, gói chồng, file collision, ACK...), nhóm **ghi quyết định** vào `docs/decisions.md`; không tự suy đoán đó là yêu cầu giảng viên.
