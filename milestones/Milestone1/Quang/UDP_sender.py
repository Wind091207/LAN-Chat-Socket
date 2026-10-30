import socket

# Cấu hình địa chỉ đích (Receiver)
TARGET_HOST = "127.0.0.1"  # Gửi tới máy local (Loopback)
TARGET_PORT = 5000  # Phải trùng với Port của Receiver


def run_sender():
    # 1. Tạo UDP Socket (AF_INET = IPv4, SOCK_DGRAM = UDP)
    # Không cần gọi bind(), hệ điều hành sẽ tự cấp một port ngẫu nhiên cho Sender
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    print(f"[*] UDP Sender đã sẵn sàng gửi tới {TARGET_HOST}:{TARGET_PORT}")
    print(
        "[*] Nhập tin nhắn (hỗ trợ tiếng Việt UTF-8). Nhập 'quit' hoặc 'exit' để thoát.\n"
    )

    try:
        while True:
            # Nhập tin nhắn từ bàn phím
            msg = input("Sender > ")

            if not msg.strip():
                continue

            if msg.strip().lower() in ("quit", "exit"):
                break

            # 2. Mã hóa chuỗi UTF-8 thành bytes
            data = msg.encode("utf-8")

            # 3. Gửi UDP Datagram trực tiếp đến Receiver (chứa sẵn địa chỉ đích)
            sock.sendto(data, (TARGET_HOST, TARGET_PORT))
            print(f"-> Đã gửi {len(data)} bytes")

    finally:
        # 4. Đóng socket
        sock.close()
        print("[*] Đã đóng UDP Sender.")


if __name__ == "__main__":
    run_sender()
