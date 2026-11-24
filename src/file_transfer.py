"""Send one file per TCP connection and report progress to the console queue."""

import os
import socket
import stat
from pathlib import Path
from threading import Thread

from protocol import (
    MAX_HEADER_LEN,
    ProtocolError,
    encode_file_header,
    is_file_ok,
    recv_header_line,
)

CHUNK_SIZE = 8192


def _open_source(path, flags):
    """Open source file with O_NONBLOCK to avoid hanging on special files."""
    return os.open(path, flags | getattr(os, "O_NONBLOCK", 0))


def send_file(
    peer_id: tuple[str, int],
    file_path: str,
    sender_name: str = "",
    events=None,
    tcp_manager=None,
) -> Thread:
    """Start a background sender thread and emit progress/completion events."""
    path = Path(file_path)
    if tcp_manager is not None:
        if events is None:
            events = tcp_manager.events
        if not sender_name:
            sender_name = tcp_manager.name

    def emit(kind, **data):
        if events is not None:
            name = path.name
            if kind == "file_error" and not name.isprintable():
                name = repr(name)
            events.put((kind, {"filename": name, **data}))

    def transfer():
        try:
            with open(path, "rb", opener=_open_source) as source:
                info = os.fstat(source.fileno())
                if not stat.S_ISREG(info.st_mode):
                    raise ValueError("Source must be a regular file")
                size = info.st_size
                header = encode_file_header(sender_name, path.name, size)
                if len(header) > MAX_HEADER_LEN:
                    raise ProtocolError("FILE header is too long")

                if tcp_manager is None:
                    sock = socket.create_connection(peer_id, timeout=10.0)
                    peer_name = f"{peer_id[0]}:{peer_id[1]}"
                else:
                    sock, address, peer_name = tcp_manager.open_file_socket(peer_id)

                with sock:
                    if tcp_manager is not None:
                        state = getattr(tcp_manager, "chat_state", None)
                        if state is not None and peer_name == f"{address[0]}:{address[1]}":
                            peer_name = state.get_peer_name(address)
                    sock.sendall(header)
                    sent = 0
                    next_percent = 25
                    while sent < size:
                        chunk = source.read(min(CHUNK_SIZE, size - sent))
                        if not chunk:
                            raise OSError(f"Source ended early ({sent}/{size} bytes)")
                        sock.sendall(chunk)
                        sent += len(chunk)
                        while next_percent < 100 and sent * 100 >= size * next_percent:
                            emit("file_progress", percent=next_percent, peer_name=peer_name)
                            next_percent += 25

                    sock.shutdown(socket.SHUT_WR)
                    if not is_file_ok(recv_header_line(sock)):
                        raise ProtocolError("Peer did not confirm the transfer with FILE_OK")

            emit("file_progress", percent=100, peer_name=peer_name)
            emit("file_sent", size=size, peer_name=peer_name)
        except (OSError, ValueError, ProtocolError) as exc:
            emit("file_error", error=str(exc))

    worker = Thread(target=transfer, name="File-Sender", daemon=True)
    worker.start()
    return worker