
from __future__ import annotations

import ipaddress
import math
import time
from queue import Queue
from threading import Event, Lock, Thread
from typing import Callable, Optional, TypedDict

# Mô tả 5 trường của 1 peer
class Peer(TypedDict):
    name: str
    ip: str
    tcp_port: int
    status: str
    last_seen: float


class PeerRegistry: # Class quản lý danh sách peer bằng dict + Lock + Queue
    def __init__( # Tạo Registry rỗng, đặt timeout 10 giây, Queue và Lock
        self,
        events: Optional[Queue] = None, 
        *, 
        timeout_seconds: float = 10.0, 
        check_interval: float = 1.0, 
        clock: Optional[Callable[[], float]] = None, 
    ) -> None:
        self._timeout = self._positive_number(timeout_seconds, "timeout_seconds") # Kiểm tra tham số thời gian phải là số dương
        self._check_interval = self._positive_number(check_interval, "check_interval") # Kiểm tra tham số thời gian phải là số dương
        if events is None:
            events = Queue()
        if type(events) is not Queue:
            raise TypeError("events must be a FIFO queue.Queue")
        if events.maxsize > 0:
            raise ValueError("Use Queue() with maxsize=0; bounded queues can lose events")
        if clock is not None and not callable(clock):
            raise TypeError("clock must be callable")

        self.events = events # Hàng đợi các sự kiện vừa xảy ra để thông báo cho B, Queue lưu sự kiện dạng tuple có 2 phần tử: ("online", peer_dict)
        self._clock = time.monotonic if clock is None else clock
        self._peers: dict[tuple[str, int], Peer] = {} # Danh sách các peer đang được phát hiện
        self._lock = Lock() 
        self._monitor_lock = Lock()
        self._stop_event = Event()
        self._monitor_thread: Optional[Thread] = None

    @staticmethod
    def _positive_number(value: float, label: str) -> float: # Kiểm tra tham số thời gian phải là số dương
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError(f"{label} must be a number")
        if not math.isfinite(value) or value <= 0:
            raise ValueError(f"{label} must be finite and greater than zero")
        return float(value)

    @staticmethod
    def _validate_peer(name: str, ip: str, tcp_port: int, status: str) -> str: # Kiểm tra name, IPv4, TCP port, status hợp lệ
        if not isinstance(name, str):
            raise TypeError("name must be a string")
        if not name.strip() or "|" in name or any(ord(c) < 32 or ord(c) == 127 for c in name):
            raise ValueError("name must be nonempty and contain no pipe or control characters")
        if not isinstance(ip, str):
            raise TypeError("ip must be a string")
        try:
            normalized_ip = str(ipaddress.IPv4Address(ip))
        except ipaddress.AddressValueError as exc:
            raise ValueError("ip must be a valid IPv4 address") from exc
        if isinstance(tcp_port, bool) or not isinstance(tcp_port, int):
            raise TypeError("tcp_port must be an integer")
        if not 1 <= tcp_port <= 65535:
            raise ValueError("tcp_port must be between 1 and 65535")
        if not isinstance(status, str):
            raise TypeError("status must be a string")
        if status not in ("online", "away"):
            raise ValueError("status must be 'online' or 'away'")
        return normalized_ip
    
    # Thêm/cập nhật peer, làm mới last_seen; phát sự kiện khi mới hoặc đổi status
    def update_peer(self, name: str, ip: str, tcp_port: int, status: str) -> Peer: 
        ip = self._validate_peer(name, ip, tcp_port, status)
        key = (ip, tcp_port)
        with self._lock:
            previous = self._peers.get(key)
            peer: Peer = {
                "name": name,
                "ip": ip,
                "tcp_port": tcp_port,
                "status": status,
                "last_seen": float(self._clock()),
            }
            self._peers[key] = peer
            if previous is None:
                self.events.put_nowait(("online", peer.copy())) # Thêm event vào cuối queue
            elif previous["status"] != status:
                self.events.put_nowait(("status_changed", peer.copy())) # Thêm event vào cuối queue
            return peer.copy()

    def get_peers(self) -> list[Peer]: # Trả về danh sách bản sao các peer cho B hiển thị /list
        with self._lock:
            return [peer.copy() for peer in self._peers.values()]

    def remove_expired_peers(self) -> list[Peer]: # Xóa peer quá 10 giây và phát sự kiện offline
        with self._lock:
            now = float(self._clock())
            expired_keys = [
                key for key, peer in self._peers.items()
                if now - peer["last_seen"] > self._timeout
            ]
            removed = []
            for key in expired_keys:
                peer = self._peers.pop(key)
                self.events.put_nowait(("offline", peer.copy()))
                removed.append(peer.copy())
            return removed

    def start_timeout_monitor(self) -> None: # Khởi chạy thread quét timeout định kỳ
        with self._monitor_lock:
            if self._monitor_thread is not None and self._monitor_thread.is_alive():
                return
            self._stop_event.clear()
            thread = Thread(
                target=self._monitor_loop,
                name=f"PeerRegistryTimeout-{id(self)}",
                daemon=True,
            )
            self._monitor_thread = thread
            thread.start()

    def stop_timeout_monitor(self) -> None: # Yêu cầu thread timeout dừng và chờ nó kết thúc
        with self._monitor_lock:
            self._stop_event.set()
            if self._monitor_thread is not None:
                self._monitor_thread.join()
                self._monitor_thread = None

    def _monitor_loop(self) -> None: # Mỗi ~1 giây gọi remove_expired_peers()
        while not self._stop_event.wait(self._check_interval):
            self.remove_expired_peers()

# Queue lưu các sự kiện về trạng thái peer, không phải lưu danh sách peer