# Task A — Lập trình UDP Socket

Tài liệu hướng dẫn và lý thuyết về **Giao thức UDP (User Datagram Protocol)** trong môn học Mạng Máy Tính.

---

## 1. Mục tiêu Yêu cầu (Objectives)

- [x] Nghiên cứu cơ chế hoạt động của giao thức UDP và cấu trúc gói tin Datagram.
- [x] Xây dựng hai chương trình độc lập:
  - `udp_sender.py`: Đóng vai trò Bên gửi dữ liệu (Sender).
  - `udp_receiver.py`: Đóng vai trò Bên nhận dữ liệu (Receiver).
- [x] Truyền nhận thành công chuỗi dữ liệu định dạng **UTF-8** (hỗ trợ tiếng Việt có dấu).
- [x] Nắm vững các hàm socket căn bản: `bind()`, `sendto()`, `recvfrom()`.
- [x] Giải thích được luồng hoạt động và các khái niệm lý thuyết liên quan để phục vụ câu hỏi vấn đáp.

---

## 2. Kiến thức Cốt lõi (Theoretical Background)

### 2.1. UDP và Datagram là gì?
- **UDP (User Datagram Protocol):** Là giao thức truyền tải thuộc tầng Transport trong mô hình OSI / TCP-IP.
- **Datagram:** Là đơn vị dữ liệu độc lập được đóng gói trong UDP. Mỗi Datagram chứa đầy đủ thông tin địa chỉ nguồn, địa chỉ đích và nội dung dữ liệu (payload).

### 2.2. Các Hằng số và Hàm Socket trong Python
- **`AF_INET`:** Họ địa chỉ IPv4 (Address Family - INET).
- **`SOCK_DGRAM`:** Loại socket UDP (Datagram Socket), phân biệt với `SOCK_STREAM` của TCP.
- **`bind((ip, port))`:** Gán địa chỉ IP và Port cố định cho socket để tiến trình có thể lắng nghe gói tin tới.
- **`sendto(data, (ip, port))`:** Gửi mảng bytes `data` trực tiếp tới địa chỉ `(ip, port)` của bên nhận mà không cần kết nối trước.
- **`recvfrom(buffer_size)`:** Tạm dừng chương trình chờ nhận gói tin UDP. Trả về cặp dữ liệu `(data, addr)` với `data` là mảng bytes nhận được và `addr` là tuple `(ip, port)` của người gửi.

### 2.3. Địa chỉ IP và Port
- **IP (Internet Protocol):** Định danh vị trí của thiết bị trong mạng LAN hoặc Internet (ví dụ: `127.0.0.1` cho Loopback Local, `192.168.1.10` cho dải LAN).
- **Port:** Định danh tiến trình cụ thể đang chạy trên thiết bị (ví dụ: Port `9999` cho tiến trình nhận UDP).

### 2.4. So sánh Đặc tính UDP vs TCP

| Tiêu chí | UDP (User Datagram Protocol) | TCP (Transmission Control Protocol) |
| :--- | :--- | :--- |
| **Thủ tục kết nối** | **Không kết nối (Connectionless)** — Gửi tin ngay không cần bắt tay. | **Hướng kết nối (Connection-oriented)** — Bắt tay 3 bước trước khi truyền. |
| **Tính tin cậy** | **Unreliable** — Không đảm bảo gói tin tới đích, không báo nhận (ACK). | **Reliable** — Đảm bảo tin tới đích 100%, tự động gửi lại nếu mất gói. |
| **Thứ tự gói tin** | Có thể bị đảo trật tự gói khi tới đích. | Đảm bảo giữ nguyên thứ tự ban đầu. |
| **Tốc độ & Chi phí** | Cực nhanh, chi phí Header nhỏ (8 bytes). | Chậm hơn, Header lớn (20 bytes trở lên). |

### 2.5. UDP Broadcast là gì?
- **Định nghĩa:** Là cơ chế gửi một gói tin UDP đơn lẻ từ một máy gửi tới **tất cả các máy tính** trong cùng một phân đoạn mạng LAN (Subnet).
- **Địa chỉ Broadcast:** Địa chỉ đặc biệt đại diện cho toàn mạng, ví dụ `255.255.255.255` hoặc `127.255.255.255` (dải loopback offline).
- **Ứng dụng:** Được ứng dụng trong tính năng Khám phá Peer (Peer Discovery) tự động, giúp các thiết bị tìm thấy nhau trong mạng LAN mà không cần biết trước IP của đối phương.

---

## 3. Cấu trúc Thư mục Dự án

```text
Task_A_UDP/
├── udp_receiver.py    # Chương trình nhận dữ liệu UDP Datagram
├── udp_sender.py      # Chương trình gửi dữ liệu UDP Datagram
└── README.md          # Tài liệu hướng dẫn và lý thuyết
```

---

## 4. Hướng dẫn Chạy và Kiểm thử (Execution Guide)

### Bước 1: Khởi chạy Receiver (Cửa sổ Terminal 1)
Mở cửa sổ Terminal thứ nhất và chạy file receiver để mở socket lắng nghe cổng `9999`:

```bash
python udp_receiver.py
```

### Bước 2: Khởi chạy Sender (Cửa sổ Terminal 2)
Mở cửa sổ Terminal thứ hai để gửi dữ liệu UTF-8 sang Receiver:

```bash
python udp_sender.py
```

### Bước 3: Kiểm tra kết quả
- Nhập chuỗi văn bản tiếng Việt bất kỳ từ Terminal của `udp_sender.py` (ví dụ: `Xin chào! Kiểm thử UDP tiếng Việt thành công`).
- Quan sát Terminal của `udp_receiver.py` để đảm bảo chuỗi văn bản được nhận và hiển thị chính xác.