import socket
import threading
import time

# module này sẽ tự tạo và gửi HELLO mỗi 3s
# python main.py --name Quan --tcp-port 5001 chạy
# sau khi chạy là module này đã tự động gửi HELLO mỗi 3s
# Khi nhập /list ở B, A vẫn gửi HELLO
# Khi set_status("away") thì trong thông điệp HELLO A tự chuyển online -> away chẳng hạn
# Khi gõ /quit A dừng gửi HELLO
class UDPDiscovery:
    def __init__(
        self,
        name: str,
        tcp_port: int,
        registry,
        bcast_addr: str = "255.255.255.255",
        port: int = 9999,
    ):
        self.name = name
        self.tcp_port = tcp_port
        self.registry = registry
        self.bcast_addr = bcast_addr
        self.port = port
        self.local_ip = None

        self.status = "online"
        self.running = False
        self.sock = None

        self._lock = threading.Lock()
        self._send_thread = None
        self._recv_thread = None

    def start(self):
        if self.running:
            return

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        if hasattr(socket, "SO_REUSEPORT"):
            try:
                self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            except OSError:
                pass

        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.sock.bind(("", self.port))
        self.sock.settimeout(1.0)

        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
            probe.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            probe.connect((self.bcast_addr, self.port))
            self.local_ip = probe.getsockname()[0]

        self.running = True

        self._send_thread = threading.Thread(target=self._send_loop, daemon=True)
        self._recv_thread = threading.Thread(target=self._recv_loop, daemon=True)

        self._send_thread.start()
        self._recv_thread.start()

    def set_status(self, new_status: str):
        with self._lock:
            self.status = new_status

    def stop(self):
        self.running = False

        if self._send_thread and self._send_thread.is_alive():
            self._send_thread.join(timeout=2.0)

        if self._recv_thread and self._recv_thread.is_alive():
            self._recv_thread.join(timeout=2.0)

        if self.sock:
            try:
                self.sock.close()
            except OSError:
                pass

    def _send_loop(self):
        while self.running:
            with self._lock:
                current_status = self.status # sau khi set_status xong thì được gán vô current_status

            msg = f"HELLO|{self.name}|{self.tcp_port}|{current_status}" # gửi HELLO
            data = msg.encode("utf-8")

            try:
                self.sock.sendto(data, (self.bcast_addr, self.port)) # Gửi đến: Địa chỉ broadcast/địa chỉ nhận
            except OSError:
                pass

            time.sleep(3) # chu kỳ 3s
    # => cơ chế quảng bá sự hiện diện / phát hiện thiết bị (Device Discovery / Heartbeat) trong mạng LAN sử dụng giao thức UDP.
    
    def _recv_loop(self): # trong cùng 1 LAN có 2 thg ví dụ ở đây là Minh sẽ nhận được câu trả lời từ Quan dựa trên hàm này
        while self.running:
            try:
                data, addr = self.sock.recvfrom(1024)
            except socket.timeout:
                continue
            except OSError:
                break

            msg = data.decode("utf-8", errors="replace")
            parts = msg.split("|") # nhận dữ liệu UDP từ Quan và tách thành ["HELLO", "Minh", "5002", "away"]

            if len(parts) == 4 and parts[0] == "HELLO":
                peer_name = parts[1]

                try:
                    peer_tcp_port = int(parts[2])
                except ValueError:
                    continue

                peer_status = parts[3]
                peer_ip = addr[0]

                if (peer_name == self.name
                    and peer_tcp_port == self.tcp_port
                    and peer_ip == self.local_ip):
                    continue

                if self.registry:
                    try:
                        self.registry.update_peer(
                            peer_name, peer_ip, peer_tcp_port, peer_status # NGAY LỆNH NÀY UPDATE PEER NHẬN ĐƯỢC TỪ QUAN
                        )
                    except (ValueError, TypeError):
                        continue
