import os
from protocol import encode_file_ok


def receive_file(sock, metadata, events=None):
    os.makedirs("downloads", exist_ok=True)
    out_path = os.path.join("downloads", metadata["filename"])
    remaining = metadata["size"]

    with open(out_path, "wb") as f:
        while remaining > 0:
            chunk = sock.recv(min(8192, remaining))
            if not chunk:
                raise ConnectionError("Incomplete file stream")
            f.write(chunk)
            remaining -= len(chunk)

    print(
        f"\n[TEST-B] Received '{metadata['filename']}' ({metadata['size']} bytes) "
        f"from {metadata['sender_name']} -> saved to {out_path}"
    )
    sock.sendall(encode_file_ok())