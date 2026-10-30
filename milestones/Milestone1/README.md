
# Milestone 1 — TCP & UDP Socket

## 1. Mục tiêu

Theo `LAN_Chat_Socket_Project.docx`, Milestone 1 yêu cầu:

- **TCP Echo Client/Server:** Client gửi dữ liệu → Server nhận → Echo lại → Client nhận phản hồi.
- **UDP Send/Receive:** Sender gửi Datagram → Receiver nhận và hiển thị.

**Checkpoint:** Demo thành công cả hai chương trình.

## 2. Phân công

| Thành viên | Nhiệm vụ |
|---|---|
| A | UDP Sender/Receiver |
| B | TCP Echo Client/Server |
| C | Kiểm thử, review và tổng hợp README |

## 3. TCP Echo

**Giao thức:** TCP — `SOCK_STREAM`  
**Địa chỉ:** `127.0.0.1:65431`

### Luồng hoạt động

```text
TCP Server                         TCP Client
    |                                  |
 socket()                           socket()
    |                                  |
  bind()                                |
    |                                  |
 listen()                               |
    |                                  |
 accept() <------------------------ connect()
    |                                  |
  recv()  <------------------------ sendall()
    |                                  |
 sendall() ------------------------> recv()
    |                                  |
  close()                            close()
```

### Hướng dẫn chạy

Mở hai Terminal tại thư mục chứa code TCP.

```powershell
python .\TCP_Server.py
```

```powershell
python .\TCP_Client.py
```

### Kết quả kiểm thử

| Test case | Kết quả |
|---|---|
| Client kết nối Server trên localhost | PASS |
| Echo tin nhắn ngắn | PASS |
| Gửi và nhận tiếng Việt UTF-8 | PASS |
| Client nhập `quit` | PASS |
| Client đóng kết nối, Server tiếp tục nhận Client khác | PASS |
| Client kết nối khi Server chưa chạy | Phát hiện lỗi `ConnectionRefusedError` |
| Gửi 1238 bytes, Client chỉ nhận 1024 bytes trong một lần `recv()` | Giới hạn đã xác định |
| Dừng Server bằng `Ctrl+C` khi Socket đang blocking | Chưa xử lý hoàn chỉnh |

**Ghi chú:** TCP là byte stream, `recv(1024)` chỉ nhận tối đa 1024 bytes mỗi lần. Chương trình Echo cơ bản chưa xác định ranh giới thông điệp.

## 4. UDP Send/Receive

**Giao thức:** UDP — `SOCK_DGRAM`  
**Receiver:** `0.0.0.0:5000`  
**Sender gửi tới:** `127.0.0.1:5000`

### Luồng hoạt động

```text
UDP Sender                        UDP Receiver
    |                                  |
 socket()                           socket()
    |                                  |
    |                                bind()
    |                                  |
  input()                               |
    |                                  |
 encode()                               |
    |                                  |
 sendto() ------------------------> recvfrom()
                                       |
                                    decode()
                                       |
                                     print()
```

### Hướng dẫn chạy

Mở hai Terminal tại thư mục chứa code UDP.

```powershell
python .\UDP_receiver.py
```

```powershell
python .\UDP_sender.py
```

### Kết quả kiểm thử

| Test case | Kết quả |
|---|---|
| Sender gửi Datagram tới Receiver | PASS |
| Receiver hiển thị đúng nội dung | PASS |
| Truyền nhận tiếng Việt UTF-8 | PASS |
| Receiver hiển thị IP và Port nguồn | PASS |
| Sender nhập `quit` hoặc `exit` để thoát | PASS |
| Sender gửi khi Receiver chưa chạy | `sendto()` vẫn có thể thành công, không đảm bảo dữ liệu được nhận |
| Sender thoát nhưng Receiver vẫn lắng nghe | Đúng tính chất UDP |
| Dừng Receiver bằng `Ctrl+C` khi đang `recvfrom()` | Có thể phản hồi chậm trên Windows |

**Ghi chú:** UDP không thiết lập kết nối. Sender đóng Socket không làm Receiver tự động dừng.

## 5. Giới hạn và hướng phát triển

| Vấn đề | Milestone tiếp theo |
|---|---|
| Chưa có UDP Broadcast Discovery, Online List, Status | M2 |
| TCP chưa có Message Framing và xử lý thông điệp dài đầy đủ | M3 |
| Chưa có TCP Chat đồng thời và nhiều Peer | M3 |
| Chưa có Console UI và File Transfer | M4 |
| Chưa xử lý đầy đủ lỗi Socket, Peer Crash và Shutdown | M5 |

## 6. Tài liệu tham khảo

- `LAN_Chat_Socket_Project.docx` — yêu cầu chính thức.
- `Seminar_Socket Programming.pdf` — slide 8–12.
- `Gioithieu_Huongdan_DoAnSocket.pdf` — hướng dẫn đồ án.
- `01_client.py`, `01_server.py`, `02_client.py`, `02_server.py` — TCP.
- `udp_broadcast_demo.py` — UDP, dùng sâu hơn ở M2.

## 7. Kết luận

Đã triển khai và kiểm thử thành công hai chức năng cơ bản:

- TCP Echo Client/Server trên localhost.
- UDP Send/Receive trên localhost, hỗ trợ UTF-8.

Các giới hạn về Message Framing, giao tiếp đồng thời và xử lý lỗi nâng cao được ghi nhận để giải quyết trong các Milestone tiếp theo.

**Milestone 1:** Đạt checkpoint chức năng cơ bản; chờ hoàn tất review của nhóm trước khi chốt.
