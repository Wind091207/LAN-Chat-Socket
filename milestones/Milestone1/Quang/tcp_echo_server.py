import socket

# Cấu hình IP và Port
HOST = "0.0.0.0"  # Lắng nghe trên tất cả các card mạng
PORT = 5000  # Cổng TCP


def run_server():
    # 1. Tạo TCP Socket (AF_INET = IPv4, SOCK_STREAM = TCP)
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Cho phép giải phóng và sử dụng lại cổng ngay lập tức khi restart server
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # 2. Gán địa chỉ IP và Port cho socket
    srv.bind((HOST, PORT))

    # 3. Chuyển sang trạng thái lắng nghe kết nối (tối đa 5 client chờ trong hàng hàng đợi)
    srv.listen(5)
    print(f"[*] TCP Echo Server đang chạy và lắng nghe tại port {PORT}...")

    while True:
        # 4. Chấp nhận kết nối từ client (lệnh này sẽ chặn/chờ cho đến khi có client kết nối)
        conn, addr = srv.accept()
        print(f"[+] Client kết nối từ địa chỉ: {addr}")

        with conn:
            while True:
                # 5. Nhận dữ liệu từ client (tối đa 1024 bytes một lần)
                data = conn.recv(1024)

                # Nếu dữ liệu rỗng (b""), nghĩa là client đã ngắt kết nối
                if not data:
                    print(f"[-] Client {addr} đã ngắt kết nối.")
                    break

                # Giải mã bytes thành chuỗi text để in ra console
                msg = data.decode("utf-8")
                print(f"[Nhan tu {addr[1]}]: {msg}")

                # 6. Gửi ngược lại chính dữ liệu vừa nhận cho client (Echo)
                conn.sendall(data)


if __name__ == "__main__":
    run_server()
