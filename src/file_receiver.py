"""Receive a FILE payload into downloads/ before acknowledging it to the peer."""

import os
from itertools import count
from pathlib import Path, PureWindowsPath

from protocol import MAX_FILE_SIZE, ProtocolError, encode_file_ok, validate_safe_filename

try:
    from ntpath import isreserved as _reserved_name
except ImportError:
    def _reserved_name(name):
        return PureWindowsPath(name).is_reserved()


def get_download_path(filename: str) -> Path:
    """Return a non-conflicting destination path inside downloads/."""
    name = validate_safe_filename(filename)
    if (
        _reserved_name(name)
        or name.endswith((" ", "."))
        or any(ord(ch) < 32 or ord(ch) == 127 or ch in '<>:"?*' for ch in name)
    ):
        raise ProtocolError("Invalid filename for local storage")

    folder = Path("downloads")
    folder.mkdir(exist_ok=True)
    if folder.is_symlink() or not folder.is_dir():
        raise OSError("downloads must be a local directory")

    original = Path(name)
    for number in count():
        candidate = name if number == 0 else f"{original.stem} ({number}){original.suffix}"
        path = folder / candidate
        if not os.path.lexists(path) and not os.path.lexists(f"{path}.part"):
            return path


def cleanup_partial_file(path) -> None:
    """Remove an incomplete .part temporary file."""
    path = Path(path)
    if not path.name.endswith(".part"):
        raise ValueError("Expected a .part file")
    path.unlink(missing_ok=True)


def _reserve_partial(filename):
    """Exclusively create a temporary .part file for writing."""
    while True:
        final = get_download_path(filename)
        partial = final.with_name(final.name + ".part")
        try:
            stream = partial.open("xb")
        except FileExistsError:
            continue
        return final, partial, stream


def _publish(partial, final, filename):
    """Atomically promote a completed .part file to its final name without overwriting."""
    while True:
        try:
            if os.name == "nt":
                partial.rename(final)
            else:
                os.link(partial, final)
            return final
        except FileExistsError:
            final = get_download_path(filename)


def receive_file(sock, metadata: dict, events=None):
    """Read raw file bytes from sock, save safely to downloads/, and send FILE_OK."""
    filename = metadata.get("filename", "")
    try:
        size = metadata.get("size")
        sender_name = metadata.get("sender_name")
        if type(size) is not int or not 0 <= size <= MAX_FILE_SIZE:
            raise ProtocolError("Invalid file size")
        if not isinstance(filename, str) or not isinstance(sender_name, str) or not sender_name:
            raise ProtocolError("Missing filename or sender name")
        if any(ord(ch) < 32 or ord(ch) == 127 for ch in sender_name):
            raise ProtocolError("Invalid characters in sender name")

        final, partial, stream = _reserve_partial(filename)
        try:
            with stream:
                remaining = size
                while remaining:
                    chunk = sock.recv(min(8192, remaining))
                    if not chunk:
                        raise ConnectionError(f"Transfer interrupted ({size - remaining}/{size} bytes)")
                    stream.write(chunk)
                    remaining -= len(chunk)
            final = _publish(partial, final, filename)
            if os.name == "nt":
                partial = None
        finally:
            if partial is not None:
                cleanup_partial_file(partial)

        try:
            sock.sendall(encode_file_ok())
        except OSError as exc:
            raise ConnectionError(f"File saved at {final}, but FILE_OK could not be sent: {exc}") from exc

        if events is not None:
            events.put(("file_received", {
                "filename": filename, "size": size, "sender_name": sender_name, "saved_path": str(final),
            }))
        return final
    except (OSError, ValueError, ProtocolError) as exc:
        if events is not None:
            display_name = filename if isinstance(filename, str) and filename.isprintable() else repr(filename)
            events.put(("file_error", {"filename": display_name, "error": str(exc)}))
        return None
    finally:
        sock.close()