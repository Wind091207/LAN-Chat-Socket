import socket

# Cấu hình địa chỉ của Server
SERVER_HOST = "127.0.0.1"  # Chạy trên cùng máy local (Loopback)
SERVER_PORT = 5000  # Phải trùng với Port của Server


def run_client():
    # 1. Tạo TCP Socket
    cli = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        # 2. Thực hiện bắt tay 3 bước kết nối đến Server
        cli.connect((SERVER_HOST, SERVER_PORT))
        print(f"[*] Đã kết nối thành công tới Server {SERVER_HOST}:{SERVER_PORT}")
        print(
            "[*] Nhập tin nhắn và nhấn Enter để gửi. Nhập 'quit' hoặc 'exit' để thoát.\n"
        )

        while True:
            # Nhập tin nhắn từ bàn phím
            msg = input("Client > ")

            if not msg.strip():
                continue

            # Nếu nhập 'quit' hoặc 'exit' thì ngắt kết nối
            if msg.strip().lower() in ("quit", "exit"):
                break

            # 3. Mã hóa chuỗi text thành bytes và gửi sang Server
            cli.sendall(msg.encode("utf-8"))

            # 4. Chờ nhận dữ liệu echo phản hồi từ Server
            data = cli.recv(1024)

            if not data:
                print("[-] Server đã ngắt kết nối.")
                break

            # In dữ liệu echo nhận được ra màn hình
            echo_msg = data.decode("utf-8")
            print(f"Server Echo > {echo_msg}\n")

    except ConnectionRefusedError:
        print(
            "[!] Lỗi: Không thể kết nối tới Server. Hãy đảm bảo Server đã được bật trước!"
        )
    finally:
        # 5. Đóng socket ngắt kết nối
        cli.close()
        print("[*] Đã đóng kết nối.")


if __name__ == "__main__":
    run_client()
