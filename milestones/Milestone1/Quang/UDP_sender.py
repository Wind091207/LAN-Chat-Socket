
import socket

TARGET_HOST = "127.0.0.1"
TARGET_PORT = 5000


def run_sender():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    print(f"UDP Sender ready: {TARGET_HOST}:{TARGET_PORT}")
    print("Type 'quit' or 'exit' to stop.")

    try:
        while True:
            msg = input("Sender > ")

            if not msg.strip():
                continue

            if msg.strip().lower() in ("quit", "exit"):
                break

            data = msg.encode("utf-8")
            sock.sendto(data, (TARGET_HOST, TARGET_PORT))

            print(f"Sent: {len(data)} bytes")

    finally:
        sock.close()
        print("UDP Sender closed.")


if __name__ == "__main__":
    run_sender()
