import threading
import time


class ChatState:
    """Quản lý đối tác hiện tại, lịch sử chat và bộ đếm tin chưa đọc (thread-safe)."""

    def __init__(self):
        self._lock = threading.RLock()
        self._current_partner = None      # peer_id = (ip, tcp_port) hoặc None
        self._histories = {}              # {peer_id: [dict_message, ...]}
        self._unread_counts = {}          # {peer_id: int}
        self._peer_names = {}             # {peer_id: str}

    def set_peer_name(self, peer_id: tuple, name: str):
        with self._lock:
            self._peer_names[peer_id] = name

    def get_peer_name(self, peer_id: tuple) -> str:
        with self._lock:
            return self._peer_names.get(peer_id, f"{peer_id[0]}:{peer_id[1]}")

    def set_current_partner(self, peer_id: tuple | None):
        """Đặt peer đang chat hiện tại. Tự động reset unread của peer đó về 0."""
        with self._lock:
            self._current_partner = peer_id
            if peer_id is not None:
                self._unread_counts[peer_id] = 0

    def get_current_partner(self) -> tuple | None:
        with self._lock:
            return self._current_partner

    def add_message(self, peer_id: tuple, message: dict | str):
        """
        Lưu tin nhắn vào lịch sử của peer_id.
        Hỗ trợ truyền vào dict chuẩn hoặc chuỗi str.
        Nếu là tin nhắn đến từ peer khác current_partner -> tự tăng unread.
        """
        if isinstance(message, str):
            msg_record = {
                "sender": self.get_peer_name(peer_id),
                "text": message,
                "is_me": False,
                "timestamp": time.time(),
            }
        else:
            msg_record = dict(message)
            msg_record.setdefault("timestamp", time.time())

        with self._lock:
            self._histories.setdefault(peer_id, []).append(msg_record)
            is_incoming = not msg_record.get("is_me", False)
            if is_incoming and self._current_partner != peer_id:
                self._unread_counts[peer_id] = self._unread_counts.get(peer_id, 0) + 1

    def get_history(self, peer_id: tuple) -> list:
        """Trả về bản sao toàn bộ lịch sử chat với peer_id."""
        with self._lock:
            return list(self._histories.get(peer_id, []))

    def get_unread_messages(self, peer_id: tuple) -> list:
        """Lấy danh sách các tin chưa đọc gần nhất của peer_id (dùng khi chuyển sang /chat peer đó)."""
        with self._lock:
            count = self._unread_counts.get(peer_id, 0)
            if count <= 0:
                return []
            history = self._histories.get(peer_id, [])
            return list(history[-count:])

    def get_unread_count(self, peer_id: tuple) -> int:
        with self._lock:
            return self._unread_counts.get(peer_id, 0)

    def mark_as_read(self, peer_id: tuple):
        with self._lock:
            self._unread_counts[peer_id] = 0