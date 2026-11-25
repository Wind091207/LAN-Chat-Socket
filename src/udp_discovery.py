"""Khám phá và quảng bá sự hiện diện của các peer qua UDP Broadcast."""

import socket
import threading
import time


class UDPDiscovery:
    """Quản lý luồng gửi và nhận bản tin HELLO định kỳ qua UDP."""

    def __init__(
        self,
        name: str,
        tcp_port: int,
        registry,
        bcast_addr: str = "255.255.255.255",
        port: int = 9999,
    ):
        """Khởi tạo các tham số cấu hình và luồng cho UDP Discovery."""
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
        """Mở socket UDP Broadcast và khởi chạy hai luồng gửi/nhận HELLO."""
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

    def _send_hello(self):
        """Đóng gói và phát ngay một bản tin HELLO qua UDP Broadcast."""
        if not self.sock:
            return
        with self._lock:
            current_status = self.status

        msg = f"HELLO|{self.name}|{self.tcp_port}|{current_status}"
        try:
            self.sock.sendto(msg.encode("utf-8"), (self.bcast_addr, self.port))
        except OSError:
            pass

    def set_status(self, new_status: str):
        """Cập nhật trạng thái hiển thị (online/away) và phát gói HELLO ngay lập tức."""
        with self._lock:
            self.status = new_status
        if self.running:
            self._send_hello()

    def stop(self):
        """Dừng các luồng UDP Discovery và đóng socket."""
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
        """Phát gói tin HELLO qua UDP Broadcast định kỳ mỗi 3 giây."""
        while self.running:
            self._send_hello()
            time.sleep(3)

    def _recv_loop(self):
        """Lắng nghe gói HELLO từ mạng LAN và cập nhật vào PeerRegistry."""
        while self.running:
            try:
                data, addr = self.sock.recvfrom(1024)
            except socket.timeout:
                continue
            except OSError:
                break

            msg = data.decode("utf-8", errors="replace")
            parts = msg.split("|")

            if len(parts) == 4 and parts[0] == "HELLO":
                peer_name = parts[1]

                try:
                    peer_tcp_port = int(parts[2])
                except ValueError:
                    continue

                peer_status = parts[3]
                peer_ip = addr[0]

                if (
                    peer_name == self.name
                    and peer_tcp_port == self.tcp_port
                    and peer_ip == self.local_ip
                ):
                    continue

                if self.registry:
                    try:
                        self.registry.update_peer(
                            peer_name, peer_ip, peer_tcp_port, peer_status
                        )
                    except (ValueError, TypeError):
                        continue