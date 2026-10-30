# Milestone 1 — TCP & UDP Fundamentals

Dự án Lập trình Socket: **LAN Chat & File Sharing Application**  
Môn học: **Mạng Máy Tính**

---

## 1. Tổng quan Milestone 1

Milestone 1 tập trung vào việc xây dựng và nắm vững các thao tác socket cơ bản bằng ngôn ngữ Python, phục vụ cho hai giao thức truyền tải cốt lõi: **TCP** và **UDP**.

### Mục tiêu Checkpoint:
*   [x] Xây dựng và chạy thành công **TCP Echo Client/Server**.
*   [x] Xây dựng và chạy thành công **UDP Send/Receive / Broadcast Demo**.
*   [x] Hoàn thiện tài liệu giải thích cơ chế và luồng hoạt động của từng giao thức.

---

## 2. Giải thích chi tiết về UDP và TCP

### 2.1. Giao thức UDP (User Datagram Protocol)

#### **Tính chất & Đặc điểm**
*   **Không kết nối (Connectionless):** Không đòi hỏi thiết lập hay duy trì kết nối giữa hai tiến trình trước khi truyền dữ liệu.
*   **Không đảm bảo tính tin cậy (Unreliable):** Không có cơ chế xác nhận (ACK), không tự động gửi lại gói tin bị mất và không đảm bảo thứ tự nhận dữ liệu.
*   **Truyền dạng Datagram:** Dữ liệu được đóng thành từng gói độc lập, giữ nguyên ranh giới thông điệp giữa bên gửi và bên nhận.
*   **Hỗ trợ Broadcast / Multicast:** Cho phép gửi một gói tin đến toàn bộ các máy trong cùng phân đoạn mạng LAN.

#### **Vai trò trong đồ án**
UDP được sử dụng cho tính năng **Khám phá Peer (Peer Discovery)** và **Cập nhật trạng thái (Online/Away)**. 
*   Mỗi máy định kỳ broadcast gói tin `HELLO` (mỗi 3 giây) trên cổng UDP cố định (ví dụ: `9999`).
*   Việc mất một vài gói UDP không ảnh hưởng tới toàn bộ hệ thống vì gói mới sẽ liên tục được gửi lại sau 3 giây.

#### **Luồng hoạt động của UDP Socket**

```text
[ Server / Listener ]                       [ Client / Sender ]
        │                                            │
    socket()                                     socket()
        │                                            │
     bind()                                       bind()* (Optional)
        │                                            │
 recvfrom() <─────── (Datagram Packet) ────────── sendto()
        │                                            │
 sendto()   ────────── (Reply Data) ────────────> recvfrom()
        │                                            │
     close()                                      close()
```

---

### 2.2. Giao thức TCP (Transmission Control Protocol)

#### **Tính chất & Đặc điểm**
*   **Hướng kết nối (Connection-oriented):** Bắt buộc phải thực hiện bắt tay 3 bước (3-way handshake) giữa Client và Server trước khi truyền dữ liệu.
*   **Đảm bảo tin cậy tuyệt đối (Reliable):** Có cơ chế xác nhận (ACK), tự động truyền lại gói bị lỗi/mất và sắp xếp dữ liệu đúng thứ tự ban đầu.
*   **Dòng Byte liên tục (Byte Stream):** Dữ liệu truyền đi không có ranh giới tin nhắn tự nhiên. Lập trình viên phải tự đóng khung thông điệp (**Message Framing**) bằng Header (độ dài/loại dữ liệu) để bên nhận tách tin chính xác.

#### **Vai trò trong đồ án**
TCP được sử dụng cho tính năng **Chat tin nhắn trực tiếp** và **Truyền nhận File**.
*   Mỗi cuộc trò chuyện hoặc mỗi lần gửi file sẽ mở một kênh kết nối TCP unicast giữa hai peer.
*   Đảm bảo không bị mất mát hoặc sai lệch nội dung tin nhắn và dữ liệu file.

#### **Luồng hoạt động của TCP Socket**

```text
[ TCP Server ]                               [ TCP Client ]
      │                                            │
  socket()                                     socket()
      │                                            │
   bind()                                          │
      │                                            │
  listen()                                         │
      │                                            │
  accept()  <──── (SYN / 3-Way Handshake) ────  connect()
      │                                            │
   recv()   <───────── (Byte Stream) ──────────  sendall()
      │                                            │
  sendall() ────────── (Byte Stream) ──────────>   recv()
      │                                            │
   close()  <────── (FIN / Connection Close) ──   close()
```

---

## 3. Cấu trúc thư mục Milestone 1

```text
milestone1/
├── tcp_echo_server.py    # Chương trình Server TCP Echo
├── tcp_echo_client.py    # Chương trình Client TCP Echo
├── udp_broadcast_demo.py # Chương trình UDP Send/Receive Broadcast
└── README.md             # Tài liệu giải thích và hướng dẫn sử dụng
```

---

## 4. Hướng dẫn chạy và kiểm thử (Testing Guide)

### Yêu cầu môi trường
*   Python 3.8 trở lên.

---

### 4.1. Kiểm thử TCP Echo Client/Server

Mở 2 cửa sổ Terminal độc lập:

**Terminal 1 (Chạy Server):**
```bash
python tcp_echo_server.py
```
*Server sẽ mở socket, bind vào cổng 5000 và chờ kết nối.*

**Terminal 2 (Chạy Client):**
```bash
python tcp_echo_client.py
```
*Nhập văn bản từ Terminal Client. Server sẽ nhận và echo (phản hồi) lại chính xác nội dung đó.*

---

### 4.2. Kiểm thử UDP Broadcast Demo

Mở 3 cửa sổ Terminal để mô phỏng 3 tiến trình P2P trong cùng một máy:

**Terminal 1 (Listener B):**
```bash
python udp_broadcast_demo.py listen --name B
```

**Terminal 2 (Listener C):**
```bash
python udp_broadcast_demo.py listen --name C
```

**Terminal 3 (Sender A):**
```bash
python udp_broadcast_demo.py send --name A
```

**Kết quả mong đợi:**  
Tiến trình A sẽ phát tín hiệu broadcast `HELLO|A|5001|online` mỗi 3 giây. Cả B và C sẽ lập tức nhận và hiển thị thông điệp từ A lên màn hình.

---

## 5. Tóm tắt so sánh TCP vs UDP

| Tiêu chí | TCP (SOCK_STREAM) | UDP (SOCK_DGRAM) |
| :--- | :--- | :--- |
| **Mô hình** | Hướng kết nối (Connection-oriented) | Không kết nối (Connectionless) |
| **Độ tin cậy** | Đảm bảo 100%, đúng thứ tự | Không đảm bảo, có thể mất gói |
| **Đơn vị dữ liệu** | Dòng byte liên tục (Byte stream) | Các gói tin độc lập (Datagrams) |
| **Truyền tin** | Unicast (1-to-1) | Unicast, Broadcast (1-to-N) |
| **Ứng dụng trong dự án** | Chat tin nhắn & Truyền File | Khám phá Peer & Cập nhật Status |