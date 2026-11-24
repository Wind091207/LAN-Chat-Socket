"""Khởi tạo và kết nối các module UDP Discovery, TCP Chat, File Transfer và CLI."""

import argparse
import inspect
from queue import Queue

from chat_state import ChatState
from cli import run_cli
from peer_registry import PeerRegistry
from tcp_transport import TCPTransport
from udp_discovery import UDPDiscovery

try:
    from file_receiver import receive_file
except ImportError:
    receive_file = None

try:
    from file_transfer import send_file
except ImportError:
    send_file = None


def tcp_port(value):
    """Kiểm tra tính hợp lệ của tham số cổng TCP (1-65535)."""
    try:
        number = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("TCP port must be an integer") from exc
    if not 1 <= number <= 65535:
        raise argparse.ArgumentTypeError("TCP port must be between 1 and 65535")
    return number


def _bind_file_receiver(events):
    """Gắn hàng đợi events vào hàm nhận file của module C."""
    if receive_file is None:
        return None
    params = inspect.signature(receive_file).parameters

    def _receiver(sock, metadata):
        kwargs = {}
        if "events" in params:
            kwargs["events"] = events
        return receive_file(sock, metadata, **kwargs)

    return _receiver


def _bind_file_sender(sender_name, events, tcp_manager):
    """Gắn ngữ cảnh phiên chạy vào hàm gửi file của module C."""
    if send_file is None:
        return None
    params = inspect.signature(send_file).parameters

    def _sender(peer_id, file_path):
        kwargs = {}
        if "sender_name" in params:
            kwargs["sender_name"] = sender_name
        if "events" in params:
            kwargs["events"] = events
        if "tcp_manager" in params:
            kwargs["tcp_manager"] = tcp_manager
        return send_file(peer_id, file_path, **kwargs)

    return _sender


def main():
    """Điểm khởi chạy chính của ứng dụng LAN Chat."""
    parser = argparse.ArgumentParser(description="LAN Chat - Milestone 4")
    parser.add_argument("--name", required=True, help="Your nickname")
    parser.add_argument("--tcp-port", type=tcp_port, required=True, help="TCP port for P2P chat and file transfer")
    parser.add_argument("--bcast", default="255.255.255.255", help="UDP broadcast destination")
    args = parser.parse_args()

    if not args.name.strip() or "|" in args.name or any(ord(ch) < 32 or ord(ch) == 127 for ch in args.name):
        parser.error("--name must be nonempty and contain no '|' or control characters")

    events = Queue()
    registry = PeerRegistry(events=events, timeout_seconds=10.0)
    chat_state = ChatState()

    discovery = UDPDiscovery(
        name=args.name,
        tcp_port=args.tcp_port,
        registry=registry,
        bcast_addr=args.bcast,
        port=9999,
    )
    tcp = TCPTransport(
        name=args.name,
        tcp_port=args.tcp_port,
        chat_state=chat_state,
        events=events,
        file_receiver=_bind_file_receiver(events),
    )

    cli_params = inspect.signature(run_cli).parameters
    cli_kwargs = {
        "tcp_manager": tcp,
        "chat_state": chat_state,
    }
    if "file_sender" in cli_params:
        cli_kwargs["file_sender"] = _bind_file_sender(args.name, events, tcp)
    if "sender_name" in cli_params:
        cli_kwargs["sender_name"] = args.name

    try:
        tcp.start()
        registry.start_timeout_monitor()
        discovery.start()
        print(f"[*] {args.name}: listening TCP {args.tcp_port}, UDP broadcast 9999")
        run_cli(registry, discovery, events, **cli_kwargs)
    finally:
        discovery.stop()
        tcp.stop()
        registry.stop_timeout_monitor()
        print("[*] Application stopped")


if __name__ == "__main__":
    main()