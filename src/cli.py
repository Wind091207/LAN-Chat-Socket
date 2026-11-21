"""Milestone 3 command-line interface (A's module)."""

from __future__ import annotations

import threading
from queue import Empty


HELP = (
    "Commands:\n"
    "  /list                 Show discovered peers and unread messages\n"
    "  /status online        Set your status to online\n"
    "  /status away          Set your status to away\n"
    "  /chat <name|number>   Start or switch chat with a peer\n"
    "  /leave                Leave the current chat session\n"
    "  /help                 Show these commands\n"
    "  /quit                 Exit the application\n"
    "  <text>                Send a message to the current chat partner"
)


def _make_peer_id(peer: dict) -> tuple[str, int]:
    """Create the canonical registry key (ip, tcp_port) for a peer."""
    return (peer["ip"], int(peer["tcp_port"]))


def _get_sorted_peers(registry) -> list[dict]:
    """Return discovered peers in the exact deterministic order used by /list."""
    return sorted(
        registry.get_peers(),
        key=lambda p: (p["name"].casefold(), p["ip"], p["tcp_port"]),
    )


def _resolve_peer(target: str, peers: list[dict]) -> tuple[dict | None, str | None]:
    """Resolve a peer from either a 1-based /list index or a peer name."""
    if not peers:
        return None, "No other peers discovered."

    if target.isdigit():
        index = int(target)
        if 1 <= index <= len(peers):
            return peers[index - 1], None
        return (
            None,
            f"Invalid peer number: {target}. Use /list to check available numbers.",
        )

    matches = [p for p in peers if p["name"].casefold() == target.casefold()]
    if len(matches) == 1:
        return matches[0], None
    if len(matches) > 1:
        return None, f"Multiple peers named '{target}'. Use /chat <number> from /list."
    return None, f"Peer '{target}' not found. Use /list to see discovered peers."


def _print_history(history, partner_name: str) -> None:
    """Display stored chat messages when opening a conversation."""
    if not history:
        return

    print("--- Recent messages ---")
    for item in history:
        if isinstance(item, dict):
            sender = (
                item.get("sender")
                or item.get("name")
                or (
                    "You"
                    if item.get("is_self") or item.get("direction") == "out"
                    else partner_name
                )
            )
            content = (
                item.get("text")
                or item.get("message")
                or item.get("content")
                or str(item)
            )
            print(f"  [{sender}]: {content}")
        else:
            print(f"  {item}")
    print("-----------------------")


def _extract_event_peer_info(data) -> tuple[tuple[str, int] | None, str]:
    """Safely extract (peer_id, peer_name) from event payloads emitted by B or C."""
    if isinstance(data, dict):
        peer_obj = data.get("peer") if isinstance(data.get("peer"), dict) else data
        peer_id = data.get("peer_id")
        if peer_id is None and "ip" in peer_obj and "tcp_port" in peer_obj:
            peer_id = _make_peer_id(peer_obj)
        name = (
            data.get("name")
            or data.get("sender")
            or peer_obj.get("name")
            or (f"{peer_id[0]}:{peer_id[1]}" if peer_id else "Peer")
        )
        return peer_id, name

    if isinstance(data, tuple) and len(data) == 2:
        return data, f"{data[0]}:{data[1]}"

    return None, "Peer"


def _show_events(
    events, stop_event, chat_state, state: dict, state_lock: threading.Lock
):
    """Print discovery and incoming chat notifications while the CLI waits for input."""
    while not stop_event.is_set():
        try:
            event_type, data = events.get(timeout=0.2)
        except Empty:
            continue

        if event_type == "online":
            print(f"\n[*] {data['name']} ({data['ip']}:{data['tcp_port']}) is online")
        elif event_type == "offline":
            peer_id = _make_peer_id(data)
            print(f"\n[*] {data['name']} is offline")
            with state_lock:
                if state["partner_id"] == peer_id:
                    state["partner_id"] = None
                    state["partner_name"] = None
                    if chat_state:
                        chat_state.set_current_partner(None)
                    print(f"[*] Chat ended because {data['name']} went offline.")
        elif event_type == "status_changed":
            print(f"\n[*] {data['name']} is now {data['status']}")
        elif event_type == "message":
            peer_id, sender_name = _extract_event_peer_info(data)
            text = ""
            if isinstance(data, dict):
                text = (
                    data.get("text") or data.get("message") or data.get("content") or ""
                )
            else:
                text = str(data)

            with state_lock:
                is_active_partner = (
                    peer_id is not None and state["partner_id"] == peer_id
                )

            if is_active_partner:
                print(f"\n[{sender_name}]: {text}")
                if chat_state and peer_id is not None:
                    chat_state.mark_as_read(peer_id)
            else:
                unread = (
                    chat_state.get_unread_count(peer_id)
                    if (chat_state and peer_id is not None)
                    else 1
                )
                print(
                    f"\n[*] New message from {sender_name} ({unread} unread). "
                    f"Type /chat {sender_name} to open."
                )
        elif event_type in ("leave", "peer_left", "bye", "disconnected", "chat_closed"):
            peer_id, sender_name = _extract_event_peer_info(data)
            with state_lock:
                if peer_id is not None and state["partner_id"] == peer_id:
                    state["partner_id"] = None
                    state["partner_name"] = None
                    if chat_state:
                        chat_state.set_current_partner(None)
                    print(f"\n[*] {sender_name} left the chat.")
                else:
                    print(f"\n[*] {sender_name} closed the chat.")


def run_cli(registry, discovery, events, tcp_manager=None, chat_state=None):
    """Handle M3 CLI commands using registry, discovery, TCP manager, and chat state."""
    state = {"partner_id": None, "partner_name": None}
    state_lock = threading.Lock()

    stop_events = threading.Event()
    event_thread = threading.Thread(
        target=_show_events,
        args=(events, stop_events, chat_state, state, state_lock),
        daemon=True,
    )
    event_thread.start()

    print("LAN Chat is running. Type /help to see commands.")
    try:
        while True:
            with state_lock:
                partner_name = state["partner_name"]
            prompt = f"[{partner_name}]> " if partner_name else "> "

            try:
                line = input(prompt).strip()
            except (EOFError, KeyboardInterrupt):
                print("\nExiting...")
                break

            if not line:
                continue

            if line == "/list":
                peers = _get_sorted_peers(registry)
                if not peers:
                    print("No other peers discovered.")
                else:
                    for number, peer in enumerate(peers, start=1):
                        peer_id = _make_peer_id(peer)
                        unread = (
                            chat_state.get_unread_count(peer_id) if chat_state else 0
                        )
                        unread_tag = f" ({unread} unread)" if unread > 0 else ""
                        print(
                            f"{number}. {peer['name']} "
                            f"({peer['ip']}:{peer['tcp_port']}) "
                            f"{peer['status']}{unread_tag}"
                        )

            elif line.startswith("/status"):
                args = line.split()
                if (
                    len(args) != 2
                    or args[0] != "/status"
                    or args[1] not in ("online", "away")
                ):
                    print("Usage: /status online | /status away")
                else:
                    discovery.set_status(args[1])
                    print(f"Your status: {args[1]} (sent in the next HELLO)")

            elif line == "/chat" or line.startswith("/chat "):
                target = line[5:].strip()
                if not target:
                    print("Usage: /chat <name|number>")
                    continue

                peers = _get_sorted_peers(registry)
                peer, error = _resolve_peer(target, peers)
                if error:
                    print(error)
                    continue

                target_id = _make_peer_id(peer)
                with state_lock:
                    old_partner_id = state["partner_id"]

                if old_partner_id == target_id:
                    print(f"Already chatting with {peer['name']}.")
                    continue

                if tcp_manager:
                    try:
                        tcp_manager.connect_peer(peer)
                    except Exception as exc:
                        print(f"Failed to connect to {peer['name']}: {exc}")
                        with state_lock:
                            state["partner_id"] = None
                            state["partner_name"] = None
                        if chat_state:
                            chat_state.set_current_partner(None)
                        continue

                with state_lock:
                    state["partner_id"] = target_id
                    state["partner_name"] = peer["name"]

                if chat_state:
                    chat_state.set_current_partner(target_id)
                    chat_state.mark_as_read(target_id)
                    history = chat_state.get_history(target_id)
                else:
                    history = []

                print(
                    f"--- Chatting with {peer['name']} "
                    f"({peer['ip']}:{peer['tcp_port']}) [Type /leave to exit] ---"
                )
                _print_history(history, peer["name"])

            elif line == "/leave":
                with state_lock:
                    current_id = state["partner_id"]
                    current_name = state["partner_name"]

                if current_id is None:
                    print("You are not in an active chat session.")
                    continue

                if tcp_manager:
                    try:
                        tcp_manager.leave_chat(current_id)
                    except Exception as exc:
                        print(f"Warning while leaving chat: {exc}")

                with state_lock:
                    state["partner_id"] = None
                    state["partner_name"] = None

                if chat_state:
                    chat_state.set_current_partner(None)

                print(f"Left chat with {current_name}.")

            elif line == "/help":
                print(HELP)

            elif line == "/quit":
                print("Exiting...")
                break

            elif line.startswith("/"):
                print("Unknown command. Type /help to see available commands.")

            else:
                with state_lock:
                    current_id = state["partner_id"]
                    current_name = state["partner_name"]

                if current_id is None:
                    print("No active chat. Use /list and /chat <name|number> first.")
                    continue

                if tcp_manager:
                    try:
                        tcp_manager.send_message(current_id, line)
                    except Exception as exc:
                        print(f"Failed to send message to {current_name}: {exc}")
                        continue

                if chat_state:
                    chat_state.add_message(current_id, {"sender": "You", "text": line})

                print(f"[You]: {line}")

    finally:
        with state_lock:
            active_id = state["partner_id"]
            state["partner_id"] = None
            state["partner_name"] = None

        if active_id is not None and tcp_manager:
            try:
                tcp_manager.leave_chat(active_id)
            except Exception:
                pass

        if chat_state:
            chat_state.set_current_partner(None)

        stop_events.set()
        event_thread.join(timeout=0.5)
