# REQUIREMENTS — LAN Chat & File Sharing

> **Nguồn:** `LAN_Chat_Socket_Project.docx` (5 trang), mục 1–9. Đây là **bảng theo dõi**, không thay thế đề gốc. Mọi ô hiện **chưa hoàn thành/chưa kiểm thử**. Chỉ đánh dấu `[x]` khi chức năng đã được kiểm thử thực tế và có thể chứng minh trong demo.

## 1. Điều kiện chung và mục tiêu

- [ ] Nhóm 2–3 sinh viên (**nhóm đã chốt: 3 người**).
- [ ] Giao tiếp mạng bằng Socket API gốc của ngôn ngữ (**nhóm chọn Python 3, module `socket`**).
- [ ] Giao diện console hoặc GUI (**nhóm ưu tiên console ban đầu**).
- [ ] Ứng dụng P2P: mọi người chạy **cùng một chương trình**, mỗi peer vừa chủ động kết nối vừa chấp nhận kết nối.
- [ ] Chạy thử trên cùng LAN/Wi-Fi; có thể dùng nhiều instance trên một máy khi phát triển. **Demo cuối ít nhất 2 máy**.
- [ ] Sử dụng **UDP cho discovery/status** và **TCP cho chat/file transfer**.

## 2. Chức năng bắt buộc — DOCX §3

### §3.1 Peer Discovery (UDP) — rubric UDP: 15 điểm cùng §3.2

- [ ] **UDP-01:** Mỗi peer broadcast presence **3 giây/lần** trên **một UDP port cố định** (ví dụ 9999).
- [ ] **UDP-02:** Mỗi peer lắng nghe cổng UDP đó và quản lý danh sách online gồm **name, IP, TCP port, status**.
- [ ] **UDP-03:** Không nhận presence từ peer trong **10 giây** thì loại peer khỏi danh sách (timeout).
- [ ] **UDP-04:** Console thông báo khi peer **online** hoặc **offline**.

### §3.2 Online Status (UDP)

- [ ] **STATUS-01:** Người dùng có thể đổi trạng thái `online` hoặc `away`.
- [ ] **STATUS-02:** Presence broadcast chứa status; status hiển thị trong danh sách online.

### §3.3 Chat (TCP) — rubric TCP chat: 20 điểm

- [ ] **CHAT-01:** Người dùng chọn peer online; ứng dụng mở TCP connection đến peer được chọn.
- [ ] **CHAT-02:** Hai phía gửi tin **bất kỳ lúc nào**; một dòng là một tin nhắn; gửi nhiều dòng liên tục.
- [ ] **CHAT-03:** Tin đến phải hiển thị **ngay cả khi người dùng đang gõ**.
- [ ] **CHAT-04:** Tin từ peer **không phải đối tác chat hiện tại** được lưu và thông báo với **unread count**.
- [ ] **CHAT-05:** Xử lý **nhiều peer đồng thời**, không chỉ một kết nối rồi đợi theo lượt.

### §3.4 File Transfer (TCP) — rubric file: 15 điểm

- [ ] **FILE-01:** Gửi file cho **đối tác chat hiện tại** bằng TCP.
- [ ] **FILE-02:** Hiển thị **tiến độ truyền (%)**.
- [ ] **FILE-03:** File nhận được lưu vào thư mục `downloads/`.
- [ ] **FILE-04:** **Chat vẫn hoạt động trong lúc truyền file** (đề yêu cầu truyền file trên thread riêng).

## 3. Lệnh và giao diện — DOCX §4

### §4.1 Các lệnh (không bỏ sót)

- [ ] `/list` — hiển thị **số thứ tự, name, IP, status**.
- [ ] `/chat <name|number>` — mở chat TCP với peer theo tên hoặc số thứ tự.
- [ ] `<any text>` — gửi văn bản cho đối tác chat hiện tại.
- [ ] `/send <file>` — gửi file cho đối tác chat hiện tại.
- [ ] `/leave` — đóng cuộc chat hiện tại.
- [ ] `/status <online|away>` — đổi trạng thái gửi qua UDP.
- [ ] `/help` — hiển thị toàn bộ lệnh.
- [ ] `/quit` — thoát chương trình.

**Quy tắc:** dòng bắt đầu bằng `/` là lệnh; văn bản thông thường là tin nhắn.

### §4.3 Nhận tin khi đang gõ — rubric UI: 15 điểm

- [ ] Tin đến **không làm mất/hỏng nội dung đã gõ nhưng chưa gửi**.
- [ ] Nếu làm console, tin được in lên phía trên dòng nhập và prompt cùng văn bản đang gõ được phục hồi.
- [ ] Đồng bộ output để nhiều thread không cùng in gây chồng lấn; nếu chọn GUI thì phải đạt hành vi tương đương.

**Gợi ý của đề (không bắt buộc chọn nguyên một file demo):** `prompt_toolkit` + `patch_stdout()`, hoặc đọc từng phím + buffer + redraw.

## 4. Kỹ thuật bắt buộc — DOCX §5

### §5.1 Concurrency / Thread Model

- [ ] Có cơ chế đồng thời cho **keyboard input, UDP broadcaster, UDP listener, TCP acceptor, TCP receiver theo peer và file sender theo lần truyền**.
- [ ] Không chặn UI hoặc các peer khác khi một socket chờ dữ liệu hay đang truyền file.
- [ ] Có lock bảo vệ **online-users list, chat histories và unread counters** (cũng cần bảo vệ các shared state tương tự).
- [ ] Đề cho phép **threads hoặc select/poll** khi quản lý nhiều kết nối; mô hình bảng thread trong đề là mô hình tham chiếu.

### §5.2 Application Protocol & Framing — rubric protocol: 10 điểm

- [ ] **Tự thiết kế** application-layer protocol cho presence, chat, file và kết thúc chat.
- [ ] UDP presence truyền trong **một datagram**, chứa các trường cần thiết.
- [ ] TCP là byte stream: **mọi thông điệp phải có header thể hiện type và length**.
- [ ] Receiver lặp `recv()` để đọc **đúng và đủ** `length` / `size` byte, không giả định một `recv()` bằng một message.
- [ ] Mô tả chính xác định dạng giao thức **nhóm thực sự triển khai** trong báo cáo.

**Đề chỉ đưa ví dụ**, không bắt buộc sao chép nguyên mẫu: `HELLO|<name>|<tcp_port>|<status>`, `MSG|<length>|<utf-8 text>`, `FILE|<filename>|<size_in_bytes>|<raw file bytes>`, `BYE|`.

### §5.3 Error Handling — rubric stability: 10 điểm

- [ ] Peer đóng kết nối hoặc crash → có thông báo và trả về prompt chính phù hợp.
- [ ] Kết nối tới peer đã offline → thông báo lỗi, chương trình không crash.
- [ ] File không tìm thấy / truyền file bị gián đoạn → thông báo lỗi và **xóa file nhận dở**.
- [ ] Lệnh sai → hiển thị hướng dẫn ngắn, không crash.

## 5. Milestones — DOCX §6

| Milestone | Phạm vi bắt buộc | Checkpoint theo đề |
|---|---|---|
| **1** | TCP echo client/server; UDP send/receive test | Demo được **cả hai chương trình** |
| **2** | UDP discovery, danh sách online, `/list`, `/status` | Peer xuất hiện/biến mất trên **2+ máy** |
| **3** | TCP chat với `/chat`, `/leave`, framing và threads/select/poll | **Hai người chat hai chiều** |
| **4** | Typing-while-receiving UI; file transfer có progress | **Gửi file trong khi vẫn chat** |
| **5** | Error handling, testing, report, demo | **Nộp bài cuối** |

## 6. Deliverables — DOCX §7

- [ ] **Source code + README** hướng dẫn **install, run, test**.
- [ ] **Báo cáo 5–10 trang:** architecture, thread model, protocol format, **problems faced and solutions**.
- [ ] **Ảnh Wireshark:** UDP broadcast và TCP **three-way handshake** (SYN → SYN-ACK → ACK), kèm giải thích ngắn.
- [ ] **Live demo 10 phút trên ít nhất 2 máy tính**.

**Thông tin bổ sung do nhóm nhận được:** thời hạn khoảng **5–6 tuần**, có **vấn đáp**, và **báo cáo không đưa source code vào**. Đây là thông báo bổ sung của lớp, không phải nội dung được ghi chi tiết trong DOCX; cần giữ đúng nếu giảng viên xác nhận.

## 7. Rubric chính thức — DOCX §8

| Tiêu chí | Điểm |
|---|---:|
| UDP discovery, online list, status | **15** |
| TCP chat (send/receive at any time, multiple peers) | **20** |
| File transfer with progress, saved correctly | **15** |
| Console UI không phá dòng nhập **hoặc GUI** | **15** |
| Protocol design and message framing | **10** |
| Error handling and stability | **10** |
| Report | **10** |
| Demo and code quality | **5** |
| **Tổng** | **100** |

## 8. Gợi ý tham khảo — DOCX §9 (không phải tính năng bắt buộc mới)

- Khi thử trên một máy, chạy nhiều instance với TCP port khác nhau.
- Có thể dùng netcat để kiểm tra nhanh TCP/UDP.
- Demo UDP nhiều instance gợi ý `SO_REUSEADDR`/`SO_REUSEPORT` và địa chỉ broadcast loopback khi phù hợp hệ điều hành.
- Kiểm tra Windows Firewall để bảo đảm UDP broadcast được nhận.
- Tài liệu tham khảo: Beej's Guide, Python socket/threading documentation và các demo giảng viên cung cấp.

---

**Quy tắc theo dõi:** đánh dấu `[x]` khi đã chạy test đúng yêu cầu, ghi lại ai kiểm thử, ngày, kết quả và bằng chứng trong GitHub Issue/nhật ký nhóm. **Push code chưa đồng nghĩa đã hoàn thành.**
