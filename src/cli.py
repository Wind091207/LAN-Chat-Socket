"""Milestone 2 command-line interface (B's module)."""

from __future__ import annotations

import threading
from queue import Empty


HELP = (
    "Commands:\n"
    "  /list                 Show discovered peers\n"
    "  /status online        Set your status to online\n"
    "  /status away          Set your status to away\n"
    "  /help                 Show these commands\n"
    "  /quit                 Exit the application"
)

# ở đây 2 thread showevent và run_cli chạy đồng thời. VD: ta đang nhập > /sta... khi đang nhập như vậy sẽ có thông báo mình đang online ngay
# chứ không đợi mình enter rồi mới in mình đang online. (Tức main thread đợi ta nhập, nhưng event thread ngay lập tức in)
def _show_events(events, stop_event):
    """Print discovery notifications while the CLI waits for input."""
    while not stop_event.is_set():
        try:
            event_type, peer = events.get(timeout=0.2) # B lấy sự kiện C vừa đưa vào Queue. Chỗ này lấy ra liên tục tuỳ theo trạng thái nên in ra rất nhanh ko sợ đầy queue
        except Empty:
            continue

        name = peer["name"]
        if event_type == "online":
            print(f"\n[*] {name} ({peer['ip']}:{peer['tcp_port']}) is online") # C phát hiện thay đổi → C đưa sự kiện vào Queue → B lấy ra → B in thông báo.
        elif event_type == "offline":
            print(f"\n[*] {name} is offline")
        elif event_type == "status_changed":
            print(f"\n[*] {name} is now {peer['status']}")


def run_cli(registry, discovery, events):
    """Handle M2 commands using the shared registry and discovery objects."""
    stop_events = threading.Event()
    event_thread = threading.Thread(
        target=_show_events, args=(events, stop_events), daemon=True
    )
    event_thread.start()

    print("UDP Discovery is running. Type /help to see commands.")
    try:
        while True:
            try:
                line = input("> ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nExiting...")
                break

            if not line:
                continue

            if line == "/list":
                peers = sorted(
                    registry.get_peers(),
                    key=lambda p: (p["name"].casefold(), p["ip"], p["tcp_port"]),
                )
                if not peers:
                    print("No other peers discovered.")
                else:
                    for number, peer in enumerate(peers, start=1):
                        print(
                            f"{number}. {peer['name']} "
                            f"({peer['ip']}:{peer['tcp_port']}) "
                            f"{peer['status']}"
                        )
            elif line.startswith("/status"):
                args = line.split()
                if len(args) != 2 or args[0] != "/status" or args[1] not in ("online", "away"):
                    print("Usage: /status online | /status away")
                else:
                    discovery.set_status(args[1])
                    print(f"Your status: {args[1]} (sent in the next HELLO)")
            elif line == "/help":
                print(HELP)
            elif line == "/quit":
                print("Exiting...")
                break
            else:
                print("Unknown command. Type /help. TCP chat starts in M3.")
    finally:
        stop_events.set()
        event_thread.join(timeout=0.5)
