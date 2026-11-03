"""Quan ly peer cho Milestone 2.
A goi update_peer() sau khi kiem tra HELLO. B doc get_peers() va Queue.
Peer het han khi monotonic_now - last_seen > timeout_seconds.
"""

from __future__ import annotations

import ipaddress
import math
import time
from queue import Queue
from threading import Event, Lock, Thread
from typing import Callable, Optional, TypedDict


class Peer(TypedDict):
    name: str
    ip: str
    tcp_port: int
    status: str
    last_seen: float


class PeerRegistry:
    """Danh sach peer an toan khi nhieu thread cung truy cap.

    events: queue.Queue() FIFO khong gioi han (maxsize=0).
    timeout_seconds: mac dinh 10 giay.
    check_interval: chu ky quet, mac dinh 1 giay.
    clock: chi can truyen khi test; mac dinh la time.monotonic.

    Su kien: ("online" | "offline" | "status_changed", peer_dict).
    Moi peer tra ra ngoai deu la ban sao, khong lo du lieu noi bo.
    """

    def __init__(
        self,
        events: Optional[Queue] = None,
        *,
        timeout_seconds: float = 10.0,
        check_interval: float = 1.0,
        clock: Optional[Callable[[], float]] = None,
    ) -> None:
        self._timeout = self._positive_number(timeout_seconds, "timeout_seconds")
        self._check_interval = self._positive_number(check_interval, "check_interval")
        if events is None:
            events = Queue()
        if type(events) is not Queue:
            raise TypeError("events must be a FIFO queue.Queue")
        if events.maxsize > 0:
            raise ValueError("Use Queue() with maxsize=0; bounded queues can lose events")
        if clock is not None and not callable(clock):
            raise TypeError("clock must be callable")

        self.events = events
        self._clock = time.monotonic if clock is None else clock
        self._peers: dict[tuple[str, int], Peer] = {}
        self._lock = Lock()
        # Khoa rieng cho start/stop; monitor khong giu khoa nay khi quet.
        self._monitor_lock = Lock()
        self._stop_event = Event()
        self._monitor_thread: Optional[Thread] = None

    @staticmethod
    def _positive_number(value: float, label: str) -> float:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError(f"{label} must be a number")
        if not math.isfinite(value) or value <= 0:
            raise ValueError(f"{label} must be finite and greater than zero")
        return float(value)

    @staticmethod
    def _validate_peer(name: str, ip: str, tcp_port: int, status: str) -> str:
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

    def update_peer(self, name: str, ip: str, tcp_port: int, status: str) -> Peer:
        """Them/cap nhat peer, lam moi last_seen, tra ve ban sao peer.
        Du lieu sai gay TypeError/ValueError truoc khi thay doi registry.
        HELLO lap lai cung status chi lam moi du lieu, khong phat su kien.
        """
        ip = self._validate_peer(name, ip, tcp_port, status)
        key = (ip, tcp_port)
        with self._lock:
            previous = self._peers.get(key)
            # Doc clock trong lock de cap nhat va xoa het han khong tranh chap.
            peer: Peer = {
                "name": name,
                "ip": ip,
                "tcp_port": tcp_port,
                "status": status,
                "last_seen": float(self._clock()),
            }
            self._peers[key] = peer
            if previous is None:
                self.events.put_nowait(("online", peer.copy()))
            elif previous["status"] != status:
                self.events.put_nowait(("status_changed", peer.copy()))
            # Queue khong gioi han: put_nowait khong cho cho nguoi doc.
            # Phat trong lock giu dung thu tu online/status_changed/offline.
            return peer.copy()

    def get_peers(self) -> list[Peer]:
        """Lay anh chup danh sach; nguoi goi duoc sua ban sao an toan.

        Ham nay khong tu xoa peer. main.py phai bat timeout monitor,
        hoac chu dong goi remove_expired_peers().
        """
        with self._lock:
            return [peer.copy() for peer in self._peers.values()]

    def remove_expired_peers(self) -> list[Peer]:
        """Xoa peer im lang QUA timeout, phat offline mot lan cho moi peer."""
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

    def start_timeout_monitor(self) -> None:
        """Bat mot thread quet het han. Goi nhieu lan khong tao thread trung."""
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

    def stop_timeout_monitor(self) -> None:
        """Dung va join monitor; khong xoa danh sach hay tao offline gia.

        Goi nhieu lan an toan. Co the start lai sau stop.
        main.py nen dung discovery truoc, roi dung monitor trong finally.
        """
        with self._monitor_lock:
            self._stop_event.set()
            if self._monitor_thread is not None:
                self._monitor_thread.join()
                self._monitor_thread = None

    def _monitor_loop(self) -> None:
        # wait() cho phep stop danh thuc ngay, khong can doi het sleep().
        while not self._stop_event.wait(self._check_interval):
            self.remove_expired_peers()
