"""Quản lý trạng thái cuộc trò chuyện, lịch sử tin nhắn và số tin chưa đọc."""

import threading
import time


class ChatState:
    """Lưu trữ dữ liệu hội thoại theo từng peer một cách an toàn đa luồng."""

    def __init__(self):
        self._lock = threading.RLock()
        self._current_partner = None
        self._histories = {}
        self._unread_counts = {}
        self._peer_names = {}

    def set_peer_name(self, peer_id: tuple, name: str):
        """Lưu ánh xạ tên hiển thị cho peer_id."""
        with self._lock:
            self._peer_names[peer_id] = name

    def get_peer_name(self, peer_id: tuple) -> str:
        """Lấy tên hiển thị của peer_id."""
        with self._lock:
            return self._peer_names.get(peer_id, f"{peer_id[0]}:{peer_id[1]}")

    def set_current_partner(self, peer_id: tuple | None):
        """Đặt đối tác đang chat hiện tại và xóa bộ đếm tin chưa đọc của đối tác đó."""
        with self._lock:
            self._current_partner = peer_id
            if peer_id is not None:
                self._unread_counts[peer_id] = 0

    def get_current_partner(self) -> tuple | None:
        """Trả về peer_id của đối tác đang chat hiện tại."""
        with self._lock:
            return self._current_partner

    def add_message(self, peer_id: tuple, message: dict | str):
        """Thêm tin nhắn vào lịch sử và tự tăng số tin chưa đọc nếu đang mở phòng khác."""
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
        """Trả về bản sao lịch sử tin nhắn với peer_id."""
        with self._lock:
            return list(self._histories.get(peer_id, []))

    def get_unread_messages(self, peer_id: tuple) -> list:
        """Lấy danh sách các tin nhắn chưa đọc gần nhất của peer_id."""
        with self._lock:
            count = self._unread_counts.get(peer_id, 0)
            if count <= 0:
                return []
            history = self._histories.get(peer_id, [])
            return list(history[-count:])

    def get_unread_count(self, peer_id: tuple) -> int:
        """Trả về số lượng tin nhắn chưa đọc của peer_id."""
        with self._lock:
            return self._unread_counts.get(peer_id, 0)

    def mark_as_read(self, peer_id: tuple):
        """Đặt lại số tin chưa đọc của peer_id về 0."""
        with self._lock:
            self._unread_counts[peer_id] = 0