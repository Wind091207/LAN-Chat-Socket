
# Milestone 3 — TCP Chat

## 1. Mục tiêu

Xây dựng chức năng chat P2P bằng TCP, kế thừa UDP Discovery và Peer Registry từ Milestone 2.

- `/chat <name|number>`: Chọn peer để chat.
- Nhập văn bản thông thường để gửi tin nhắn.
- `/leave`: Kết thúc cuộc chat hiện tại.
- Gửi và nhận tin nhắn hai chiều.
- Hỗ trợ nhiều peer, lịch sử chat và số tin chưa đọc.
- Sử dụng Message Framing để xử lý TCP Byte Stream.

**Checkpoint:** Hai máy chat TCP hai chiều thành công.

## 2. Phân công nhiệm vụ

### A — CLI & Chat Interface

**File:** `src/cli.py`

- Bổ sung `/chat <name|number>` và `/leave`.
- Xử lý văn bản không bắt đầu bằng `/` thành tin nhắn.
- Hiển thị tin nhắn và thông báo tin chưa đọc.
- Giữ nguyên `/list`, `/status`, `/help`, `/quit` của M2.
- Gọi API TCP do B cung cấp.
- Cập nhật `/help` và kiểm thử các lệnh CLI.

### B — TCP Networking, Protocol & Integration

**File:** `src/tcp_transport.py`, `src/protocol.py`, `src/chat_state.py`, `src/main.py`

- Tạo TCP Server bằng `socket()`, `bind()`, `listen()`.
- Tạo Acceptor Thread và Receiver Thread cho từng kết nối.
- Kết nối peer bằng `connect()`.
- Gửi/nhận bằng `sendall()` và `recv()`.
- Xây dựng giao thức HI / MSG / BYE.
- Xử lý Message Framing và đọc đủ byte.
- Quản lý kết nối, lịch sử chat, đối tác hiện tại, unread.
- Dùng Lock bảo vệ dữ liệu dùng chung.
- Tích hợp TCP Chat vào `main.py`.
- Kiểm thử tích hợp cùng A.

### C — Chuẩn bị Milestone 4

- Chưa giao module phát triển mới trong M3.
- Nghiên cứu File Transfer bằng TCP.
- Tìm hiểu chunking, file nhị phân, progress và checksum.
- Đọc giao thức và API của B để chuẩn bị tích hợp ở M4.

## 3. Quy ước thống nhất

### Định danh peer

- `peer_id = (ip, tcp_port)`.
- Không dùng nickname làm định danh duy nhất.
- TCP port lấy từ thông tin HELLO ở M2.
- Mỗi peer vừa là TCP Client vừa là TCP Server.

### Giao thức TCP

Sử dụng header kết thúc bằng `\n`:

- `HI|<name>|<tcp_port>\n`
- `MSG|<length>\n<UTF-8 bytes>`
- `BYE\n`

Trong đó:

- `HI`: Nhận diện peer.
- `MSG`: Gửi tin nhắn.
- `BYE`: Kết thúc chat.
- `length` tính theo byte UTF-8, không phải số ký tự.

Bên nhận phải đọc đủ header và payload, không giả định một lần `recv()` nhận đủ thông điệp.

### Quản lý kết nối

- Mỗi cặp peer ưu tiên một kết nối chat.
- Kết nối đang hoạt động được tái sử dụng.
- Khi hai peer đồng thời kết nối, dùng thứ tự `(ip, tcp_port)` để quyết định giữ một kết nối.
- `/leave` gửi BYE và đóng kết nối chat hiện tại.
- `/quit` dừng TCP và UDP.
- Tin từ peer khác được lưu vào lịch sử và tăng unread.
- Khi chuyển sang peer đó, hiển thị tin chưa đọc và đặt unread về 0.

### Thread, Queue và Lock

- Main Thread: Nhận lệnh người dùng.
- TCP Acceptor Thread: Chờ kết nối mới.
- TCP Receiver Thread: Nhận dữ liệu từ từng kết nối.
- Queue: Chuyển sự kiện TCP sang CLI.
- Lock: Bảo vệ kết nối, lịch sử chat, unread và thao tác gửi chung socket.

## 4. API cần thống nhất

**B cung cấp cho A:**

- `start()`
- `connect_peer(peer)`
- `send_message(peer_id, text)`
- `leave_chat(peer_id)`
- `stop()`

**Protocol:**

- `encode_hi(name, tcp_port)`
- `encode_msg(text)`
- `encode_bye()`
- `recv_frame(sock)`

**Chat State:**

- `set_current_partner(peer_id)`
- `add_message(peer_id, message)`
- `get_history(peer_id)`
- `get_unread_count(peer_id)`
- `mark_as_read(peer_id)`

Tên hàm là quy ước thiết kế. Nếu thay đổi phải cập nhật thống nhất giữa các module.

## 5. Kiểm thử

- [ ] Hai máy kết nối TCP thành công.
- [ ] Chat hai chiều liên tục.
- [ ] `/chat`, `/leave` hoạt động.
- [ ] Gửi tiếng Việt UTF-8 chính xác.
- [ ] Tin dài và frame bị chia nhỏ vẫn đọc đủ.
- [ ] Nhiều tin liên tiếp không bị dính.
- [ ] Ba peer, lịch sử và unread hoạt động.
- [ ] Hai bên đồng thời `/chat` không tạo kết nối trùng.
- [ ] Đóng kết nối và kết nối lại thành công.

## 6. Minh chứng và báo cáo

- [ ] Ảnh hai Terminal chat hai chiều.
- [ ] Ảnh chat nhiều peer và unread.
- [ ] Wireshark TCP SYN / SYN-ACK / ACK.
- [ ] Ảnh TCP Stream và nội dung tin nhắn.
- [ ] Sơ đồ TCP Acceptor / Receiver Threads.
- [ ] Bảng kiểm thử PASS/FAIL.

**Nội dung cần giải thích:**

- Vì sao sử dụng TCP cho Chat.
- Vì sao TCP cần Message Framing.
- Cách quản lý nhiều kết nối.
- Thread, Queue, Lock và Chat State.
- Các lỗi thực tế và cách khắc phục.

**Không triển khai trong M3:** File Transfer và Console Redraw hoàn chỉnh.
