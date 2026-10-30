# Milestone 1 — TCP & UDP Socket

## 1. Mục tiêu

Theo `LAN_Chat_Socket_Project.docx`, Milestone 1 yêu cầu:

- **TCP Echo Client/Server:** Client gửi dữ liệu → Server nhận → gửi trả dữ liệu → Client hiển thị.
- **UDP Send/Receive:** Sender gửi Datagram → Receiver nhận và hiển thị dữ liệu.

**Checkpoint:** Demo được cả hai chương trình.

## 2. Phân công

| Thành viên | Công việc |
|---|---|
| A | UDP Sender/Receiver |
| B | TCP Echo Client/Server |
| C | Kiểm thử và tổng hợp kết quả |

## 3. TCP Echo

TCP là giao thức hướng kết nối, cung cấp luồng byte tin cậy và có thứ tự.

**Luồng hoạt động:**

`Server: socket() → bind() → listen() → accept() → recv() → sendall()`

`Client: socket() → connect() → sendall() → recv()`

**Cấu hình:** `127.0.0.1:65431` (TCP).

**Cách chạy:** Mở hai Terminal tại thư mục chứa code.

Terminal 1:

`python TCP_Server.py`

Terminal 2:

`python TCP_Client.py`

Nhập tin nhắn ở Client và quan sát dữ liệu Echo. Nhập `quit` để kết thúc kết nối phía Client.

Xem `TCP.md` để đọc phần lý thuyết chi tiết.

## 4. UDP Send/Receive

UDP là giao thức không kết nối, truyền dữ liệu dưới dạng Datagram và không đảm bảo giao hàng.

**Luồng hoạt động:**

`Sender: socket() → encode() → sendto()`

`Receiver: socket() → bind() → recvfrom() → decode()`

**Cấu hình:** Receiver lắng nghe UDP port `5000`; Sender gửi tới `127.0.0.1:5000`.

**Cách chạy:**

Terminal 1:

`python UDP_receiver.py`

Terminal 2:

`python UDP_sender.py`

Nhập nội dung tiếng Việt để kiểm tra UTF-8. Nhập `quit` hoặc `exit` ở Sender để thoát.

## 5. Kiểm thử

| Trường hợp | Kết quả mong đợi |
|---|---|
| TCP Connection | Client kết nối Server |
| TCP Echo | Client nhận lại đúng dữ liệu |
| TCP Disconnect | Server xử lý được việc Client đóng kết nối |
| UDP Datagram | Receiver nhận đúng dữ liệu |
| UDP UTF-8 | Hiển thị chính xác tiếng Việt |
| UDP Source Address | Hiển thị IP và port của Sender |

**Tình trạng:** Đã kiểm thử nhanh việc gửi/nhận TCP và UDP trên localhost. Còn lỗi TCP Server khi Client ngắt kết nối không gửi `quit`; cần sửa và kiểm thử lại trước khi xác nhận hoàn thành.

## 6. Tài liệu tham khảo

- `LAN_Chat_Socket_Project.docx` — yêu cầu chính thức.
- `Seminar_Socket Programming.pdf` — slide 8–12.
- `01_server.py`, `01_client.py`, `02_server.py`, `02_client.py` — demo TCP.
- `udp_broadcast_demo.py` — tham khảo UDP.
- `TCP.md` — ghi chú lý thuyết TCP của nhóm.

## 7. Kết luận

Milestone 1 tập trung vào nền tảng TCP và UDP Socket. Sau khi sửa lỗi, chạy lại các bài kiểm thử và được review, nhóm sẽ hoàn thành checkpoint trước khi chuyển sang UDP Discovery ở Milestone 2.
