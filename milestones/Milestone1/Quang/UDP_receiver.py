import socket

HOST = "0.0.0.0"
PORT = 5000


def run_receiver():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((HOST, PORT))

    print(f"UDP Receiver listening on port {PORT}")

    try:
        while True:
            data, addr = sock.recvfrom(1024)
            msg = data.decode("utf-8", errors="replace")

            print(f"Received from {addr[0]}:{addr[1]}: {msg}")

    except KeyboardInterrupt:
        print("\nUDP Receiver stopped.")

    finally:
        sock.close()


if __name__ == "__main__":
    run_receiver()
