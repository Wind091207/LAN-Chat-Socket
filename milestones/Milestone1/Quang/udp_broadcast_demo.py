import argparse
import socket
import time

PORT = 9999  # Port UDP cố định dùng cho việc broadcast khám phá peer


def make_socket():
    # 1. Tạo UDP Socket (AF_INET = IPv4, SOCK_DGRAM = UDP)
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # 2. Cho phép nhiều tiến trình trên cùng 1 máy bind chung 1 port UDP
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # Nếu chạy trên macOS/BSD thì bật thêm cờ SO_REUSEPORT (Windows sẽ tự bỏ qua)
    if hasattr(socket, "SO_REUSEPORT"):
        try:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        except OSError:
            pass

    # 3. Bật quyền phát sóng Broadcast cho socket
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    # 4. Gán socket vào tất cả card mạng ("") tại port 9999
    s.bind(("", PORT))
    return s


def listen(name):
    s = make_socket()
    print(f"[{name}] Đang lắng nghe gói tin UDP Broadcast tại port {PORT}...")
    while True:
        # 5. Nhận gói tin UDP (chờ cho đến khi có gói tin gửi tới)
        data, addr = s.recvfrom(1024)
        msg = data.decode("utf-8", errors="replace")

        # Tách chuỗi theo ký tự '|' để kiểm tra định dạng gói tin HELLO
        parts = msg.split("|")

        # Bỏ qua nếu gói tin HELLO do chính mình phát ra
        if len(parts) == 4 and parts[0] == "HELLO" and parts[1] == name:
            continue

        print(f"[{name}] Nhận được: {msg!r} từ địa chỉ {addr[0]}:{addr[1]}")


def send(name, bcast, tcp_port):
    s = make_socket()

    # Định dạng gói tin hiện diện: HELLO|<name>|<tcp_port>|<status>
    msg = f"HELLO|{name}|{tcp_port}|online".encode("utf-8")

    print(
        f"[{name}] Đang phát sóng Broadcast tới {bcast}:{PORT} mỗi 3 giây (Nhấn Ctrl+C để dừng)..."
    )
    while True:
        # 6. Gửi gói tin broadcast tới địa chỉ IP phát sóng
        s.sendto(msg, (bcast, PORT))
        print(f"[{name}] Đã phát: {msg.decode('utf-8')}")
        time.sleep(3)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="UDP Broadcast Demo")
    p.add_argument("role", choices=["listen", "send"], help="Chế độ: listen hoặc send")
    p.add_argument("--name", required=True, help="Tên hiển thị của peer")
    p.add_argument(
        "--bcast",
        default="255.255.255.255",
        help="Địa chỉ broadcast (dùng 127.255.255.255 nếu test offline)",
    )
    p.add_argument("--tcp-port", type=int, default=5001, help="Port TCP của peer này")
    a = p.parse_args()

    try:
        if a.role == "listen":
            listen(a.name)
        else:
            send(a.name, a.bcast, a.tcp_port)
    except KeyboardInterrupt:
        print("\n[*] Đã thoát chương trình.")
