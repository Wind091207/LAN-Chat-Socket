import queue
import socket
import threading
import time

from chat_state import ChatState
from protocol import encode_bye, encode_hi, encode_msg, recv_frame


class TCPTransport:
    """Tầng giao vận P2P TCP: Server lắng nghe, Client kết nối và quản lý đa luồng."""

    def __init__(
        self,
        name: str,
        tcp_port: int,
        chat_state: ChatState = None,
        events: queue.Queue = None,
    ):
        self.name = name
        self.tcp_port = int(tcp_port)
        self.chat_state = chat_state if chat_state is not None else ChatState()
        self.events = events if events is not None else queue.Queue()

        self._server_sock = None
        self._running = False
        self._conn_lock = threading.RLock()

        # peer_id -> {"sock": socket, "send_lock": threading.Lock(), "outgoing": bool}
        self._connections = {}

    def _emit(self, event_type: str, data: dict):
        """Đẩy tuple (event_type, data) sang Queue theo đúng format của cli.py."""
        self.events.put((event_type, data))

    @staticmethod
    def _configure_socket(sock: socket.socket):
        """Tắt Nagle để gửi tin nhắn chat ngay lập tức."""
        try:
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        except OSError:
            pass

    @staticmethod
    def _extract_peer(peer) -> tuple[tuple[str, int], str]:
        """Chuẩn hóa thông tin peer (hỗ trợ dict, object hoặc tuple)."""
        if isinstance(peer, dict):
            ip = peer["ip"]
            port = int(peer["tcp_port"])
            peer_name = peer.get("name", f"{ip}:{port}")
        elif isinstance(peer, tuple) and len(peer) == 2:
            ip, port = peer[0], int(peer[1])
            peer_name = f"{ip}:{port}"
        else:
            ip = getattr(peer, "ip")
            port = int(getattr(peer, "tcp_port"))
            peer_name = getattr(peer, "name", f"{ip}:{port}")
        return (ip, port), peer_name

    # ------------------------------------------------------------------
    # 1. Khởi động & Dừng TCP Server
    # ------------------------------------------------------------------
    def start(self):
        """Mở socket TCP Server và chạy Acceptor Thread."""
        if self._running:
            return
        self._running = True
        self._server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server_sock.bind(("0.0.0.0", self.tcp_port))
        self._server_sock.listen(16)

        threading.Thread(
            target=self._accept_loop,
            name="TCP-Acceptor",
            daemon=True,
        ).start()

    def stop(self):
        """Gửi BYE tới tất cả kết nối đang mở và đóng toàn bộ socket TCP."""
        self._running = False
        if self._server_sock:
            try:
                self._server_sock.close()
            except OSError:
                pass
            self._server_sock = None

        with self._conn_lock:
            conns = list(self._connections.items())
            self._connections.clear()

        for _, info in conns:
            sock = info["sock"]
            try:
                with info["send_lock"]:
                    sock.sendall(encode_bye())
            except OSError:
                pass
            try:
                sock.close()
            except OSError:
                pass

        self.chat_state.set_current_partner(None)

    # ------------------------------------------------------------------
    # 2. Chấp nhận kết nối đến (Acceptor & Handshake)
    # ------------------------------------------------------------------
    def _accept_loop(self):
        while self._running:
            try:
                client_sock, addr = self._server_sock.accept()
                self._configure_socket(client_sock)
                threading.Thread(
                    target=self._handle_incoming,
                    args=(client_sock, addr),
                    daemon=True,
                ).start()
            except OSError:
                break

    def _handle_incoming(self, sock: socket.socket, addr: tuple):
        remote_ip = addr[0]
        try:
            sock.settimeout(5.0)
            first_frame = recv_frame(sock)
            sock.settimeout(None)

            if not first_frame or first_frame[0] != "HI":
                sock.close()
                return

            _, peer_name, peer_tcp_port = first_frame
            peer_id = (remote_ip, peer_tcp_port)
            self.chat_state.set_peer_name(peer_id, peer_name)

            # Phản hồi HI để xác nhận định danh hai chiều
            sock.sendall(encode_hi(self.name, self.tcp_port))

            if not self._register_connection(peer_id, sock, outgoing=False):
                sock.close()
                return

            # Giữ nguyên current_partner của CLI để khi có tin nhắn đến,
            # CLI tự đếm unread và nhắc người dùng gõ /chat <name>
            self._receive_loop(peer_id, sock)

        except Exception:
            try:
                sock.close()
            except OSError:
                pass

    def _register_connection(self, peer_id: tuple, new_sock: socket.socket, outgoing: bool) -> bool:
        """
        Đảm bảo mỗi cặp peer chỉ giữ 1 kết nối TCP duy nhất.
        Nếu hai bên connect() đồng thời, dùng thứ tự tuple (ip, tcp_port) để quyết định:
        bên có (ip, tcp_port) nhỏ hơn giữ kết nối outgoing (chủ động mở).
        """
        with self._conn_lock:
            existing = self._connections.get(peer_id)
            if existing is None:
                self._connections[peer_id] = {
                    "sock": new_sock,
                    "send_lock": threading.Lock(),
                    "outgoing": outgoing,
                }
                return True

            local_ip = new_sock.getsockname()[0]
            my_id = (local_ip, self.tcp_port)
            keep_outgoing = (my_id < peer_id)

            if outgoing == keep_outgoing:
                old_sock = existing["sock"]
                self._connections[peer_id] = {
                    "sock": new_sock,
                    "send_lock": threading.Lock(),
                    "outgoing": outgoing,
                }
                try:
                    old_sock.close()
                except OSError:
                    pass
                return True

            return False

    # ------------------------------------------------------------------
    # 3. Chủ động kết nối, Gửi tin nhắn & Rời cuộc chat (API cho CLI)
    # ------------------------------------------------------------------
    def connect_peer(self, peer) -> tuple:
        """
        Mở hoặc tái sử dụng kết nối TCP tới peer.
        Ném Exception nếu kết nối thất bại để cli.py bắt lỗi và thông báo.
        """
        peer_id, peer_name = self._extract_peer(peer)
        self.chat_state.set_peer_name(peer_id, peer_name)

        # Tái sử dụng nếu kết nối tới peer này đã mở sẵn
        with self._conn_lock:
            if peer_id in self._connections:
                return peer_id

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._configure_socket(sock)
        sock.settimeout(5.0)

        try:
            sock.connect(peer_id)

            if (sock.getsockname()[0], self.tcp_port) == peer_id:
                raise ValueError("Cannot chat with yourself.")

            sock.sendall(encode_hi(self.name, self.tcp_port))
            reply = recv_frame(sock)
            sock.settimeout(None)

            if not reply or reply[0] != "HI":
                raise ConnectionError(f"Invalid handshake from {peer_name}")

            if not self._register_connection(peer_id, sock, outgoing=True):
                sock.close()
                with self._conn_lock:
                    if peer_id not in self._connections:
                        raise ConnectionError(f"Connection to {peer_name} was closed")
                return peer_id

            threading.Thread(
                target=self._receive_loop,
                args=(peer_id, sock),
                name=f"TCP-Recv-{peer_name}",
                daemon=True,
            ).start()
            return peer_id

        except Exception:
            try:
                sock.close()
            except OSError:
                pass
            raise

    def send_message(self, peer_id: tuple | None, text: str) -> bool:
        """
        Gửi tin nhắn UTF-8 tới peer_id.
        Ném ConnectionError/OSError nếu gửi thất bại để cli.py bắt lỗi.
        """
        if peer_id is None:
            peer_id = self.chat_state.get_current_partner()
        if peer_id is None:
            raise ConnectionError("No active chat partner.")

        with self._conn_lock:
            conn = self._connections.get(peer_id)
            if not conn:
                raise ConnectionError("Connection to peer is closed.")
            sock = conn["sock"]
            send_lock = conn["send_lock"]

        try:
            frame = encode_msg(text)
            with send_lock:
                sock.sendall(frame)
            return True
        except OSError:
            self._cleanup_connection(peer_id, sock)
            raise

    def leave_chat(self, peer_id: tuple | None = None) -> bool:
        """Gửi BYE\n và đóng kết nối chat với peer_id."""
        if peer_id is None:
            peer_id = self.chat_state.get_current_partner()
        if peer_id is None:
            return False

        with self._conn_lock:
            conn = self._connections.pop(peer_id, None)

        if self.chat_state.get_current_partner() == peer_id:
            self.chat_state.set_current_partner(None)

        if conn:
            sock = conn["sock"]
            try:
                with conn["send_lock"]:
                    sock.sendall(encode_bye())
            except OSError:
                pass
            try:
                sock.close()
            except OSError:
                pass
            return True
        return False

    # ------------------------------------------------------------------
    # 4. Vòng lặp nhận dữ liệu cho từng peer (Receiver Thread)
    # ------------------------------------------------------------------
    def _receive_loop(self, peer_id: tuple, sock: socket.socket):
        peer_name = self.chat_state.get_peer_name(peer_id)
        try:
            while self._running:
                frame = recv_frame(sock)
                if frame is None:
                    self._emit("disconnected", {"peer_id": peer_id, "name": peer_name})
                    break

                frame_type = frame[0]
                if frame_type == "MSG":
                    text = frame[1]
                    self.chat_state.add_message(
                        peer_id,
                        {
                            "sender": peer_name,
                            "text": text,
                            "is_me": False,
                            "timestamp": time.time(),
                        },
                    )
                    self._emit(
                        "message",
                        {"peer_id": peer_id, "name": peer_name, "text": text},
                    )

                elif frame_type == "BYE":
                    self._emit("peer_left", {"peer_id": peer_id, "name": peer_name})
                    break

                elif frame_type == "HI":
                    self.chat_state.set_peer_name(peer_id, frame[1])
                    peer_name = frame[1]

        except (ConnectionError, OSError):
            with self._conn_lock:
                is_active = self._connections.get(peer_id, {}).get("sock") is sock
            if self._running and is_active:
                self._emit("disconnected", {"peer_id": peer_id, "name": peer_name})
        except ValueError:
            pass
        finally:
            self._cleanup_connection(peer_id, sock)

    def _cleanup_connection(self, peer_id: tuple, sock: socket.socket):
        removed = False
        with self._conn_lock:
            conn = self._connections.get(peer_id)
            if conn and conn["sock"] is sock:
                del self._connections[peer_id]
                removed = True

        if removed and self.chat_state.get_current_partner() == peer_id:
            self.chat_state.set_current_partner(None)

        try:
            sock.close()
        except OSError:
            pass