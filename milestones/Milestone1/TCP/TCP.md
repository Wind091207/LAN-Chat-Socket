### Socket là gì ?

=> Là cánh cửa trung gian giữa phần mềm bạn viết ở application layer và hệ điều hành
=> Giúp ứng dụng đẩy dữ liệu ra mạng internet mà không cần tự xử lý các thao tác định tuyến hay truyền tải vật lý phức tạp bên dưới.
=> TCP và UDP đều là giao thức cốt lỗi của tầng transport
=> Xem socket là một thùng thư ta viết chương trình nhét dữ liệu vào đây và khi chạy chương trình thì lúc này HĐH sẽ lấy dữ liệu và bọc thông tin địa chỉ xử lí việc còn lại và theo chiều ngược lại OS sẽ bóc tách cái vỏ bọc thông tin ra xong nhét vô socket => Lúc này ta có thể viết socket để lấy dữ liệu từ OS nhét vào.

### TCP là gì ?

=> TCP (Transmission Control Protocol) là giao thức hướng kết nối, truyền dữ liệu dưới dạng một dòng byte liên tục (byte stream) và đảm bảo độ tin cậy tuyệt đối.

### Yêu cầu 

=> tính chất của mạng "Echo" đòi hỏi sự phản hồi (như tiếng vang), tức là **Client gửi -> Server nhận rồi ném ngược lại y hệt -> Client hứng lấy và in ra**.

### Luồng hoạt động của UDP Socket

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
