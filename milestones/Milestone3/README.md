# Milestone 3 — P2P TCP Chat, Message Framing & Quản lý đa kết nối

## 1. Mục tiêu

Xây dựng tầng giao tiếp **TCP Peer-to-Peer (P2P)** tích hợp vào hệ thống LAN Chat từ Milestone 2, cho phép các peer thiết lập kết nối trực tiếp, trao đổi tin nhắn văn bản tiếng Việt (UTF-8) ổn định theo giao thức đóng khung tự định nghĩa (Message Framing), hỗ trợ trò chuyện đồng thời với nhiều peer và xử lý an toàn các tình huống ngắt kết nối hoặc dữ liệu lỗi.

---

## 2. Kiến trúc hệ thống & Cấu trúc mã nguồn (`src/`)

Hệ thống vận hành theo mô hình đa luồng trên một tiến trình duy nhất (`main.py`):

| Tệp tin | Vai trò | Chức năng chính |
|---|---|---|
| `main.py` | Điểm khởi chạy | Khởi tạo `Queue`, `PeerRegistry`, `ChatState`, `UDPDiscovery`, `TCPTransport` và gọi `run_cli` |
| `protocol.py` | Đóng khung bản tin | Mã hóa/giải mã các frame `HI`, `MSG`, `BYE`; đọc đúng số byte theo header để chống dính gói và phân mảnh TCP |
| `tcp_transport.py` | Giao vận TCP P2P | Mở TCP Server (`Acceptor`), chủ động kết nối (`connect_peer`), tạo luồng nhận riêng cho từng peer, phá vỡ xung đột kết nối đồng thời |
| `chat_state.py` | Trạng thái hội thoại | Lưu lịch sử tin nhắn, tên peer, đối tác đang mở và bộ đếm `unread` an toàn đa luồng bằng `threading.RLock` |
| `cli.py` | Giao diện dòng lệnh | Xử lý `/chat`, `/leave`, `/list`, hiển thị màu sắc, mốc giờ `[HH:MM]`, giữ kết nối ngầm khi chuyển phòng và vẽ lại dấu nhắc khi có tin đến |
| `udp_discovery.py` | Khám phá peer (M2) | Phát và lắng nghe gói `HELLO` qua UDP broadcast cổng `9999` |
| `peer_registry.py` | Danh bạ peer (M2) | Quản lý danh sách peer online/away và theo dõi timeout 10 giây |

---

## 3. Thiết kế giao thức ứng dụng (TCP Framing)

### 3.1. Định dạng khung bản tin

Vì TCP truyền dữ liệu dưới dạng **dòng byte liên tục (byte stream)** không có ranh giới gói tin tự nhiên, nhóm thiết kế 3 loại khung bản tin kết thúc hoặc xác định độ dài tường minh:

- **Bắt tay định danh:**
  ```text
  HI|<name>|<tcp_port>\n
  ```
- **Gửi tin nhắn văn bản UTF-8:**
  ```text
  MSG|<byte_length>\n<UTF-8 payload>
  ```
  Trong đó `<byte_length>` là **số byte sau khi mã hóa UTF-8** (`len(text.encode("utf-8"))`), đảm bảo xử lý chính xác các ký tự tiếng Việt có dấu (2–3 byte/ký tự).
- **Kết thúc phiên chat:**
  ```text
  BYE\n
  ```

### 3.2. Cơ chế đọc 2 pha (`recv_frame`)

1. **Pha 1 (`_recv_line`):** Đọc từng byte cho tới khi gặp ký tự `\n` để tách header (giới hạn `MAX_HEADER_LEN = 1024` byte nhằm chặn kết nối rác gửi chuỗi dài không có ký tự xuống dòng). Không dùng `makefile().readline()` để tránh đọc lố sang phần payload phía sau.
2. **Pha 2 (`_recv_exact`):** Lấy giá trị `<byte_length>` từ header `MSG`, lặp gọi `sock.recv()` cho tới khi gom đủ chính xác `<byte_length>` byte rồi mới giải mã UTF-8. Cơ chế này giải quyết triệt để cả **dính gói (sticky packets)** lẫn **phân mảnh gói tin (TCP fragmentation)**.

### 3.3. Xử lý xung đột khi hai peer `/chat` đồng thời

Mỗi peer được định danh duy nhất bằng khóa `peer_id = (ip, tcp_port)`. Nếu hai peer A và B cùng gọi `/chat` tới nhau tại một thời điểm, sau khi trao đổi gói `HI`, cả hai áp dụng quy tắc đối xứng: **bên có tuple `(ip, tcp_port)` nhỏ hơn giữ lại kết nối chủ động (`outgoing`), bên còn lại đóng socket thừa**. Nhờ đó mỗi cặp peer luôn duy trì tối đa **1 kết nối TCP**.

---

## 4. Các vấn đề thực tế đã gặp & Cách khắc phục

| Vấn đề gặp phải | Nguyên nhân kỹ thuật | Giải pháp đã áp dụng |
|---|---|---|
| Sai lệch độ dài khung tin tiếng Việt | Tiếng Việt có dấu chiếm 2–3 byte/ký tự trong UTF-8 (ví dụ `"Hi bờ rồ Minh"` dài 13 ký tự nhưng chiếm **17 byte** — hiển thị `MSG\|17` trên Wireshark). Dùng `len(text)` gây thiếu byte cuối. | Tính `<byte_length>` theo `len(text.encode("utf-8"))` và dùng vòng lặp `_recv_exact` gom đủ chính xác số byte. |
| Đóng ngang kết nối cũ khi chuyển phòng `/chat` | Bản `cli.py` ban đầu tự gọi `leave_chat` với đối tác cũ mỗi khi người dùng `/chat` sang người mới, làm mất kết nối nền và không nhận được thông báo `unread`. | Giữ nguyên các socket TCP đang mở khi chuyển phòng trên CLI, chỉ gửi `BYE` khi người dùng chủ động gõ `/leave` hoặc `/quit`. |
| Lỗi `timed out` khi Ubuntu kết nối sang Windows | Windows Defender Firewall mặc định chặn kết nối TCP Inbound trên card mạng VirtualBox Host-Only (`Public` profile). | Thêm rule Firewall cho phép luồng Inbound trên cổng TCP `5000-5010` và UDP `9999`. |
| Chồng lấn dòng nhập liệu khi có thông báo bất đồng bộ | Các luồng nền in thông báo `is online` / tin nhắn đến làm mất dấu nhắc nhập liệu trên console. | Dùng mã điều khiển ANSI (`\r\033[2K`) xóa dòng hiện tại, in sự kiện mới và tự động vẽ lại dấu nhắc `You -> <Tên>>`. |

---

## 5. Hạn chế kỹ thuật hiện tại & Hướng mở rộng

1. **Chưa mã hóa đường truyền & xác thực (Plaintext):** Dữ liệu trao đổi qua TCP ở dạng văn bản rõ (có thể đọc trực tiếp qua tính năng *Follow TCP Stream* của Wireshark) và chưa có cơ chế xác thực danh tính peer. *Hướng mở rộng:* Bọc socket bằng `ssl.SSLContext` (TLS) và thêm bước xác thực token/chữ ký.
2. **Phụ thuộc phạm vi mạng LAN & Tường lửa:** Cơ chế UDP Broadcast chỉ hoạt động trong cùng một subnet và dễ bị chặn bởi tính năng *Client Isolation* trên Wi-Fi công cộng hoặc Firewall của hệ điều hành. *Hướng mở rộng:* Bổ sung cơ chế nhập trực tiếp IP:Port thủ công hoặc máy chủ Rendezvous/Relay khi khác mạng con.
3. **Lưu trữ tạm thời trên RAM (In-memory):** Lịch sử trò chuyện và bộ đếm `unread` chỉ tồn tại trong bộ nhớ trong suốt phiên chạy; khi người dùng thoát chương trình (`/quit`) toàn bộ lịch sử phiên cũ sẽ mất. *Hướng mở rộng:* Lưu lịch sử tin nhắn cục bộ ra tệp JSON hoặc SQLite theo từng `peer_id`.
4. **Độ trễ phát hiện `offline` ở tầng UDP & Giới hạn giao diện Console:** Khi một peer tắt ngang không qua `/quit`, tầng TCP phát hiện ngắt kết nối ngay lập tức, nhưng trạng thái `offline` trên `/list` phụ thuộc chu kỳ timeout 10 giây của gói UDP `HELLO`. Ngoài ra, giao diện CLI dựa vào mã ANSI nên hạn chế về mặt trực quan khi mở nhiều hội thoại. *Hướng mở rộng:* Xây dựng giao diện đồ họa (Tkinter / PyQt / Web UI).
5. **Chưa tích hợp truyền tập tin (File Transfer):** Giao thức ở Milestone 3 mới hỗ trợ tin nhắn văn bản UTF-8 (`MSG`); tính năng chia nhỏ tệp tin (chunking) và kiểm tra toàn vẹn (checksum) sẽ được hoàn thiện ở **Milestone 4**.

---

## 6. Minh chứng kiểm thử

Toàn bộ kết quả kiểm thử chi tiết và ảnh chụp màn hình (chat tiếng Việt dài, đa peer 3 người + `unread`, xử lý crash & gói rác `nc`, bắt tay 3 bước TCP và `Follow TCP Stream` trên Wireshark) được lưu trong thư mục `milestones/Milestone3/` kèm tài liệu `HUONG_DAN_CHAY_M3.md`.
