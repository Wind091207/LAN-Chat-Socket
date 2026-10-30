### Socket là gì ?

=> Là cánh cửa trung gian giữa phần mềm bạn viết ở application layer và hệ điều hành
=> Giúp ứng dụng đẩy dữ liệu ra mạng internet mà không cần tự xử lý các thao tác định tuyến hay truyền tải vật lý phức tạp bên dưới.
=> TCP và UDP đều là giao thức cốt lỗi của tầng transport
=> Xem socket là một thùng thư ta viết chương trình nhét dữ liệu vào đây và khi chạy chương trình thì lúc này HĐH sẽ lấy dữ liệu và bọc thông tin địa chỉ xử lí việc còn lại và theo chiều ngược lại OS sẽ bóc tách cái vỏ bọc thông tin ra xong nhét vô socket => Lúc này ta có thể viết socket để lấy dữ liệu từ OS nhét vào.

### TCP là gì ?

=> TCP (Transmission Control Protocol) là giao thức hướng kết nối, truyền dữ liệu dưới dạng một dòng byte liên tục (byte stream) và đảm bảo độ tin cậy tuyệt đối.

### Yêu cầu 

=> tính chất của mạng "Echo" đòi hỏi sự phản hồi (như tiếng vang), tức là **Client gửi -> Server nhận rồi ném ngược lại y hệt -> Client hứng lấy và in ra**.

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

### Kiểm thử TCP Echo Client/Server

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

