import socket
import os

MAX_FILE_SIZE = 1024 * 1024 * 1024 # dùng cho file

MAX_HEADER_LEN = 1024  # Chặn header rác quá dài không có ký tự '\n'


def encode_hi(name: str, tcp_port: int) -> bytes:
    """Đóng gói bản tin định danh đầu kết nối: HI|<name>|<tcp_port>\n"""
    clean_name = name.replace("|", "_").replace("\n", "").replace("\r", "")
    return f"HI|{clean_name}|{int(tcp_port)}\n".encode("utf-8")


def encode_msg(text: str) -> bytes:
    """Đóng gói tin nhắn chat: MSG|<byte_length>\n<UTF-8 bytes>"""
    payload = text.encode("utf-8")
    header = f"MSG|{len(payload)}\n".encode("utf-8")
    return header + payload


def encode_bye() -> bytes:
    """Đóng gói bản tin kết thúc phiên chat: BYE\n"""
    return b"BYE\n"


def _recv_exact(sock: socket.socket, num_bytes: int) -> bytes:
    """Đọc chính xác num_bytes từ TCP stream. Ném ConnectionError nếu đứt giữa chừng."""
    chunks = bytearray()
    while len(chunks) < num_bytes:
        chunk = sock.recv(num_bytes - len(chunks))
        if not chunk:
            raise ConnectionError("Connection closed prematurely while reading payload")
        chunks.extend(chunk)
    return bytes(chunks)


def _recv_line(sock: socket.socket) -> str:
    """Đọc từng byte cho tới dấu '\n' để lấy trọn vẹn dòng header."""
    line = bytearray()
    while True:
        ch = sock.recv(1)
        if not ch:
            if not line:
                return ""  # Đối phương đóng kết nối sạch sẽ (EOF)
            raise ConnectionError("Connection closed prematurely mid-header")
        if ch == b"\n":
            break
        line.extend(ch)
        if len(line) > MAX_HEADER_LEN:
            raise ValueError("Header exceeds maximum allowed length")
    return line.decode("utf-8")


def recv_frame(sock: socket.socket) -> tuple | None:
    """
    Đọc và giải mã 1 frame từ socket.
    Trả về:
      - ("HI", name, tcp_port)
      - ("MSG", text)
      - ("BYE",)
      - None nếu đối phương ngắt kết nối (EOF)
    Ném ValueError nếu frame sai định dạng giao thức.
    """
    header = _recv_line(sock)
    if header == "":
        return None

    parts = header.split("|")
    frame_type = parts[0]

    if frame_type == "HI":
        if len(parts) != 3 or not parts[1].strip():
            raise ValueError(f"Malformed HI frame: {header!r}")
        name = parts[1]
        tcp_port = int(parts[2])
        if not (1 <= tcp_port <= 65535):
            raise ValueError(f"Invalid TCP port in HI: {tcp_port}")
        return ("HI", name, tcp_port)

    if frame_type == "MSG":
        if len(parts) != 2:
            raise ValueError(f"Malformed MSG header: {header!r}")
        length = int(parts[1])
        if length < 0:
            raise ValueError("Negative message length")
        payload = _recv_exact(sock, length)
        return ("MSG", payload.decode("utf-8"))

    if frame_type == "BYE":
        if len(parts) != 1:
            raise ValueError(f"Malformed BYE frame: {header!r}")
        return ("BYE",)

    raise ValueError(f"Unknown frame type: {frame_type!r}")

#Hàm cho file
class ProtocolError(Exception):
    pass

def validate_safe_filename(filename: str) -> str:
    if not filename or "\n" in filename or "\r" in filename or "|" in filename:
        raise ProtocolError("Invalid filename characters")
    if "/" in filename or "\\" in filename or ".." in filename:
        raise ProtocolError("Path traversal is not allowed")
    base = os.path.basename(filename)
    if base != filename or base in (".", ".."):
        raise ProtocolError("Filename must not contain directory paths")
    return base


def encode_file_header(sender_name: str, filename: str, size: int) -> bytes:
    if not sender_name or "|" in sender_name or "\n" in sender_name or "\r" in sender_name:
        raise ProtocolError("Invalid sender name")
    safe_name = validate_safe_filename(filename)
    if not isinstance(size, int) or isinstance(size, bool) or size < 0 or size > MAX_FILE_SIZE:
        raise ProtocolError("Invalid file size")
    header = f"FILE|{sender_name}|{safe_name}|{size}\n"
    return header.encode("utf-8")


def parse_file_header(line: str) -> dict:
    clean = line.rstrip("\r\n")
    parts = clean.split("|")
    if len(parts) != 4 or parts[0] != "FILE":
        raise ProtocolError("Malformed FILE header")
    sender_name = parts[1].strip()
    if not sender_name:
        raise ProtocolError("Empty sender name")
    safe_name = validate_safe_filename(parts[2])
    try:
        size = int(parts[3])
    except ValueError as exc:
        raise ProtocolError("Invalid file size") from exc
    if size < 0 or size > MAX_FILE_SIZE:
        raise ProtocolError("File size out of bounds")
    return {
        "type": "FILE",
        "sender_name": sender_name,
        "filename": safe_name,
        "size": size,
    }


def encode_file_ok() -> bytes:
    return b"FILE_OK\n"


def is_file_ok(line: str) -> bool:
    return line.rstrip("\r\n") == "FILE_OK"


def recv_header_line(sock) -> str:
    return _recv_line(sock)