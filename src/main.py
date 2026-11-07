"""Milestone 2 app entry point: connect A, B, and C's modules."""

import argparse
from queue import Queue

from cli import run_cli
from peer_registry import PeerRegistry
from udp_discovery import UDPDiscovery

# Kiểm tra chuỗi port từ terminal thành int, ktra từ 1 -> 65535 sai báo lỗi
def tcp_port(value):
    try:
        number = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("TCP port must be an integer") from exc
    if not 1 <= number <= 65535:
        raise argparse.ArgumentTypeError("TCP port must be between 1 and 65535")
    return number


def main(): # Đọc tham số, tạo Queue + Registry + Discovery, chạy CLI, rồi dừng các module
    parser = argparse.ArgumentParser(description="LAN Chat - Milestone 2")
    parser.add_argument("--name", required=True, help="Your nickname")
    parser.add_argument("--tcp-port", type=tcp_port, required=True, help="TCP port advertised in HELLO (M3)")
    parser.add_argument("--bcast", default="255.255.255.255", help="UDP broadcast destination")
    args = parser.parse_args()

    if not args.name.strip() or "|" in args.name or any(ord(ch) < 32 or ord(ch) == 127 for ch in args.name):
        parser.error("--name must be nonempty and contain no '|' or control characters")

    events = Queue() # Hàng đợi thông báo C -> B
    registry = PeerRegistry(events=events, timeout_seconds=10.0) # C: nơi lưu các peer
    
    discovery = UDPDiscovery(  # A: dùng CHÍNH registry đó
        name=args.name,
        tcp_port=args.tcp_port,
        registry=registry,
        bcast_addr=args.bcast,
        port=9999,
    )

    try: 
        registry.start_timeout_monitor() # C bật Thread kiểm tra peer hết hạn
        discovery.start() # A mở UDP socket và bật 2 Thread
        print(f"[*] {args.name}: UDP 9999, advertised TCP port {args.tcp_port}")
        run_cli(registry, discovery, events) # # B chạy CLI trong Main Thread và bắt đầu nhận lệnh từ người dùng
    finally:
        discovery.stop()
        registry.stop_timeout_monitor()
        print("[*] Application stopped")


if __name__ == "__main__":
    main()
