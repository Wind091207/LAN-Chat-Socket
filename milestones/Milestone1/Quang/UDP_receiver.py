import socket

# Cấu hình IP và Port lắng nghe
HOST = "0.0.0.0"  # Lắng nghe trên tất cả các card mạng
PORT = 5000  # Port UDP cố định để Sender gửi dữ liệu tới


def run_receiver():
    # 1. Tạo UDP Socket (AF_INET = IPv4, SOCK_DGRAM = UDP)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Cho phép giải phóng và tái sử dụng Port nhanh chóng khi khởi động lại
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # 2. Gán địa chỉ IP và Port cho socket
    sock.bind((HOST, PORT))
    print(f"[*] UDP Receiver đang chạy và lắng nghe tại port {PORT}...")
    print("[*] Nhấn Ctrl+C để dừng chương trình.\n")

    try:
        while True:
            # 3. Nhận dữ liệu (Chờ gói tin UDP gửi đến)
            # recvfrom trả về một tuple: (dữ liệu dạng bytes, (IP_nguồn, Port_nguồn))
            data, addr = sock.recvfrom(1024)

            # 4. Giải mã mảng bytes nhận được thành chuỗi UTF-8
            msg = data.decode("utf-8", errors="replace")

            print(f"[Nhận từ {addr[0]}:{addr[1]}]: {msg}")

    except KeyboardInterrupt:
        print("\n[*] Đã dừng UDP Receiver.")
    finally:
        # 5. Đóng socket giải phóng tài nguyên
        sock.close()


if __name__ == "__main__":
    run_receiver()
