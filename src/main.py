"""Milestone 3 app entry point: connect UDP Discovery, TCP Chat, and CLI modules."""

import argparse
from queue import Queue

from chat_state import ChatState
from cli import run_cli
from peer_registry import PeerRegistry
from tcp_transport import TCPTransport
from udp_discovery import UDPDiscovery


def tcp_port(value):
    try:
        number = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("TCP port must be an integer") from exc
    if not 1 <= number <= 65535:
        raise argparse.ArgumentTypeError("TCP port must be between 1 and 65535")
    return number


def main():
    parser = argparse.ArgumentParser(description="LAN Chat - Milestone 3")
    parser.add_argument("--name", required=True, help="Your nickname")
    parser.add_argument("--tcp-port", type=tcp_port, required=True, help="TCP port for P2P chat")
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
    )

    try:
        tcp.start()
        registry.start_timeout_monitor()
        discovery.start()
        print(f"[*] {args.name}: listening TCP {args.tcp_port}, UDP broadcast 9999")
        run_cli(registry, discovery, events, tcp_manager=tcp, chat_state=chat_state)
    finally:
        discovery.stop()
        tcp.stop()
        registry.stop_timeout_monitor()
        print("[*] Application stopped")


if __name__ == "__main__":
    main()