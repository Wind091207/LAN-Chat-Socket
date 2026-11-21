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

    def _emit(self, event_type: str, **payload):
        """Đẩy sự kiện bất đồng bộ sang Queue để CLI hiển thị an toàn."""
        self.events.put({"type": event_type, **payload})

    @staticmethod
    def _configure_socket(sock: socket.socket):
        """Tối ưu độ trễ gói tin chat nhỏ."""
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

            # Nếu người dùng hiện tại chưa chọn ai để chat, tự động đặt người gọi làm đối tác
            if self.chat_state.get_current_partner() is None:
                self.chat_state.set_current_partner(peer_id)
                self._emit("TCP_CONNECTED", peer_id=peer_id, name=peer_name, incoming=True)
            else:
                self._emit("TCP_INCOMING_PEER", peer_id=peer_id, name=peer_name)

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
    def connect_peer(self, peer) -> tuple | None:
        """
        Mở hoặc tái sử dụng kết nối TCP tới peer.
        Trả về peer_id = (ip, tcp_port) nếu thành công, None nếu thất bại.
        """
        try:
            peer_id, peer_name = self._extract_peer(peer)
        except Exception as e:
            self._emit("TCP_ERROR", message=f"Invalid peer info: {e}")
            return None

        self.chat_state.set_peer_name(peer_id, peer_name)

        # Kiểm tra kết nối đã tồn tại -> tái sử dụng ngay
        with self._conn_lock:
            if peer_id in self._connections:
                self.chat_state.set_current_partner(peer_id)
                return peer_id

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._configure_socket(sock)
        sock.settimeout(5.0)

        try:
            sock.connect(peer_id)

            # Chặn tự kết nối với chính mình
            if (sock.getsockname()[0], self.tcp_port) == peer_id:
                sock.close()
                self._emit("TCP_ERROR", message="Cannot chat with yourself.")
                return None

            sock.sendall(encode_hi(self.name, self.tcp_port))
            reply = recv_frame(sock)
            sock.settimeout(None)

            if not reply or reply[0] != "HI":
                sock.close()
                self._emit("TCP_ERROR", message=f"Invalid handshake from {peer_name}")
                return None

            if not self._register_connection(peer_id, sock, outgoing=True):
                sock.close()
                # Nếu kết nối incoming vừa thắng tie-break thì vẫn tái sử dụng kết nối đó
                with self._conn_lock:
                    if peer_id not in self._connections:
                        return None
                self.chat_state.set_current_partner(peer_id)
                return peer_id

            self.chat_state.set_current_partner(peer_id)
            threading.Thread(
                target=self._receive_loop,
                args=(peer_id, sock),
                name=f"TCP-Recv-{peer_name}",
                daemon=True,
            ).start()
            return peer_id

        except Exception as e:
            try:
                sock.close()
            except OSError:
                pass
            self._emit("TCP_ERROR", message=f"Could not connect to {peer_name}: {e}")
            return None

    def send_message(self, peer_id: tuple | None, text: str) -> bool:
        """Gửi tin nhắn UTF-8 tới peer_id (mặc định dùng current_partner nếu peer_id=None)."""
        if peer_id is None:
            peer_id = self.chat_state.get_current_partner()
        if peer_id is None:
            self._emit("TCP_ERROR", message="No active chat partner. Use /chat <name|number> first.")
            return False

        with self._conn_lock:
            conn = self._connections.get(peer_id)
            if not conn:
                self._emit("TCP_ERROR", message="Connection to peer is closed.")
                return False
            sock = conn["sock"]
            send_lock = conn["send_lock"]

        try:
            frame = encode_msg(text)
            with send_lock:
                sock.sendall(frame)

            self.chat_state.add_message(
                peer_id,
                {
                    "sender": self.name,
                    "text": text,
                    "is_me": True,
                    "timestamp": time.time(),
                },
            )
            return True
        except OSError as e:
            self._emit("TCP_ERROR", message=f"Failed to send message: {e}")
            self._cleanup_connection(peer_id, sock)
            return False

    def leave_chat(self, peer_id: tuple | None = None) -> bool:
        """Gửi BYE\n, đóng kết nối chat với peer_id và đưa current_partner về None."""
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
                    # Đối phương đóng terminal / crash (EOF)
                    self._emit(
                        "TCP_DISCONNECTED",
                        peer_id=peer_id,
                        name=peer_name,
                        reason="connection closed",
                    )
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
                    if self.chat_state.get_current_partner() == peer_id:
                        self._emit("TCP_MESSAGE", peer_id=peer_id, name=peer_name, text=text)
                    else:
                        unread = self.chat_state.get_unread_count(peer_id)
                        self._emit("TCP_UNREAD", peer_id=peer_id, name=peer_name, count=unread)

                elif frame_type == "BYE":
                    self._emit("TCP_PEER_LEFT", peer_id=peer_id, name=peer_name)
                    break

                elif frame_type == "HI":
                    # Cập nhật lại tên nếu nhận gói HI bổ sung
                    self.chat_state.set_peer_name(peer_id, frame[1])
                    peer_name = frame[1]

        except (ConnectionError, OSError):
            with self._conn_lock:
                is_active = self._connections.get(peer_id, {}).get("sock") is sock
            if self._running and is_active:
                self._emit(
                    "TCP_DISCONNECTED",
                    peer_id=peer_id,
                    name=peer_name,
                    reason="connection lost",
                )
        except ValueError as e:
            self._emit("TCP_ERROR", message=f"Protocol error from {peer_name}: {e}")
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