
# Milestone 3 — TCP Chat

## 1. Mục tiêu

Xây dựng chức năng Chat P2P bằng TCP, kế thừa toàn bộ Milestone 2.

- `/chat <name|number>`: Chọn peer để chat.
- Nhập văn bản thông thường để gửi tin nhắn.
- `/leave`: Kết thúc cuộc chat hiện tại.
- Gửi và nhận tin nhắn hai chiều liên tục.
- Nhận tin nhắn từ nhiều peer, quản lý tin chưa đọc.
- Sử dụng Message Framing để xử lý TCP Byte Stream.

**Checkpoint:** Hai máy chat TCP hai chiều thành công.

## 2. Phân công nhiệm vụ

### Thành viên A — `cli.py`

Phụ trách giao diện Console:

- Giữ nguyên các lệnh M2: `/list`, `/status`, `/help`, `/quit`.
- Bổ sung `/chat <name|number>` và `/leave`.
- Xử lý văn bản thông thường thành tin nhắn.
- Gọi API TCP của B để kết nối, gửi tin và rời chat.
- Hiển thị tin nhắn và thông báo từ Queue.
- Cập nhật hướng dẫn `/help`.
- Kiểm thử các lệnh CLI.

Lưu ý:
- A không tự tạo TCP Socket trong CLI.
- CLI chỉ điều khiển TCP thông qua API do B cung cấp.
- Console Redraw hoàn chỉnh triển khai ở M4.

### Thành viên B — `tcp_transport.py`, `protocol.py`, `chat_state.py`

Phụ trách TCP Chat và giao thức.

**`tcp_transport.py`:**
- Tạo TCP Server bằng `socket()`, `bind()`, `listen()`.
- TCP Acceptor Thread chạy `accept()`.
- Tạo TCP Receiver Thread cho mỗi peer.
- Kết nối chủ động bằng `connect()`.
- Gửi và nhận dữ liệu bằng `sendall()`, `recv()`.
- Quản lý kết nối, đóng socket, xử lý mất kết nối.

API dự kiến:
- `start()` — khởi động TCP Server.
- `connect_peer(peer)` — kết nối peer.
- `send_message(peer_id, text)` — gửi tin nhắn.
- `leave_chat(peer_id)` — rời chat.
- `stop()` — dừng TCP.

**`protocol.py`:**
- Đóng gói thông điệp HI, MSG, BYE.
- Đọc header và payload theo đúng độ dài.
- Xử lý TCP nhận thiếu hoặc nhiều frame liên tiếp.

API dự kiến:
- `encode_hi(name, tcp_port)`
- `encode_msg(text)`
- `encode_bye()`
- `recv_frame(sock)`

**`chat_state.py`:**
- Lưu đối tác đang chat (`current_partner`).
- Lưu lịch sử tin nhắn theo peer.
- Quản lý số lượng tin chưa đọc (`unread`).
- Sử dụng Lock bảo vệ dữ liệu chung.

B tiếp tục quản lý việc tích hợp TCP vào `main.py`.

### Thành viên C — `tests/`

Phụ trách kiểm thử và hỗ trợ xử lý lỗi:

- Test TCP connect/disconnect.
- Test gửi/nhận tin nhắn hai chiều.
- Test TCP Message Framing.
- Test tin nhắn UTF-8, tin dài, nhiều frame.
- Test nhiều peer và unread.
- Ghi kết quả PASS/FAIL, báo lỗi cho A/B.

C chưa triển khai File Transfer ở M3.

## 3. Quy ước kỹ thuật thống nhất

### Định danh peer

- Peer được định danh bằng `(ip, tcp_port)`.
- Nickname có thể trùng nhau.
- TCP port sử dụng giá trị `--tcp-port` đã quảng bá ở M2.
- Mỗi peer vừa là TCP Client vừa là TCP Server.

### TCP Protocol

Header kết thúc bằng ký tự xuống dòng `\n`.

- `HI|<name>|<tcp_port>\n` — nhận diện peer.
- `MSG|<length>\n<UTF-8 bytes>` — tin nhắn.
- `BYE\n` — kết thúc chat.

Quy tắc:
- `length` tính bằng BYTE, không phải số ký tự.
- Bên nhận phải đọc đủ header và payload.
- Không giả định một lần `recv()` nhận trọn thông điệp.
- Giới hạn độ dài header và kích thước tin nhắn để tránh dữ liệu bất thường.

### Quản lý TCP Connection

- Mỗi cặp peer ưu tiên một kết nối chat đang hoạt động.
- Kết nối còn hoạt động được tái sử dụng.
- Nếu hai phía đồng thời tạo kết nối trùng, dùng thứ tự `(ip, port)` để quyết định giữ kết nối do phía có định danh nhỏ hơn khởi tạo.
- `/leave` gửi BYE và đóng kết nối chat hiện tại.
- `/quit` dừng cả TCP và UDP.
- Một lỗi kết nối không được làm crash toàn bộ chương trình.

### Thread, Queue và Lock

- Main Thread: Nhận lệnh CLI.
- TCP Acceptor Thread: Nhận kết nối mới.
- TCP Receiver Thread: Nhận tin từ mỗi peer.
- Các Thread M2 tiếp tục hoạt động.

Sử dụng:
- Queue để chuyển sự kiện TCP sang CLI.
- Lock cho Connection Manager, Chat State và Unread.
- Lock riêng cho thao tác gửi frame trên cùng socket nếu có nhiều Thread gửi.

### Chat nhiều peer

- Tin từ đối tác hiện tại được hiển thị ngay.
- Tin từ peer khác được lưu vào lịch sử.
- Tăng unread khi nhận tin từ peer không phải đối tác hiện tại.
- Khi chuyển sang peer đó, hiển thị tin chưa đọc và đặt unread về 0.

## 4. Kiểm thử

- [ ] TCP Server khởi động và lắng nghe đúng port.
- [ ] Hai máy kết nối TCP thành công.
- [ ] Chat hai chiều liên tục.
- [ ] Gửi tiếng Việt UTF-8 chính xác.
- [ ] Tin dài, frame chia nhỏ hoặc dính nhau được xử lý đúng.
- [ ] `/leave` và kết nối lại.
- [ ] Ba peer, quản lý tin chưa đọc.
- [ ] Hai bên đồng thời `/chat` không tạo kết nối trùng.

## 5. Ảnh và báo cáo

- [ ] Ảnh hai Terminal chat hai chiều.
- [ ] Ảnh ba peer và unread.
- [ ] Wireshark: SYN, SYN-ACK, ACK.
- [ ] Ảnh TCP Stream và thông điệp ứng dụng.
- [ ] Sơ đồ TCP Acceptor / Receiver Threads.
- [ ] Bảng kiểm thử và lỗi đã xử lý.

**Phải giải thích trong báo cáo:**
- Tại sao TCP cần Message Framing.
- Sự khác nhau giữa TCP và UDP trong dự án.
- Cách kết nối và nhận tin từ nhiều peer.
- Cách hoạt động của Thread, Queue và Lock.

**Không thực hiện trong M3:** File Transfer và Console Redraw hoàn chỉnh.
