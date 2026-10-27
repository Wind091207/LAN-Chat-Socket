# Module ownership, trách nhiệm, giao diện và tài liệu học

> Các module dưới đây **chỉ là thiết kế dự kiến cho Python 3**, chưa triển khai. Đề không yêu cầu đúng các tên file. Chỉ tách module sau khi nhóm chốt data/protocol contracts trong `architecture.md` và `protocol.md`.

## Nguyên tắc chia module

- **Single responsibility:** mỗi module phụ trách một vấn đề rõ ràng.
- **Không phụ thuộc vòng:** `discovery.py` không cần import `chat.py`, và `file_transfer.py` không tự sửa peer table.
- **Giao tiếp qua interface đã thống nhất:** A/B/C không tự thay đổi schema hay frame rồi đòi người khác sửa theo.
- **App coordinator** chịu startup, shutdown và kết nối các module; không dồn mọi thuật toán vào `app.py`.
- **Chỉ một nguồn chân lý:** trạng thái peer, active chat, unread histories có chủ quản và quy tắc lock rõ ràng.
- **Test + docs nằm trong cùng PR**, reviewer đối chiếu `requirements.md` và bằng chứng thực tế.

## A1. `discovery.py` — UDP Discovery

- **Owner:** A; **Reviewer:** C.
- **Chức năng:** tạo socket UDP; broadcast presence đúng nhịp **3s**; lắng nghe presence; kiểm tra/parse datagram theo wire format đã duyệt; chuyển dữ liệu hợp lệ cho registry; xử lý lỗi mạng và đóng UDP socket.
- **Input:** local username, advertised TCP port, status, broadcast destination, UDP port, stop event, callback tới registry.
- **Output:** peer-present event / online announcement; lỗi mạng được hiển thị hoặc ghi log theo quy tắc nhóm.
- **Điểm cần chốt:** UDP port, broadcasting địa chỉ nào, có phản hồi presence ngay khi có peer mới không, nhận ra datagram từ mình thế nào, phiên bản format, hành vi nhiều instance trên Windows.
- **Nguồn bắt buộc:** `LAN_Chat_Socket_Project.docx` §3.1–3.2, §5.1, §9.
- **Học:** `udp_broadcast_demo.py`; `HDLT_Socket.pdf` pp. 4–5; `Seminar_Socket Programming.pdf` pp. 10–12; Python `socket` docs.
- **Test:** T-UDP-01, T-UDP-02, T-UDP-03; 2 máy cùng LAN ở milestone M2; ảnh Wireshark UDP.
- **Không làm:** tự mở TCP/chat/file, tự in trực tiếp từ nhiều thread mà không qua UI dispatcher.

## A2. `peer_registry.py` — Online list / status

- **Owner:** A; **Reviewer:** C.
- **Chức năng:** lưu `name`, `IP`, `tcp_port`, `status`, `last_seen`; thêm/cập nhật peer theo presence; phát hiện timeout **10s**; cấp snapshot cho `/list` và module chat; thông báo online/offline.
- **Input:** presence parsed từ `discovery.py`, thời gian monotonic, local config.
- **Output:** snapshot danh sách peer, peer lookup cho `/chat`, trạng thái sự kiện.
- **Điểm cần chốt:** khóa định danh peer không phụ thuộc chỉ vào tên, quy tắc username trùng, cách bỏ self-packet, tình huống peer khởi động lại/đổi IP/port, timer behavior.
- **Shared data:** khóa bảo vệ bảng peer và snapshot; không giữ lock khi network I/O blocking.
- **Nguồn:** DOCX §3.1–3.2; §5.1; kịch bản `Gioithieu_Huongdan_DoAnSocket.pdf`.
- **Test:** T-UDP-01/02/03/04 và snapshot consistency T-RACE-01.

## A3. `cli.py` — Console I/O / command routing

- **Owner:** A; **Reviewer:** C.
- **Chức năng:** đọc dòng nhập và phát command event; phân biệt text thường và `/command`; trình bày thông báo tin tới và progress; giữ nguyên text đang gõ; `/help`; đưa lệnh đến đúng module; hiển thị lỗi lệnh hợp lý.
- **Input:** UI events (peer online/offline, incoming chat, unread, transfer percent), user input.
- **Output:** `list/chat/send/leave/status/help/quit` và plain message commands cho app/owner xử lý.
- **Điểm cần chốt:** `prompt_toolkit` hoặc manual redraw, xử lý Unicode/tiếng Việt, mọi output đi qua một điểm đồng bộ, newline/scrolling, xử lý Ctrl+C/EOF.
- **Nguồn:** DOCX §4.1–4.3; `option_a_prompt_toolkit.py`, `option_b_manual_redraw.py`, `chat_redraw.cpp`.
- **Test:** T-CLI-01, T-UI-01, T-UI-02, T-ERR-04.
- **Không làm:** tự parse TCP frame, tự đọc file, tự quản lý peer table theo bản copy rời.

## B1. `protocol.py` — Application-layer protocol & TCP framing

- **Owner:** B; **Reviewers:** A + C (**bắt buộc cả hai khi đổi wire format**).
- **Chức năng:** định dạng/parse UDP presence và TCP frames theo spec nhóm; encode/decode UTF-8, loại thông điệp, payload length tính bằng **byte**; nhận đủ `length` bytes; kiểm tra bad header, truncated frame, giới hạn size.
- **Input:** structured app message; raw bytes/connection.
- **Output:** serialized bytes; parsed frame/message; lỗi format cụ thể.
- **Điểm cần chốt:** length encoding, delimiter hay binary length-prefix, endianness, type enum, max message/file metadata size, filename policy, response ACK nếu nhóm dùng, file-vs-chat frame routing.
- **Nguồn:** DOCX §5.2; `PythonNetBinder.pdf` trang tài liệu phần *Partial Reads/Writes*, *Data Reassembly*; Seminar PDF pp. 7–9; Python Socket HOWTO.
- **Test:** T-PROTO-01, 02, 03, T-FILE-01; so sánh payload byte-by-byte.
- **Cực kỳ quan trọng:** `recv(1024)` **không đảm bảo nhận một frame đầy đủ**; `sendall` cũng không báo đối tác đã lưu dữ liệu vào file.

## B2. `connections.py` — TCP lifecycle / multi-peer connections

- **Owner:** B; **Reviewer:** A.
- **Chức năng:** TCP listening socket, acceptor, outgoing `connect`, receiver lifecycle, peer handshake/identity, connection tracking, clean close, lỗi connect/refused/disconnect. Cung cấp connection interface cho `chat.py` và `file_transfer.py`.
- **Input:** address+TCP port từ registry, connection events.
- **Output:** connection established/closed events, safe send/receive hooks.
- **Điểm cần chốt:** nếu hai peer đồng thời connect thì tránh double connections thế nào; chat socket có được dùng lại không; xử lý peer đang nói chuyện với người khác; connection timeout; shutdown coordination.
- **Nguồn:** DOCX §3.3, §5.1, §5.3; Seminar PDF pp. 8–9, 17–24; `02_client.py`, `02_server.py`; `Demo_CSocket_thread` chỉ để so sánh.
- **Test:** T-TCP-01/02/03, T-ERR-01/02.

## B3. `chat.py` — Messaging / active peer / unread

- **Owner:** B; **Reviewer:** A.
- **Chức năng:** lệnh `/chat`, `/leave`; chat full-duplex; truyền MSG frame; routing tin tới đúng peer; lưu tin người không active và cập nhật unread count; hiển thị lịch sử khi đổi partner (theo kịch bản §4.2).
- **Input:** text command và parsed MSG từ connection receiver.
- **Output:** send MSG, UI incoming/unread events, active-peer change, history snapshot.
- **Điểm cần chốt:** buffer history sống trong RAM hay ghi file (không bắt buộc persistence); đồng bộ số unread; cách rời chat mà vẫn nhận tin từ peer khác; không block CLI.
- **Nguồn:** DOCX §3.3, §4.1–4.2; Seminar PDF pp. 13–24; `03_client.py`/`03_server.py` chỉ học nhiều client, **không sao chép kiến trúc server trung tâm**.
- **Test:** T-TCP-01/02/03, T-UI-01, T-RACE-01.

## C1. `file_transfer.py` — File transfer / progress / cleanup

- **Owner:** C; **Reviewer:** B.
- **Chức năng:** kiểm tra file nguồn; lấy metadata phù hợp; gửi file TCP thành chunk; tiến độ `%`; nhận file lưu dưới `downloads/`; chat hoạt động trong lúc transfer; phát hiện interrupted và xóa file dở.
- **Input:** `/send path`, active peer + connection/protocol APIs; metadata từ phía gửi.
- **Output:** progress events (cho UI), file hợp lệ trong downloads, success/error events.
- **Điểm cần chốt:** chung hay tách TCP connection so với chat (**khuyến nghị tách**, không bắt buộc); chunk size; giới hạn file; tên trùng; đường dẫn ngoài downloads; tên độc hại; cách xác nhận truyền đủ; việc kết thúc và dọn file tạm.
- **Nguồn:** DOCX §3.4, §5.1–5.3; `Gioithieu_Huongdan_DoAnSocket.pdf` tình huống tách connection; Python file I/O (`pathlib`) và Socket docs.
- **Test:** T-FILE-01/02/03/04, T-ERR-03.
- **Lưu ý:** không hiển thị `100%` như bằng chứng duy nhất của file lưu đúng; kiểm tra bytes/size/hash trong test.

## Shared S1. `state.py` — App state (A+B+C duyệt)

- **Chức năng dự kiến:** lưu trạng thái shared được phân vai sở hữu rõ, tránh nhiều bản dữ liệu mâu thuẫn. Tách snapshots/bounded locks.
- **Điểm phải chốt:** ai có quyền mutate `active_peer`, who owns unread counters, notification queue, stop event, lock ordering.
- **Nguồn:** DOCX §5.1; Python threading docs.
- **Test:** T-RACE-01, T-ERR-05.

## Shared S2. `app.py`, `config.py`, `__main__.py` — Lifecycle & integration

- **Chức năng dự kiến:** CLI startup, parse name/ports/config, start/stop background tasks, connect event routes giữa module, quản lý `/quit`, giải phóng sockets/threads.
- **Phân công:** C điều phối integration testing; A và B chịu trách nhiệm ghép phần mình. Không ai độc quyền `app.py`.
- **Nguồn:** DOCX §4.2, §5.1, §9; Python argparse/socket/threading.
- **Test:** T-CLI-01, T-ERR-05 và smoke test 2 máy.

## Interface contract: những điều phải ký duyệt trước khi tách branch (M0 nội bộ)

| Giao diện | Producer | Consumer | Nội dung phải thống nhất |
|---|---|---|---|
| `PeerSnapshot` (ý tưởng) | A registry | B chat, CLI | Peer identifier, IP, TCP port, status, timestamp, immutable snapshot |
| `AppMessage` (ý tưởng) | B protocol | A/B/C | Type, length, text/file metadata, parse errors |
| `ChatEvent` (ý tưởng) | B chat | A UI | Sender identity, text, active/unread state |
| `TransferProgress` (ý tưởng) | C file | A UI | Filename, bytes done/total, percent, status |
| `Connection` lifecycle | B connections | B chat/C file | Send/read ownership, close responsibility, threads, error callback |
| Shared cancellation | app | A/B/C | Stop event; shutdown order; timeout/blocked IO policy |

**Đây không phải API đã chốt.** Các class/function cụ thể chỉ viết vào docs sau buổi review. Mọi thay đổi phải qua PR có reviewer của các module phụ thuộc.

## Khi một module được xem là hoàn thành?

1. Requirement IDs liên quan có test case.
2. Owner đã chạy test với **expected và actual**; có log/ảnh/evidence.
3. Review xác nhận phù hợp DOCX và không phá contract.
4. `docs/protocol.md`/`docs/architecture.md`/`docs/devlog.md` được cập nhật nếu code thay đổi thiết kế.
5. Issue và PR đã được liên kết; sau merge và kiểm thử tích hợp mới đổi trạng thái thành `VERIFIED`.
