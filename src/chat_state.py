from __future__ import annotations

import json
import os
import re
import threading
import time
from typing import Any


class ChatState:
    def __init__(self, storage_path: str | None = None):
        self._lock = threading.Lock()
        self._histories: dict[tuple[str, int], list[dict[str, Any]]] = {}
        self._unread: dict[tuple[str, int], int] = {}
        self._peer_names: dict[tuple[str, int], str] = {}
        self._current_partner: tuple[str, int] | None = None
        self._storage: ChatJsonStorage | None = None

        if storage_path:
            self.bind_storage(storage_path)

    def bind_storage(self, storage_path: str) -> None:
        storage = ChatJsonStorage(storage_path)
        histories, unread, peer_names = storage.load()
        with self._lock:
            self._storage = storage
            for pid, msgs in histories.items():
                if pid not in self._histories:
                    self._histories[pid] = msgs
            for pid, count in unread.items():
                if pid not in self._unread and count > 0:
                    self._unread[pid] = count
            for pid, name in peer_names.items():
                if pid not in self._peer_names and name:
                    self._peer_names[pid] = name

    def _persist_locked(self) -> None:
        if self._storage is not None:
            self._storage.save(self._histories, self._unread, self._peer_names)

    def set_peer_name(self, peer_id: tuple[str, int], name: str) -> None:
        if not name:
            return
        with self._lock:
            if self._peer_names.get(peer_id) != name:
                self._peer_names[peer_id] = name
                self._persist_locked()

    def get_peer_name(self, peer_id: tuple[str, int]) -> str:
        with self._lock:
            return self._peer_names.get(peer_id, f"{peer_id[0]}:{peer_id[1]}")

    def set_current_partner(self, peer_id: tuple[str, int] | None) -> None:
        with self._lock:
            self._current_partner = peer_id
            if peer_id is not None and self._unread.get(peer_id, 0) > 0:
                self._unread[peer_id] = 0
                self._persist_locked()

    def get_current_partner(self) -> tuple[str, int] | None:
        with self._lock:
            return self._current_partner

    def add_message(self, peer_id: tuple[str, int], *args, **kwargs) -> None:
        sender = kwargs.get("sender")
        text = kwargs.get("text")
        is_me = kwargs.get("is_me")
        timestamp = kwargs.get("timestamp")

        if len(args) == 1:
            first = args[0]
            if isinstance(first, dict):
                entry = dict(first)
                entry.setdefault("timestamp", time.time())
            else:
                content = text if text is not None else str(first)
                entry = {
                    "sender": sender or ("You" if is_me else self.get_peer_name(peer_id)),
                    "text": content,
                    "is_me": bool(is_me),
                    "timestamp": timestamp if timestamp is not None else time.time(),
                }
        elif len(args) >= 2:
            arg_sender = str(args[0])
            arg_text = str(args[1])
            arg_is_me = bool(args[2]) if len(args) >= 3 else bool(is_me or arg_sender == "You")
            entry = {
                "sender": arg_sender,
                "text": arg_text,
                "is_me": arg_is_me,
                "timestamp": timestamp if timestamp is not None else time.time(),
            }
        else:
            entry = {
                "sender": sender or ("You" if is_me else self.get_peer_name(peer_id)),
                "text": text or "",
                "is_me": bool(is_me),
                "timestamp": timestamp if timestamp is not None else time.time(),
            }

        outgoing = bool(
            entry.get("is_me")
            or entry.get("is_self")
            or entry.get("direction") == "out"
            or entry.get("sender") == "You"
        )

        with self._lock:
            if not outgoing and entry.get("sender") and entry.get("sender") != "You":
                self._peer_names[peer_id] = str(entry["sender"])

            msgs = self._histories.setdefault(peer_id, [])
            msgs.append(entry)
            if len(msgs) > 500:
                self._histories[peer_id] = msgs[-500:]

            if not outgoing and self._current_partner != peer_id:
                self._unread[peer_id] = self._unread.get(peer_id, 0) + 1

            self._persist_locked()

    def get_history(self, peer_id: tuple[str, int]) -> list[dict[str, Any]]:
        with self._lock:
            return list(self._histories.get(peer_id, []))

    def get_unread_count(self, peer_id: tuple[str, int]) -> int:
        with self._lock:
            return self._unread.get(peer_id, 0)

    def get_all_unread(self) -> dict[tuple[str, int], int]:
        with self._lock:
            return {pid: cnt for pid, cnt in self._unread.items() if cnt > 0}

    def mark_as_read(self, peer_id: tuple[str, int]) -> None:
        with self._lock:
            if self._unread.get(peer_id, 0) != 0:
                self._unread[peer_id] = 0
                self._persist_locked()

    def clear_history(self, peer_id: tuple[str, int] | None = None) -> None:
        with self._lock:
            if peer_id is None:
                self._histories.clear()
                self._unread.clear()
            else:
                self._histories.pop(peer_id, None)
                self._unread.pop(peer_id, None)
            self._persist_locked()


class ChatJsonStorage:
    def __init__(self, file_path: str):
        self.file_path = file_path
        parent = os.path.dirname(file_path)
        if parent:
            os.makedirs(parent, exist_ok=True)

    @staticmethod
    def _encode_key(peer_id: tuple[str, int]) -> str:
        return f"{peer_id[0]}:{int(peer_id[1])}"

    @staticmethod
    def _decode_key(raw_key: str) -> tuple[str, int] | None:
        if ":" not in raw_key:
            return None
        ip, port_str = raw_key.rsplit(":", 1)
        try:
            return (ip, int(port_str))
        except ValueError:
            return None

    def load(
        self,
    ) -> tuple[
        dict[tuple[str, int], list[dict[str, Any]]],
        dict[tuple[str, int], int],
        dict[tuple[str, int], str],
    ]:
        histories: dict[tuple[str, int], list[dict[str, Any]]] = {}
        unread: dict[tuple[str, int], int] = {}
        peer_names: dict[tuple[str, int], str] = {}

        if not os.path.exists(self.file_path):
            return histories, unread, peer_names

        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            return histories, unread, peer_names

        raw_histories = data.get("histories", {})
        if isinstance(raw_histories, dict):
            for key_str, items in raw_histories.items():
                pid = self._decode_key(key_str)
                if pid is not None and isinstance(items, list):
                    histories[pid] = list(items)

        raw_unread = data.get("unread", {})
        if isinstance(raw_unread, dict):
            for key_str, count in raw_unread.items():
                pid = self._decode_key(key_str)
                if pid is not None:
                    try:
                        val = int(count)
                        if val > 0:
                            unread[pid] = val
                    except (TypeError, ValueError):
                        pass

        raw_names = data.get("peer_names", {})
        if isinstance(raw_names, dict):
            for key_str, name in raw_names.items():
                pid = self._decode_key(key_str)
                if pid is not None and isinstance(name, str) and name:
                    peer_names[pid] = name

        return histories, unread, peer_names

    def save(
        self,
        histories: dict[tuple[str, int], list[dict[str, Any]]],
        unread: dict[tuple[str, int], int],
        peer_names: dict[tuple[str, int], str],
    ) -> None:
        payload = {
            "peer_names": {
                self._encode_key(pid): name
                for pid, name in peer_names.items()
                if name
            },
            "unread": {
                self._encode_key(pid): cnt
                for pid, cnt in unread.items()
                if cnt > 0
            },
            "histories": {
                self._encode_key(pid): msgs
                for pid, msgs in histories.items()
            },
        }
        tmp_path = f"{self.file_path}.tmp"
        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
            os.replace(tmp_path, self.file_path)
        except Exception:
            try:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
            except Exception:
                pass


def build_default_storage_path(user_name: str, tcp_port: int | None = None) -> str:
    safe_name = re.sub(r"[^A-Za-z0-9_-]+", "_", user_name.strip() or "user")
    port_part = f"_{int(tcp_port)}" if tcp_port else ""
    return os.path.join("data", f"chat_state_{safe_name}{port_part}.json")