from __future__ import annotations

import os
import sys
import threading
import time
from datetime import datetime
from queue import Empty

from chat_state import build_default_storage_path
from console_ui import (
    HAS_PROMPT_TOOLKIT,
    ChatTUI,
    ConsoleUI,
    MouseEventType,
    StyleAndTextTuples,
    set_default_ui,
)

if os.name == "nt":
    os.system("")


def _make_peer_id(peer: dict) -> tuple[str, int]:
    return (peer["ip"], int(peer["tcp_port"]))


def _get_sorted_peers(registry) -> list[dict]:
    return sorted(
        registry.get_peers(),
        key=lambda p: (p["name"].casefold(), p["ip"], p["tcp_port"]),
    )


def _resolve_peer(target: str, peers: list[dict]) -> tuple[dict | None, str | None]:
    if not peers:
        return None, "No other peers discovered."

    if target.isdigit():
        index = int(target)
        if 1 <= index <= len(peers):
            return peers[index - 1], None
        return None, f"Invalid peer number: {target}. Use /list to check available numbers."

    matches = [p for p in peers if p["name"].casefold() == target.casefold()]
    if len(matches) == 1:
        return matches[0], None
    if len(matches) > 1:
        return None, f"Multiple peers named '{target}'. Use /chat <number>."
    return None, f"Peer '{target}' not found. Type /list to check peers."


def _extract_event_peer_info(data) -> tuple[tuple[str, int] | None, str]:
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


HELP_FRAGMENTS: StyleAndTextTuples = [
    ("class:msg.accent", " Commands:\n"),
    ("class:tag.chat", "   /list                 "),
    ("class:msg.text", "Show discovered peers and unread messages\n"),
    ("class:tag.chat", "   /status online|away   "),
    ("class:msg.text", "Set your presence status (or shorthand /online, /away)\n"),
    ("class:tag.chat", "   /chat <name|number>   "),
    ("class:msg.text", "Join/resume chat with a peer (unlocks messaging)\n"),
    ("class:tag.chat", "   /send <file>          "),
    ("class:msg.text", "Send a file to the active chat partner\n"),
    ("class:tag.chat", "   /clear                "),
    ("class:msg.text", "Clear current room's chat history on your device\n"),
    ("class:tag.chat", "   /leave                "),
    ("class:msg.text", "Leave active chat (jumps to Lobby; peer room becomes Read-Only)\n"),
    ("class:tag.chat", "   /help                 "),
    ("class:msg.text", "Show these commands\n"),
    ("class:tag.chat", "   /quit                 "),
    ("class:msg.text", "Exit the application\n"),
    ("class:tag.chat", "   <text>                "),
    ("class:msg.text", "Send a message (auto-switches AWAY -> ONLINE if needed)"),
]


def _now_str() -> str:
    return datetime.now().strftime("%H:%M:%S")


def _format_size(num_bytes: int) -> str:
    return f"{num_bytes:,} bytes"


def _format_chat_fragments(
    sender: str, text: str, is_self: bool, ts: str | None = None
) -> StyleAndTextTuples:
    time_str = f" [{ts or _now_str()}] "
    if is_self:
        return [
            ("class:ts", time_str),
            ("class:tag.chat", "[Chat] "),
            ("class:sender.you", "[You]: "),
            ("class:msg.text", text),
        ]
    return [
        ("class:ts", time_str),
        ("class:tag.chat", "[Chat] "),
        ("class:sender.peer", f"[{sender}]: "),
        ("class:msg.text", text),
    ]


def _format_join_log(message: str) -> StyleAndTextTuples:
    return [
        ("class:ts", f" [{_now_str()}] "),
        ("class:tag.join", "[System] "),
        ("class:msg.join", message),
    ]


def _format_leave_log(message: str) -> StyleAndTextTuples:
    return [
        ("class:ts", f" [{_now_str()}] "),
        ("class:tag.leave", "[System] "),
        ("class:msg.leave", message),
    ]


def _build_history_fragments(history, partner_name: str) -> list[StyleAndTextTuples]:
    if not history:
        return []
    result: list[StyleAndTextTuples] = [[("class:msg.muted", " --- Previous messages ---")]]
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
                datetime.fromtimestamp(raw_ts).strftime("%H:%M:%S")
                if isinstance(raw_ts, (int, float))
                else None
            )
            result.append(_format_chat_fragments(sender, content, is_self=is_self, ts=ts_str))
        else:
            result.append([("class:msg.text", f"   {item}")])
    result.append([("class:msg.muted", " -------------------------")])
    return result


def _render_peer_sidebar(
    registry,
    chat_state,
    state: dict,
    state_lock: threading.Lock,
    on_view_peer,
    on_view_lobby,
    width: int = 30,
    is_compact_drawer: bool = False,
    on_toggle_collapse=None,
) -> StyleAndTextTuples:
    peers = _get_sorted_peers(registry)
    with state_lock:
        viewed_id = state["viewed_room_id"]
        active_id = state["active_chat_id"]
        active_name = state["active_chat_name"]

    fragments: StyleAndTextTuples = []

    def _lobby_click(mouse_event):
        if MouseEventType is not None and mouse_event.event_type == MouseEventType.MOUSE_UP:
            on_view_lobby()
            return None
        return NotImplemented

    in_lobby_view = viewed_id is None
    lobby_style = "class:peer.active" if in_lobby_view else "class:peer.normal"
    lobby_sub = "class:peer.active.sub" if in_lobby_view else "class:peer.sub"
    lobby_title = " > Lobby (System Logs)" if in_lobby_view else " # Lobby (System Logs)"
    if len(lobby_title) > width - 1:
        lobby_title = lobby_title[: max(4, width - 2)] + "."
    fragments.append((lobby_style, lobby_title + " " * max(0, width - len(lobby_title)) + "\n", _lobby_click))

    sub_lobby = (
        f"   Active: {active_name}"
        if active_name
        else "   System events & logs"
    )
    if len(sub_lobby) > width - 1:
        sub_lobby = sub_lobby[: max(4, width - 2)] + "."
    fragments.append((lobby_sub, sub_lobby + " " * max(0, width - len(sub_lobby)) + "\n", _lobby_click))
    fragments.append(("class:peer.sep", "─" * max(1, width) + "\n"))

    if not peers:
        fragments.append(("class:peer.hint", "\n Scanning LAN for peers...\n"))
        fragments.append(("class:peer.sub", " Listening on UDP 9999"))
        return fragments

    for idx, peer in enumerate(peers, start=1):
        peer_id = _make_peer_id(peer)
        is_viewed = peer_id == viewed_id
        is_joined = peer_id == active_id
        is_online = peer["status"] == "online"
        unread = chat_state.get_unread_count(peer_id) if chat_state else 0
        peer_name = peer["name"]

        def _make_click_handler(target_peer_id: tuple[str, int], target_name: str):
            def _handler(mouse_event):
                if MouseEventType is not None and mouse_event.event_type == MouseEventType.MOUSE_UP:
                    on_view_peer(target_name, target_peer_id)
                    return None
                return NotImplemented

            return _handler

        click = _make_click_handler(peer_id, peer_name)

        if is_viewed:
            row_style = "class:peer.active"
            sub_style = "class:peer.active.sub"
            status_style = "class:peer.active.online" if is_online else "class:peer.active.away"
            badge_style = "class:peer.active.unread"
            icon = " > "
        else:
            row_style = "class:peer.normal"
            sub_style = "class:peer.sub"
            status_style = "class:peer.online" if is_online else "class:peer.away"
            badge_style = "class:peer.unread"
            icon = " * " if is_joined else (" + " if is_online else " - ")

        status_label = "ONLINE" if is_online else "AWAY"
        right_block = f"{status_label} "
        badge_str = f"+{unread}" if unread > 0 else ""
        badge_total_len = (1 + len(badge_str)) if unread > 0 else 0

        max_name_len = max(3, width - len(icon) - badge_total_len - len(right_block) - 1)
        shown_name = (
            peer_name
            if len(peer_name) <= max_name_len
            else peer_name[: max_name_len - 1] + "."
        )
        used_cols = len(icon) + len(shown_name) + badge_total_len + len(right_block)
        middle_gap = " " * max(1, width - used_cols)

        fragments.append((status_style, icon, click))
        fragments.append((row_style, shown_name, click))
        if unread > 0:
            fragments.append((row_style, " ", click))
            fragments.append((badge_style, badge_str, click))
        fragments.append((row_style, middle_gap, click))
        fragments.append((status_style, f"{right_block}\n", click))

        joined_tag = " (Joined)" if is_joined else ""
        sub_raw = f"   #{idx} {peer['ip']}:{peer['tcp_port']}{joined_tag}"
        if len(sub_raw) > width - 1:
            sub_raw = sub_raw[: max(4, width - 2)] + "."
        sub_pad = " " * max(0, width - len(sub_raw))
        fragments.append((sub_style, sub_raw + sub_pad + "\n", click))

        if idx < len(peers) or not is_compact_drawer:
            fragments.append(("class:peer.sep", "─" * max(1, width) + "\n"))

    if not is_compact_drawer and on_toggle_collapse is not None:
        def _collapse_click(mouse_event):
            if MouseEventType is not None and mouse_event.event_type == MouseEventType.MOUSE_UP:
                on_toggle_collapse()
                return None
            return NotImplemented

        fragments.append(("class:peer.hint", " << Collapse Sidebar", _collapse_click))

    return fragments


def _consume_events(
    events,
    stop_event: threading.Event,
    chat_state,
    state: dict,
    state_lock: threading.Lock,
    emit_fn,
    emit_room_fn,
    has_room_fn,
    on_room_locked,
    on_refresh,
):
    while not stop_event.is_set():
        try:
            event_type, data = events.get(timeout=0.2)
        except Empty:
            continue

        ts = f" [{_now_str()}] "

        if event_type == "online":
            peer_id = _make_peer_id(data)
            if chat_state and hasattr(chat_state, "set_peer_name"):
                chat_state.set_peer_name(peer_id, data["name"])
            emit_room_fn(
                None,
                [
                    ("class:ts", ts),
                    ("class:tag.sys", "[System] "),
                    ("class:msg.accent", data["name"]),
                    ("class:msg.text", f" ({data['ip']}:{data['tcp_port']}) is online"),
                ],
            )
            if chat_state:
                saved_unread = chat_state.get_unread_count(peer_id)
                if saved_unread > 0:
                    emit_room_fn(
                        None,
                        [
                            ("class:ts", ts),
                            ("class:tag.unread", "[Unread] "),
                            ("class:msg.accent", data["name"]),
                            (
                                "class:msg.text",
                                f" has {saved_unread} unread message(s) — click {data['name']} or type /chat {data['name']}",
                            ),
                        ],
                    )
            on_refresh()

        elif event_type == "offline":
            peer_id = _make_peer_id(data)
            peer_label = f"{data['name']} ({data['ip']}:{data['tcp_port']})"
            with state_lock:
                was_active = state["active_chat_id"] == peer_id
                if was_active:
                    state["active_chat_id"] = None
                    state["active_chat_name"] = None
                    if chat_state:
                        chat_state.set_current_partner(None)

            emit_room_fn(None, _format_leave_log(f"{data['name']} went offline."))
            if was_active:
                on_room_locked(peer_id, peer_label)
                if has_room_fn(peer_id):
                    emit_room_fn(
                        peer_id,
                        [
                            ("class:ts", ts),
                            ("class:tag.leave", "[Read-Only] "),
                            ("class:msg.leave", f"{data['name']} went offline. Chat is locked."),
                        ],
                    )
            on_refresh()

        elif event_type == "status_changed":
            peer_id, peer_name = _extract_event_peer_info(data)
            if peer_id is not None and chat_state and hasattr(chat_state, "set_peer_name"):
                chat_state.set_peer_name(peer_id, peer_name)
            new_st = str(data.get("status", "online"))
            st_style = "class:tag.join" if new_st == "online" else "class:tag.warn"
            status_line: StyleAndTextTuples = [
                ("class:ts", ts),
                ("class:tag.warn", "[System] "),
                ("class:msg.accent", peer_name),
                ("class:msg.text", " is now "),
                (st_style, new_st.upper()),
            ]
            emit_room_fn(None, status_line)
            if peer_id is not None and has_room_fn(peer_id):
                emit_room_fn(peer_id, status_line)
            on_refresh()

        elif event_type == "message":
            peer_id, sender_name = _extract_event_peer_info(data)
            if peer_id is not None and chat_state and hasattr(chat_state, "set_peer_name"):
                chat_state.set_peer_name(peer_id, sender_name)
            text = (
                data.get("text") or data.get("message") or data.get("content") or ""
                if isinstance(data, dict)
                else str(data)
            )
            with state_lock:
                active_id = state["active_chat_id"]
                viewed_id = state["viewed_room_id"]
                is_active_partner = peer_id is not None and active_id == peer_id
                is_viewing_sender = peer_id is not None and viewed_id == peer_id

            msg_frags = _format_chat_fragments(sender_name, text, is_self=False)

            if peer_id is not None and has_room_fn(peer_id):
                emit_room_fn(peer_id, msg_frags)

            if is_active_partner or is_viewing_sender:
                if chat_state and peer_id is not None:
                    chat_state.mark_as_read(peer_id)
            else:
                unread = (
                    chat_state.get_unread_count(peer_id)
                    if (chat_state and peer_id is not None)
                    else 1
                )
                emit_room_fn(
                    None,
                    [
                        ("class:ts", ts),
                        ("class:tag.unread", "[Unread] "),
                        ("class:msg.text", "New message from "),
                        ("class:msg.accent", sender_name),
                        ("class:msg.text", f" ({unread} unread) — type "),
                        ("class:tag.chat", f"/chat {sender_name}"),
                        ("class:msg.text", " to reply"),
                    ],
                )
            on_refresh()

        elif event_type in ("leave", "peer_left", "bye", "disconnected", "chat_closed"):
            peer_id, sender_name = _extract_event_peer_info(data)
            peer_label = (
                f"{sender_name} ({peer_id[0]}:{peer_id[1]})"
                if peer_id is not None
                else sender_name
            )
            emit_room_fn(None, _format_leave_log(f"{peer_label} left the chat."))

            if peer_id is not None and has_room_fn(peer_id):
                emit_room_fn(
                    peer_id,
                    [
                        ("class:ts", ts),
                        ("class:tag.leave", "[System] "),
                        ("class:msg.leave", f"{sender_name} left the chat."),
                    ],
                )
            on_refresh()

        elif event_type == "file_progress" and isinstance(data, dict):
            filename = data.get("filename", "unknown")
            percent = max(0, min(100, int(data.get("percent", 0))))
            peer_name = data.get("peer_name") or "peer"
            width = 16
            filled = int(round(width * percent / 100))
            fill_style = "class:bar.done" if percent >= 100 else "class:bar.fill"
            emit_fn(
                [
                    ("class:ts", ts),
                    ("class:tag.file", "[File] "),
                    ("class:msg.text", f"'{filename}' -> {peer_name}: ["),
                    (fill_style, "#" * filled),
                    ("class:bar.empty", "-" * (width - filled)),
                    ("class:msg.text", "] "),
                    ("class:msg.accent", f"{percent}%"),
                ]
            )

        elif event_type == "file_sent" and isinstance(data, dict):
            filename = data.get("filename", "unknown")
            size = int(data.get("size", 0))
            peer_name = data.get("peer_name") or "peer"
            emit_fn(
                [
                    ("class:ts", ts),
                    ("class:tag.file", "[File] "),
                    ("class:msg.text", "Sent '"),
                    ("class:msg.accent", filename),
                    ("class:msg.text", f"' ({_format_size(size)}) to {peer_name}."),
                ]
            )

        elif event_type == "file_received" and isinstance(data, dict):
            filename = data.get("filename", "unknown")
            size = int(data.get("size", 0))
            sender = data.get("sender_name") or "peer"
            saved_path = data.get("saved_path") or f"downloads/{filename}"
            peer_id, _ = _extract_event_peer_info(data)
            recv_line: StyleAndTextTuples = [
                ("class:ts", ts),
                ("class:tag.file", "[File] "),
                ("class:msg.text", "Received '"),
                ("class:msg.accent", filename),
                ("class:msg.text", f"' ({_format_size(size)}) from {sender} -> "),
                ("class:tag.sys", saved_path),
            ]
            if peer_id is not None and has_room_fn(peer_id):
                emit_room_fn(peer_id, recv_line)
            else:
                emit_fn(recv_line)

        elif event_type == "file_error" and isinstance(data, dict):
            filename = data.get("filename", "unknown")
            error = data.get("error", "Unknown error")
            emit_fn(
                [
                    ("class:ts", ts),
                    ("class:tag.err", "[Error] "),
                    ("class:msg.err", f"File transfer ({filename}): {error}"),
                ]
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
    state = {
        "viewed_room_id": None,
        "active_chat_id": None,
        "active_chat_name": None,
        "my_status": "online",
        "last_click_ts": 0.0,
    }
    state_lock = threading.Lock()
    local_name = sender_name or getattr(discovery, "name", "Me")
    local_port = getattr(discovery, "tcp_port", None)

    if chat_state is not None and hasattr(chat_state, "bind_storage"):
        chat_state.bind_storage(build_default_storage_path(local_name, local_port))

    use_tui = HAS_PROMPT_TOOLKIT and sys.stdin.isatty() and sys.stdout.isatty()
    tui: ChatTUI | None = None
    fallback_ui = ConsoleUI()
    set_default_ui(fallback_ui)

    def emit_fn(fragments: StyleAndTextTuples) -> None:
        if tui is not None:
            tui.append_fragments(fragments)
        else:
            plain = "".join(part[1] for part in fragments)
            fallback_ui.show_notification(plain)

    def emit_room_fn(room_key, fragments: StyleAndTextTuples) -> None:
        if tui is not None:
            tui.append_fragments(fragments, room_key=room_key)
        else:
            plain = "".join(part[1] for part in fragments)
            fallback_ui.show_notification(plain)

    def has_room_fn(room_key) -> bool:
        return tui.has_room(room_key) if tui is not None else False

    def on_room_locked(peer_id: tuple[str, int], peer_label: str) -> None:
        if tui is not None:
            tui.update_room_readonly(peer_id, peer_label, is_readonly=True)

    def on_refresh() -> None:
        if tui is not None:
            tui.invalidate()

    def apply_local_status(new_status: str, reason: str | None = None) -> None:
        with state_lock:
            changed = state["my_status"] != new_status
            state["my_status"] = new_status
            active_room = state["active_chat_id"]

        if not changed and reason is not None:
            return

        discovery.set_status(new_status)
        if tui is not None:
            tui.set_status(new_status)

        ts = f" [{_now_str()}] "
        st_style = "class:tag.join" if new_status == "online" else "class:tag.warn"
        msg_text = (
            reason
            if reason
            else f"Your status is now {new_status.upper()} (broadcasting via UDP HELLO)."
        )
        notice: StyleAndTextTuples = [
            ("class:ts", ts),
            (st_style, "[Status] "),
            ("class:msg.text", msg_text),
        ]
        emit_room_fn(None, notice)
        if active_room is not None and has_room_fn(active_room):
            emit_room_fn(active_room, notice)
    def view_lobby_manual() -> None:
        if tui is not None:
            tui.close_mobile_drawer()

        now_mono = time.monotonic()
        with state_lock:
            if state["viewed_room_id"] is None:
                return
            if now_mono - state["last_click_ts"] < 0.15:
                return
            state["last_click_ts"] = now_mono
            state["viewed_room_id"] = None
            still_active = state["active_chat_name"]

        if tui is not None:
            tui.activate_room(None, None, is_readonly=False)
            note = (
                f"Switched view to Lobby (still joined with {still_active} — type /leave to exit chat)."
                if still_active
                else "Switched view to Lobby (System Logs)."
            )
            emit_room_fn(
                None,
                [
                    ("class:ts", f" [{_now_str()}] "),
                    ("class:msg.muted", "[View] "),
                    ("class:msg.muted", note),
                ],
            )
            tui.invalidate()

    def view_peer_manual(target: str, expected_peer_id: tuple[str, int] | None = None) -> None:
        if tui is not None:
            tui.close_mobile_drawer()

        peers = _get_sorted_peers(registry)
        peer = None
        if expected_peer_id is not None:
            for item in peers:
                if _make_peer_id(item) == expected_peer_id:
                    peer = item
                    break
        if peer is None:
            peer, _ = _resolve_peer(target, peers)
        if peer is None:
            return

        target_id = _make_peer_id(peer)
        now_mono = time.monotonic()
        with state_lock:
            if state["viewed_room_id"] == target_id:
                return
            if now_mono - state["last_click_ts"] < 0.15:
                return
            state["last_click_ts"] = now_mono
            state["viewed_room_id"] = target_id
            is_joined = state["active_chat_id"] == target_id

        if chat_state:
            if hasattr(chat_state, "set_peer_name"):
                chat_state.set_peer_name(target_id, peer["name"])
            history = chat_state.get_history(target_id)
            chat_state.mark_as_read(target_id)
        else:
            history = []

        peer_label = f"{peer['name']} ({peer['ip']}:{peer['tcp_port']})"
        if tui is not None:
            seed_lines = _build_history_fragments(history, peer["name"])
            if not is_joined:
                seed_lines.append(
                    [
                        ("class:ts", f" [{_now_str()}] "),
                        ("class:tag.leave", "[Read-Only] "),
                        (
                            "class:msg.muted",
                            f"Viewing {peer['name']}'s room. Type /chat {peer['name']} to chat.",
                        ),
                    ]
                )
            tui.activate_room(
                target_id,
                peer_label,
                initial_fragments_list=seed_lines,
                is_readonly=not is_joined,
            )
            mode_str = "active chat" if is_joined else "read-only view"
            emit_room_fn(
                None,
                [
                    ("class:ts", f" [{_now_str()}] "),
                    ("class:msg.muted", "[View] "),
                    ("class:msg.muted", f"Opened {peer['name']}'s room ({mode_str})."),
                ],
            )
            tui.invalidate()

    def join_chat_with(target: str) -> None:
        if tui is not None:
            tui.close_mobile_drawer()

        ts = f" [{_now_str()}] "
        peers = _get_sorted_peers(registry)
        peer, error = _resolve_peer(target, peers)
        if error:
            emit_fn([("class:ts", ts), ("class:tag.warn", "[System] "), ("class:msg.text", error)])
            return

        target_id = _make_peer_id(peer)
        peer_label = f"{peer['name']} ({peer['ip']}:{peer['tcp_port']})"

        if chat_state and hasattr(chat_state, "set_peer_name"):
            chat_state.set_peer_name(target_id, peer["name"])

        with state_lock:
            already_joined = state["active_chat_id"] == target_id
            prev_active_id = state["active_chat_id"]
            prev_active_name = state["active_chat_name"]

        if already_joined:
            with state_lock:
                state["viewed_room_id"] = target_id
            if tui is not None:
                tui.activate_room(target_id, peer_label, is_readonly=False)
                tui.invalidate()
            return

        if prev_active_id is not None and prev_active_id != target_id:
            if tcp_manager:
                try:
                    tcp_manager.leave_chat(prev_active_id)
                except Exception:
                    pass
            emit_room_fn(None, _format_leave_log(f"Left chat with {prev_active_name}."))
            on_room_locked(prev_active_id, prev_active_name or "Peer")

        if tcp_manager:
            try:
                tcp_manager.connect_peer(peer)
            except Exception as exc:
                emit_fn(
                    [
                        ("class:ts", ts),
                        ("class:tag.err", "[Error] "),
                        ("class:msg.err", f"Failed to connect to {peer['name']}: {exc}"),
                    ]
                )
                return

        with state_lock:
            state["active_chat_id"] = target_id
            state["active_chat_name"] = peer["name"]
            state["viewed_room_id"] = target_id

        if chat_state:
            history = chat_state.get_history(target_id)
            chat_state.set_current_partner(target_id)
            chat_state.mark_as_read(target_id)
        else:
            history = []

        emit_room_fn(None, _format_join_log(f"Joined chat with {peer_label}."))

        if tui is not None:
            seed_lines = _build_history_fragments(history, peer["name"])
            tui.activate_room(
                target_id,
                peer_label,
                initial_fragments_list=seed_lines,
                is_readonly=False,
            )
            emit_room_fn(
                target_id,
                [
                    ("class:ts", ts),
                    ("class:tag.join", "[Joined] "),
                    ("class:msg.join", f"Connected to {peer_label} — Type /leave to exit"),
                ],
            )
            tui.invalidate()
        else:
            emit_fn(_format_join_log(f"Joined chat with {peer_label}."))

    def leave_active_chat() -> None:
        ts = f" [{_now_str()}] "
        with state_lock:
            current_id = state["active_chat_id"]
            current_name = state["active_chat_name"]

        if current_id is None:
            emit_fn(
                [
                    ("class:ts", ts),
                    ("class:tag.warn", "[System] "),
                    ("class:msg.text", "You are not in an active chat session."),
                ]
            )
            return

        if tcp_manager:
            try:
                tcp_manager.leave_chat(current_id)
            except Exception as exc:
                emit_room_fn(
                    None,
                    [
                        ("class:ts", ts),
                        ("class:tag.warn", "[System] "),
                        ("class:msg.text", f"Warning while leaving chat: {exc}"),
                    ],
                )

        peer_label = f"{current_name} ({current_id[0]}:{current_id[1]})"

        with state_lock:
            state["active_chat_id"] = None
            state["active_chat_name"] = None
            state["viewed_room_id"] = None

        if chat_state:
            chat_state.set_current_partner(None)

        if tui is not None:
            if tui.has_room(current_id):
                emit_room_fn(
                    current_id,
                    [
                        ("class:ts", ts),
                        ("class:tag.leave", "[Read-Only] "),
                        (
                            "class:msg.leave",
                            f"You left this chat. History is read-only — type /chat {current_name} to chat again.",
                        ),
                    ],
                )
            tui.activate_room(None, None, is_readonly=False)

        emit_room_fn(None, _format_leave_log(f"Left chat with {peer_label}."))
        on_refresh()

    def process_line(raw_input: str) -> bool:
        line = raw_input.strip()
        if not line:
            return False

        ts = f" [{_now_str()}] "

        if line == "/list":
            peers = _get_sorted_peers(registry)
            if not peers:
                emit_fn([("class:ts", ts), ("class:tag.warn", "[System] "), ("class:msg.text", "No other peers discovered.")])
            else:
                emit_fn([("class:ts", ts), ("class:tag.chat", "[Peers] "), ("class:msg.text", "Discovered peers:")])
                with state_lock:
                    active_id = state["active_chat_id"]
                for number, peer in enumerate(peers, start=1):
                    peer_id = _make_peer_id(peer)
                    unread = chat_state.get_unread_count(peer_id) if chat_state else 0
                    status_style = "class:peer.online" if peer["status"] == "online" else "class:peer.away"
                    row: StyleAndTextTuples = [
                        ("class:msg.accent", f"   {number}. "),
                        ("class:msg.text", f"{peer['name']} "),
                        ("class:ts", f"({peer['ip']}:{peer['tcp_port']}) "),
                        (status_style, peer["status"]),
                    ]
                    if peer_id == active_id:
                        row.append(("class:tag.join", " [JOINED]"))
                    if unread > 0:
                        row.append(("class:tag.unread", f" (+{unread})"))
                    emit_fn(row)
            return False

        if line in ("/away", "/online"):
            apply_local_status(line[1:])
            return False

        if line.startswith("/status"):
            args = line.split()
            if len(args) != 2 or args[0] != "/status" or args[1] not in ("online", "away"):
                emit_fn([("class:ts", ts), ("class:tag.warn", "[System] "), ("class:msg.text", "Usage: /status online | /status away")])
            else:
                apply_local_status(args[1])
            return False

        if line == "/chat" or line.startswith("/chat "):
            target = line[5:].strip()
            if not target:
                emit_fn([("class:ts", ts), ("class:tag.warn", "[System] "), ("class:msg.text", "Usage: /chat <name|number>")])
                return False
            join_chat_with(target)
            return False

        if line == "/clear":
            with state_lock:
                target_id = state["viewed_room_id"] or state["active_chat_id"]
                viewed_id = state["viewed_room_id"]

            if target_id is None:
                emit_fn(
                    [
                        ("class:ts", ts),
                        ("class:tag.warn", "[System] "),
                        ("class:msg.text", "Open a peer room or join a chat first to clear its history."),
                    ]
                )
                return False

            if chat_state:
                chat_state.clear_history(target_id)

            banner: StyleAndTextTuples = [
                ("class:ts", ts),
                ("class:tag.warn", "[System] "),
                ("class:msg.muted", "Chat history cleared on this device."),
            ]
            if tui is not None:
                tui.clear_room_lines(target_id, banner)
            if viewed_id is None:
                emit_room_fn(None, banner)
            on_refresh()
            return False

        if line == "/send" or line.startswith("/send "):
            file_path = line[5:].strip()
            if (
                len(file_path) >= 2
                and file_path[0] == file_path[-1]
                and file_path[0] in ('"', "'")
            ):
                file_path = file_path[1:-1]

            if not file_path:
                emit_fn([("class:ts", ts), ("class:tag.warn", "[System] "), ("class:msg.text", "Usage: /send <file_path>")])
                return False

            with state_lock:
                current_partner = state["active_chat_id"]
                viewed_id = state["viewed_room_id"]

            if current_partner is None:
                hint = (
                    "This room is Read-Only. Type /chat <name> before sending files."
                    if viewed_id is not None
                    else "No active chat. Type /chat <name|number> first."
                )
                emit_fn([("class:ts", ts), ("class:tag.leave", "[Read-Only] "), ("class:msg.text", hint)])
                return False

            if file_sender is None:
                emit_fn([("class:ts", ts), ("class:tag.warn", "[System] "), ("class:msg.text", "File transfer module is not available.")])
                return False

            try:
                file_sender(current_partner, file_path)
            except Exception as exc:
                emit_fn([("class:ts", ts), ("class:tag.err", "[Error] "), ("class:msg.err", f"Failed to send file: {exc}")])
            return False

        if line == "/leave":
            leave_active_chat()
            return False

        if line == "/help":
            emit_fn(HELP_FRAGMENTS)
            return False

        if line == "/quit":
            emit_fn([("class:ts", ts), ("class:tag.warn", "[System] "), ("class:msg.text", "Exiting...")])
            return True

        if line.startswith("/"):
            emit_fn([("class:ts", ts), ("class:tag.warn", "[System] "), ("class:msg.text", "Unknown command. Type /help to see available commands.")])
            return False

        with state_lock:
            current_id = state["active_chat_id"]
            current_name = state["active_chat_name"]
            viewed_id = state["viewed_room_id"]
            was_away = state["my_status"] == "away"

        if current_id is None:
            if viewed_id is not None:
                viewed_peer_name = "<name>"
                for p in _get_sorted_peers(registry):
                    if _make_peer_id(p) == viewed_id:
                        viewed_peer_name = p["name"]
                        break
                emit_fn(
                    [
                        ("class:ts", ts),
                        ("class:tag.leave", "[Read-Only] "),
                        (
                            "class:msg.text",
                            f"Cannot send messages while left/read-only. Type /chat {viewed_peer_name} to resume chatting.",
                        ),
                    ]
                )
            else:
                emit_fn(
                    [
                        ("class:ts", ts),
                        ("class:tag.warn", "[System] "),
                        ("class:msg.text", "No active chat. Type /chat <name|number> to join a chat."),
                    ]
                )
            return False

        with state_lock:
            if state["viewed_room_id"] != current_id:
                state["viewed_room_id"] = current_id
                if tui is not None:
                    tui.activate_room(
                        current_id,
                        f"{current_name} ({current_id[0]}:{current_id[1]})",
                        is_readonly=False,
                    )

        if tcp_manager:
            try:
                tcp_manager.send_message(current_id, line)
            except Exception as first_exc:
                reconnected = False
                for p in _get_sorted_peers(registry):
                    if _make_peer_id(p) == current_id:
                        try:
                            tcp_manager.connect_peer(p)
                            tcp_manager.send_message(current_id, line)
                            reconnected = True
                        except Exception:
                            reconnected = False
                        break
                if not reconnected:
                    emit_room_fn(
                        current_id,
                        [("class:ts", ts), ("class:tag.err", "[Error] "), ("class:msg.err", f"Failed to send message to {current_name}: {first_exc}")],
                    )
                    return False

        if was_away:
            apply_local_status(
                "online",
                reason="You sent a message while Away — status automatically switched to ONLINE.",
            )

        if chat_state:
            chat_state.add_message(current_id, {"sender": "You", "text": line, "is_me": True})

        emit_room_fn(current_id, _format_chat_fragments("You", line, is_self=True))
        return False

    if use_tui:
        tui = ChatTUI(
            self_name=local_name,
            on_submit=process_line,
            get_peers_fragments=lambda w, compact: _render_peer_sidebar(
                registry,
                chat_state,
                state,
                state_lock,
                view_peer_manual,
                view_lobby_manual,
                width=w,
                is_compact_drawer=compact,
                on_toggle_collapse=lambda: tui.toggle_peers_panel() if tui else None,
            ),
            get_peer_count=lambda: len(registry.get_peers()),
        )

    stop_events = threading.Event()
    event_thread = threading.Thread(
        target=_consume_events,
        args=(
            events,
            stop_events,
            chat_state,
            state,
            state_lock,
            emit_fn,
            emit_room_fn,
            has_room_fn,
            on_room_locked,
            on_refresh,
        ),
        daemon=True,
    )
    event_thread.start()

    try:
        emit_room_fn(
            None,
            [
                ("class:ts", f" [{_now_str()}] "),
                ("class:tag.sys", "[System] "),
                ("class:msg.accent", "LAN Chat TUI ready. "),
                ("class:msg.text", "Use "),
                ("class:tag.chat", "/chat <name>"),
                ("class:msg.text", " to start chatting or click a peer to view history."),
            ],
        )
        if tui is not None:
            tui.run()
        else:
            while True:
                with state_lock:
                    partner_name = state["active_chat_name"]
                prompt = f"You > {partner_name}> " if partner_name else "> "
                try:
                    raw = fallback_ui.prompt_line(prompt)
                except (EOFError, KeyboardInterrupt):
                    break
                if process_line(raw):
                    break
    finally:
        with state_lock:
            active_id = state["active_chat_id"]
            state["active_chat_id"] = None
            state["active_chat_name"] = None

        if active_id is not None and tcp_manager:
            try:
                tcp_manager.leave_chat(active_id)
            except Exception:
                pass

        if chat_state:
            chat_state.set_current_partner(None)

        stop_events.set()
        event_thread.join(timeout=0.5)