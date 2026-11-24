"""Milestone 4 command-line interface (A's module - Console UI & File Transfer)."""

from __future__ import annotations

import os
import shutil
import sys
import threading
from datetime import datetime
from queue import Empty

from console_ui import ConsoleUI, set_default_ui

# Bật hỗ trợ màu ANSI trên Windows PowerShell / CMD
if os.name == "nt":
    os.system("")

# Mã màu ANSI gọn nhẹ, dễ nhìn trên cả nền tối lẫn nền sáng
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[95m"
GRAY = "\033[90m"

HELP = (
    f"{BOLD}Commands:{RESET}\n"
    f"  {CYAN}/list{RESET}                 Show discovered peers and unread messages\n"
    f"  {CYAN}/status online{RESET}        Set your status to online\n"
    f"  {CYAN}/status away{RESET}          Set your status to away\n"
    f"  {CYAN}/chat <name|number>{RESET}   Start or switch chat with a peer\n"
    f"  {CYAN}/send <file>{RESET}          Send a file to the current chat partner\n"
    f"  {CYAN}/leave{RESET}                Leave the current chat session\n"
    f"  {CYAN}/help{RESET}                 Show these commands\n"
    f"  {CYAN}/quit{RESET}                 Exit the application\n"
    f"  {CYAN}<text>{RESET}                Send a message to the current chat partner"
)


def _now_str() -> str:
    """Return current local time formatted as HH:MM."""
    return datetime.now().strftime("%H:%M")


def _format_prompt(partner_name: str | None) -> tuple[str, str]:
    """Return (colored_prompt, plain_prompt) so it's clear who you are messaging."""
    if partner_name:
        colored = f"{BOLD}{BLUE}You -> {partner_name}>{RESET} "
        plain = f"You -> {partner_name}> "
    else:
        colored = f"{BOLD}> {RESET}"
        plain = "> "
    return colored, plain


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


def _format_chat_line(
    sender: str, text: str, is_self: bool, ts: str | None = None
) -> str:
    """Format a single chat message with timestamp and distinct sender color."""
    time_tag = f"{GRAY}[{ts or _now_str()}]{RESET} "
    if is_self:
        return f"{time_tag}{BOLD}{BLUE}[You]:{RESET} {text}"
    return f"{time_tag}{BOLD}{GREEN}[{sender}]:{RESET} {text}"


def _print_history(history, partner_name: str, ui: ConsoleUI | None = None) -> None:
    """Display stored chat messages when opening a conversation."""
    if not history:
        return

    emit = ui.show_line if ui is not None else print
    emit(f"{DIM}--- Recent messages ---{RESET}")
    for item in history:
        if isinstance(item, dict):
            is_self = bool(
                item.get("is_me")
                or item.get("is_self")
                or item.get("direction") == "out"
                or item.get("sender") == "You"
            )
            sender = (
                "You"
                if is_self
                else (item.get("sender") or item.get("name") or partner_name)
            )
            content = (
                item.get("text")
                or item.get("message")
                or item.get("content")
                or str(item)
            )
            raw_ts = item.get("timestamp")
            ts_str = (
                datetime.fromtimestamp(raw_ts).strftime("%H:%M")
                if isinstance(raw_ts, (int, float))
                else None
            )
            emit("  " + _format_chat_line(sender, content, is_self=is_self, ts=ts_str))
        else:
            emit(f"  {item}")
    emit(f"{DIM}-----------------------{RESET}")


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


def _print_async(
    text: str, state: dict, state_lock: threading.Lock, ui: ConsoleUI | None = None
) -> None:
    """Clear current prompt line, print incoming line cleanly, and redraw prompt."""
    with state_lock:
        partner_name = state["partner_name"]
    colored_prompt, _ = _format_prompt(partner_name)

    if ui is not None:
        ui.set_prompt(colored_prompt)
        ui.show_notification(text)
        return

    sys.stdout.write(f"\r\033[2K{text}\n{colored_prompt}")
    sys.stdout.flush()


def _format_size(num_bytes: int) -> str:
    """Format byte count into a readable string."""
    return f"{num_bytes:,} bytes"


def _show_events(
    events,
    stop_event,
    chat_state,
    state: dict,
    state_lock: threading.Lock,
    ui: ConsoleUI | None = None,
):
    """Print discovery, chat, and file transfer notifications while keeping prompt intact."""
    while not stop_event.is_set():
        try:
            event_type, data = events.get(timeout=0.2)
        except Empty:
            continue

        if event_type == "online":
            _print_async(
                f"{YELLOW}[*] {data['name']} ({data['ip']}:{data['tcp_port']}) is online{RESET}",
                state,
                state_lock,
                ui,
            )
        elif event_type == "offline":
            peer_id = _make_peer_id(data)
            with state_lock:
                was_partner = state["partner_id"] == peer_id
                if was_partner:
                    state["partner_id"] = None
                    state["partner_name"] = None
                    if chat_state:
                        chat_state.set_current_partner(None)
            msg = f"{YELLOW}[*] {data['name']} is offline{RESET}"
            if was_partner:
                msg += f"\n{YELLOW}[*] Chat ended because {data['name']} went offline.{RESET}"
            _print_async(msg, state, state_lock, ui)

        elif event_type == "status_changed":
            _print_async(
                f"{YELLOW}[*] {data['name']} is now {data['status']}{RESET}",
                state,
                state_lock,
                ui,
            )
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
                if chat_state and peer_id is not None:
                    chat_state.mark_as_read(peer_id)
                _print_async(
                    _format_chat_line(sender_name, text, is_self=False),
                    state,
                    state_lock,
                    ui,
                )
            else:
                unread = (
                    chat_state.get_unread_count(peer_id)
                    if (chat_state and peer_id is not None)
                    else 1
                )
                _print_async(
                    f"{YELLOW}[*] New message from {BOLD}{sender_name}{RESET}{YELLOW} "
                    f"({unread} unread). Type /chat {sender_name} to open.{RESET}",
                    state,
                    state_lock,
                    ui,
                )
        elif event_type in ("leave", "peer_left", "bye", "disconnected", "chat_closed"):
            peer_id, sender_name = _extract_event_peer_info(data)
            with state_lock:
                was_partner = peer_id is not None and state["partner_id"] == peer_id
                if was_partner:
                    state["partner_id"] = None
                    state["partner_name"] = None
                    if chat_state:
                        chat_state.set_current_partner(None)
            if was_partner:
                _print_async(
                    f"{YELLOW}[*] {sender_name} left the chat.{RESET}",
                    state,
                    state_lock,
                    ui,
                )
            else:
                _print_async(
                    f"{YELLOW}[*] {sender_name} closed the chat.{RESET}",
                    state,
                    state_lock,
                    ui,
                )
        elif event_type == "file_progress" and isinstance(data, dict):
            filename = data.get("filename", "unknown")
            percent = int(data.get("percent", 0))
            peer_name = data.get("peer_name") or "peer"
            transfer_id = f"{peer_name}:{filename}"
            if ui is not None:
                with state_lock:
                    partner_name = state["partner_name"]
                colored_prompt, _ = _format_prompt(partner_name)
                ui.set_prompt(colored_prompt)
                ui.show_progress(transfer_id, filename, percent, peer_name=peer_name)
            else:
                _print_async(
                    f"{CYAN}[*] File '{filename}' ({peer_name}): {percent}%{RESET}",
                    state,
                    state_lock,
                )
        elif event_type == "file_sent" and isinstance(data, dict):
            filename = data.get("filename", "unknown")
            size = int(data.get("size", 0))
            peer_name = data.get("peer_name") or "peer"
            _print_async(
                f"{GREEN}[*] Sent file '{filename}' ({_format_size(size)}) to {peer_name}.{RESET}",
                state,
                state_lock,
                ui,
            )
        elif event_type == "file_received" and isinstance(data, dict):
            filename = data.get("filename", "unknown")
            size = int(data.get("size", 0))
            sender = data.get("sender_name") or "peer"
            saved_path = data.get("saved_path") or f"downloads/{filename}"
            _print_async(
                f"{GREEN}[*] Received file '{filename}' ({_format_size(size)}) "
                f"from {sender} -> saved to {saved_path}{RESET}",
                state,
                state_lock,
                ui,
            )
        elif event_type == "file_error" and isinstance(data, dict):
            filename = data.get("filename", "unknown")
            error = data.get("error", "Unknown error")
            _print_async(
                f"{RED}[!] File transfer error ({filename}): {error}{RESET}",
                state,
                state_lock,
                ui,
            )


def run_cli(
    registry,
    discovery,
    events,
    tcp_manager=None,
    chat_state=None,
    file_sender=None,
    sender_name: str = "",
):
    """Handle M4 CLI commands using registry, discovery, TCP manager, chat state, and file transfer."""
    state = {"partner_id": None, "partner_name": None}
    state_lock = threading.Lock()
    ui = ConsoleUI()
    set_default_ui(ui)

    stop_events = threading.Event()
    event_thread = threading.Thread(
        target=_show_events,
        args=(events, stop_events, chat_state, state, state_lock, ui),
        daemon=True,
    )
    event_thread.start()

    try:
        with ui.stdout_context():
            ui.show_line(
                f"{BOLD}LAN Chat is running.{RESET} Type {CYAN}/help{RESET} to see commands."
            )
            while True:
                with state_lock:
                    partner_name = state["partner_name"]
                colored_prompt, plain_prompt = _format_prompt(partner_name)
                ui.set_prompt(colored_prompt)

                try:
                    raw_input = ui.prompt_line(colored_prompt)
                except (EOFError, KeyboardInterrupt):
                    ui.show_line("\nExiting...")
                    break

                line = raw_input.strip()
                if not line:
                    continue

                if line == "/list":
                    peers = _get_sorted_peers(registry)
                    if not peers:
                        ui.show_line("No other peers discovered.")
                    else:
                        for number, peer in enumerate(peers, start=1):
                            peer_id = _make_peer_id(peer)
                            unread = (
                                chat_state.get_unread_count(peer_id)
                                if chat_state
                                else 0
                            )
                            unread_tag = (
                                f" {YELLOW}({unread} unread){RESET}"
                                if unread > 0
                                else ""
                            )
                            status_color = (
                                GREEN if peer["status"] == "online" else YELLOW
                            )
                            ui.show_line(
                                f"  {BOLD}{number}.{RESET} {peer['name']} "
                                f"{GRAY}({peer['ip']}:{peer['tcp_port']}){RESET} "
                                f"{status_color}{peer['status']}{RESET}{unread_tag}"
                            )

                elif line.startswith("/status"):
                    args = line.split()
                    if (
                        len(args) != 2
                        or args[0] != "/status"
                        or args[1] not in ("online", "away")
                    ):
                        ui.show_line("Usage: /status online | /status away")
                    else:
                        discovery.set_status(args[1])
                        ui.show_line(
                            f"Your status: {args[1]} (sent in the next HELLO)"
                        )

                elif line == "/chat" or line.startswith("/chat "):
                    target = line[5:].strip()
                    if not target:
                        ui.show_line("Usage: /chat <name|number>")
                        continue

                    peers = _get_sorted_peers(registry)
                    peer, error = _resolve_peer(target, peers)
                    if error:
                        ui.show_line(error)
                        continue

                    target_id = _make_peer_id(peer)
                    with state_lock:
                        old_partner_id = state["partner_id"]

                    if old_partner_id == target_id:
                        ui.show_line(f"Already chatting with {peer['name']}.")
                        continue

                    if tcp_manager:
                        try:
                            tcp_manager.connect_peer(peer)
                        except Exception as exc:
                            ui.show_line(f"Failed to connect to {peer['name']}: {exc}")
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

                    ui.show_line(
                        f"\n{CYAN}=== Chatting with {BOLD}{peer['name']}{RESET}{CYAN} "
                        f"({peer['ip']}:{peer['tcp_port']}) [Type /leave to exit] ==={RESET}"
                    )
                    _print_history(history, peer["name"], ui=ui)

                elif line == "/send" or line.startswith("/send "):
                    file_path = line[5:].strip()
                    if (
                        len(file_path) >= 2
                        and file_path[0] == file_path[-1]
                        and file_path[0] in ('"', "'")
                    ):
                        file_path = file_path[1:-1]

                    if not file_path:
                        ui.show_line("Usage: /send <file_path>")
                        continue

                    current_partner = (
                        chat_state.get_current_partner()
                        if chat_state
                        else state["partner_id"]
                    )
                    if current_partner is None:
                        ui.show_line(
                            f"{YELLOW}No active chat. Use /list and /chat <name|number> before sending a file.{RESET}"
                        )
                        continue

                    if file_sender is None:
                        ui.show_line(
                            f"{YELLOW}File transfer module is not available.{RESET}"
                        )
                        continue

                    try:
                        file_sender(current_partner, file_path)
                    except Exception as exc:
                        ui.show_line(f"{RED}[!] Failed to send file: {exc}{RESET}")

                elif line == "/leave":
                    with state_lock:
                        current_id = state["partner_id"]
                        current_name = state["partner_name"]

                    if current_id is None:
                        ui.show_line("You are not in an active chat session.")
                        continue

                    if tcp_manager:
                        try:
                            tcp_manager.leave_chat(current_id)
                        except Exception as exc:
                            ui.show_line(f"Warning while leaving chat: {exc}")

                    with state_lock:
                        state["partner_id"] = None
                        state["partner_name"] = None

                    if chat_state:
                        chat_state.set_current_partner(None)

                    ui.show_line(f"{YELLOW}Left chat with {current_name}.{RESET}")

                elif line == "/help":
                    ui.show_line(HELP)

                elif line == "/quit":
                    ui.show_line("Exiting...")
                    break

                elif line.startswith("/"):
                    ui.show_line(
                        "Unknown command. Type /help to see available commands."
                    )

                else:
                    with state_lock:
                        current_id = state["partner_id"]
                        current_name = state["partner_name"]

                    if current_id is None:
                        ui.show_line(
                            "No active chat. Use /list and /chat <name|number> first."
                        )
                        continue

                    if tcp_manager:
                        try:
                            tcp_manager.send_message(current_id, line)
                        except Exception as exc:
                            ui.show_line(
                                f"Failed to send message to {current_name}: {exc}"
                            )
                            continue

                    if chat_state:
                        chat_state.add_message(
                            current_id, {"sender": "You", "text": line}
                        )

                    # Xóa dòng thô vừa gõ (nếu ngắn <= 5 dòng màn hình) để tránh lặp chữ
                    cols = shutil.get_terminal_size((80, 24)).columns
                    rows = max(
                        1, (len(plain_prompt) + len(raw_input) + cols - 1) // cols
                    )
                    if rows <= 5:
                        sys.stdout.write("\033[1A\033[2K" * rows + "\r")
                        sys.stdout.flush()

                    ui.show_line(_format_chat_line("You", line, is_self=True))

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
