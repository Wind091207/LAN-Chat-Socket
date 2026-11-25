from __future__ import annotations

import os
import shutil
import sys
import threading
import time
from typing import Callable, Hashable

if os.name == "nt":
    os.system("")

try:
    from prompt_toolkit.application import Application
    from prompt_toolkit.application.current import get_app_or_none
    from prompt_toolkit.buffer import Buffer
    from prompt_toolkit.document import Document
    from prompt_toolkit.filters import Condition
    from prompt_toolkit.formatted_text import StyleAndTextTuples
    from prompt_toolkit.key_binding import KeyBindings
    from prompt_toolkit.layout.containers import (
        ConditionalContainer,
        HSplit,
        VSplit,
        Window,
    )
    from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
    from prompt_toolkit.layout.dimension import Dimension as D
    from prompt_toolkit.layout.layout import Layout
    from prompt_toolkit.layout.margins import ScrollbarMargin
    from prompt_toolkit.lexers import Lexer
    from prompt_toolkit.mouse_events import MouseEventType
    from prompt_toolkit.output import ColorDepth
    from prompt_toolkit.styles import Style
    from prompt_toolkit.widgets import TextArea

    HAS_PROMPT_TOOLKIT = True
except ImportError:
    Application = None
    get_app_or_none = None
    Buffer = None
    Document = None
    Condition = None
    StyleAndTextTuples = list
    KeyBindings = None
    ConditionalContainer = None
    HSplit = None
    VSplit = None
    Window = None
    BufferControl = None
    FormattedTextControl = None
    D = None
    Layout = None
    ScrollbarMargin = None
    Lexer = object
    MouseEventType = None
    ColorDepth = None
    Style = None
    TextArea = None
    HAS_PROMPT_TOOLKIT = False


COMPACT_BREAKPOINT = 76
_CURRENT_ROOM_SENTINEL = object()

TUI_STYLE = Style.from_dict(
    {
        "header": "bg:#111114 #e4e4e7",
        "header.menu": "bg:#1f1f26 #ffffff bold",
        "header.menu.open": "bg:#2563eb #ffffff bold",
        "header.brand": "bg:#ffffff #09090b bold",
        "header.user": "bg:#111114 #ffffff bold",
        "header.online": "bg:#111114 #22c55e bold",
        "header.away": "bg:#111114 #eab308 bold",
        "header.room": "bg:#111114 #ffffff bold",
        "header.sep": "bg:#111114 #52525b",
        "footer": "bg:#111114 #a1a1aa",
        "footer.key": "bg:#111114 #ffffff bold",
        "line.bright": "bg:#0a0a0c #d4d4d8",
        "line.bar": "bg:#111114 #3f3f46",
        "sidebar": "bg:#0a0a0c #ffffff",
        "sidebar.th": "bg:#111114 #ffffff bold",
        "sidebar.th.muted": "bg:#111114 #a1a1aa bold",
        "log-pane": "bg:#0a0a0c #ffffff",
        "log.header": "bg:#111114 #ffffff bold",
        "log.header.tag": "bg:#111114 #60a5fa bold",
        "log.header.readonly": "bg:#111114 #f97316 bold",
        "log.header.alert": "bg:#2563eb #ffffff bold",
        "input-pane": "bg:#111114 #ffffff",
        "input-prompt": "bg:#111114 #ffffff bold",
        "input-prompt.locked": "bg:#111114 #f97316 bold",
        "scrollbar.background": "bg:#111114",
        "scrollbar.button": "bg:#d4d4d8",
        "scrollbar.arrow": "bg:#111114 #ffffff bold",
        "peer.active": "bg:#2563eb #ffffff bold",
        "peer.active.sub": "bg:#2563eb #eff6ff",
        "peer.active.online": "bg:#2563eb #ffffff bold",
        "peer.active.away": "bg:#2563eb #fef08a bold",
        "peer.active.unread": "bg:#ffffff #1d4ed8 bold",
        "peer.normal": "bg:#0a0a0c #ffffff bold",
        "peer.sub": "bg:#0a0a0c #8e8ea0",
        "peer.online": "bg:#0a0a0c #22c55e bold",
        "peer.chatting": "bg:#0a0a0c #4ade80 bold",
        "peer.away": "bg:#0a0a0c #eab308 bold",
        "peer.unread": "bg:#2563eb #ffffff bold",
        "peer.sep": "bg:#0a0a0c #27272a",
        "peer.hint": "bg:#0a0a0c #a1a1aa",
        "ts": "#71717a",
        "tag.chat": "#60a5fa bold",
        "tag.sys": "#22c55e bold",
        "tag.join": "#22c55e bold",
        "tag.leave": "#f97316 bold",
        "tag.warn": "#eab308 bold",
        "tag.unread": "#f97316 bold",
        "tag.file": "#c084fc bold",
        "tag.err": "#ef4444 bold",
        "sender.you": "#ffffff bold",
        "sender.peer": "#4ade80 bold",
        "msg.text": "#ffffff",
        "msg.join": "#4ade80 bold",
        "msg.leave": "#fb923c bold",
        "msg.muted": "#a1a1aa",
        "msg.accent": "#93c5fd bold",
        "msg.err": "#fca5a5",
        "bar.fill": "#ffffff bold",
        "bar.done": "#22c55e bold",
        "bar.empty": "#3f3f46",
    }
)


def get_terminal_size_safe() -> tuple[int, int]:
    if get_app_or_none is not None:
        app = get_app_or_none()
        if app is not None and app.output is not None:
            try:
                sz = app.output.get_size()
                if sz.rows > 0 and sz.columns > 0:
                    return (sz.rows, sz.columns)
            except Exception:
                pass
    sz = shutil.get_terminal_size((100, 30))
    return (max(1, sz.lines), max(1, sz.columns))


def compute_sidebar_width(total_cols: int | None = None) -> int:
    cols = total_cols if total_cols is not None else get_terminal_size_safe()[1]
    return min(34, max(25, int(cols * 0.28)))


class _FormattedLinesLexer(Lexer):
    def __init__(self, get_lines: Callable[[], list[StyleAndTextTuples]]):
        self._get_lines = get_lines

    def lex_document(self, document):
        lines = self._get_lines()

        def get_line(lineno: int):
            if 0 <= lineno < len(lines):
                return lines[lineno]
            return []

        return get_line


class _InteractiveLogControl(BufferControl):
    def __init__(
        self,
        buffer: Buffer,
        lexer: Lexer,
        on_wheel: Callable[[int], None],
        on_jump_ratio: Callable[[float], None],
        get_window: Callable[[], Window | None],
    ):
        super().__init__(buffer=buffer, lexer=lexer, focusable=False)
        self._on_wheel = on_wheel
        self._on_jump_ratio = on_jump_ratio
        self._get_window = get_window

    def mouse_handler(self, mouse_event):
        if mouse_event.event_type == MouseEventType.SCROLL_UP:
            self._on_wheel(-3)
            return None
        if mouse_event.event_type == MouseEventType.SCROLL_DOWN:
            self._on_wheel(3)
            return None

        if mouse_event.event_type in (MouseEventType.MOUSE_DOWN, MouseEventType.MOUSE_MOVE):
            win = self._get_window()
            info = getattr(win, "render_info", None) if win is not None else None
            if info is not None and info.window_height > 0:
                if mouse_event.position.x >= max(0, info.window_width - 3):
                    ratio = mouse_event.position.y / max(1, info.window_height - 1)
                    self._on_jump_ratio(max(0.0, min(1.0, ratio)))
                    return None
        return NotImplemented


class ChatTUI:
    def __init__(
        self,
        self_name: str,
        on_submit: Callable[[str], bool | None],
        get_peers_fragments: Callable[[int, bool], StyleAndTextTuples],
        get_peer_count: Callable[[], int],
    ):
        self._self_name = self_name or "Me"
        self._on_submit = on_submit
        self._get_peers_fragments = get_peers_fragments
        self._get_peer_count = get_peer_count

        self._lock = threading.Lock()
        self._current_room: Hashable = None
        self._rooms: dict[Hashable, list[StyleAndTextTuples]] = {None: []}
        self._room_auto_scroll: dict[Hashable, bool] = {None: True}
        self._room_top_line: dict[Hashable, int] = {None: 0}
        self._room_unseen: dict[Hashable, bool] = {None: False}

        self._partner_label = "Lobby (System Logs)"
        self._room_is_readonly = False
        self._status = "online"

        self._desktop_collapsed = False
        self._mobile_drawer_open = False
        self._last_dims = (0, 0)
        self._stop_watcher = threading.Event()

        self._log_buffer = Buffer(read_only=True)
        self._log_window: Window | None = None

        self._input_area = TextArea(
            height=1,
            prompt=[("class:input-prompt", " > ")],
            multiline=False,
            wrap_lines=False,
            style="class:input-pane",
            accept_handler=self._handle_accept,
        )

        self._app = self._build_application()

    @staticmethod
    def _split_fragments_to_lines(fragments: StyleAndTextTuples) -> list[StyleAndTextTuples]:
        lines: list[StyleAndTextTuples] = [[]]
        for item in fragments:
            style = item[0]
            text = item[1]
            parts = text.split("\n")
            for idx, part in enumerate(parts):
                if idx > 0:
                    lines.append([])
                if part:
                    lines[-1].append((style, part))
        return lines

    def has_room(self, room_key: Hashable) -> bool:
        with self._lock:
            return room_key in self._rooms

    def activate_room(
        self,
        room_key: Hashable,
        partner_label: str | None,
        initial_fragments_list: list[StyleAndTextTuples] | None = None,
        is_readonly: bool = False,
    ) -> None:
        with self._lock:
            if room_key not in self._rooms:
                seeded: list[StyleAndTextTuples] = []
                if initial_fragments_list:
                    for frags in initial_fragments_list:
                        seeded.extend(self._split_fragments_to_lines(frags))
                self._rooms[room_key] = seeded
                self._room_auto_scroll[room_key] = True
                self._room_top_line[room_key] = 0
                self._room_unseen[room_key] = False

            self._current_room = room_key
            self._room_auto_scroll[room_key] = True
            self._room_unseen[room_key] = False
            self._room_is_readonly = bool(room_key is not None and is_readonly)

            if partner_label:
                short_name = partner_label.split(" (")[0]
                if is_readonly:
                    self._partner_label = f"Viewing {partner_label}"
                    self._input_area.prompt = [
                        ("class:input-prompt.locked", f" [Read-Only: {short_name}] > ")
                    ]
                else:
                    self._partner_label = f"Chatting with {partner_label}"
                    self._input_area.prompt = [
                        ("class:input-prompt", f" You > {short_name} > ")
                    ]
            else:
                self._partner_label = "Lobby (System Logs)"
                self._input_area.prompt = [("class:input-prompt", " > ")]

        self._sync_buffer()

    def update_room_readonly(
        self, room_key: Hashable, partner_label: str, is_readonly: bool
    ) -> None:
        with self._lock:
            if self._current_room != room_key:
                return
            self._room_is_readonly = is_readonly
            short_name = partner_label.split(" (")[0]
            if is_readonly:
                self._partner_label = f"Viewing {partner_label}"
                self._input_area.prompt = [
                    ("class:input-prompt.locked", f" [Read-Only: {short_name}] > ")
                ]
            else:
                self._partner_label = f"Chatting with {partner_label}"
                self._input_area.prompt = [
                    ("class:input-prompt", f" You > {short_name} > ")
                ]
        self.invalidate()

    def _is_compact_mode(self) -> bool:
        _, cols = get_terminal_size_safe()
        return cols < COMPACT_BREAKPOINT

    def _show_desktop_sidebar(self) -> bool:
        return (not self._is_compact_mode()) and (not self._desktop_collapsed)

    def _show_mobile_drawer(self) -> bool:
        return self._is_compact_mode() and self._mobile_drawer_open

    def toggle_peers_panel(self) -> None:
        if self._is_compact_mode():
            self._mobile_drawer_open = not self._mobile_drawer_open
        else:
            self._desktop_collapsed = not self._desktop_collapsed
        self._force_full_redraw()

    def close_mobile_drawer(self) -> None:
        if self._mobile_drawer_open:
            self._mobile_drawer_open = False
            self._force_full_redraw()

    def _force_full_redraw(self) -> None:
        if self._app is not None and self._app.is_running:
            try:
                self._app.renderer.clear()
            except Exception:
                pass
            self._app.invalidate()

    def _build_application(self) -> Application:
        header = Window(
            content=FormattedTextControl(self._render_header),
            height=1,
            wrap_lines=False,
            dont_extend_height=True,
            style="class:header",
        )
        top_border = Window(
            height=1,
            char="─",
            dont_extend_height=True,
            style="class:line.bright",
        )

        drawer_list = Window(
            content=FormattedTextControl(
                lambda: self._get_peers_fragments(get_terminal_size_safe()[1], True)
            ),
            wrap_lines=False,
            height=lambda: min(max(4, (self._get_peer_count() + 1) * 3), 10),
            style="class:sidebar",
        )
        drawer_border = Window(
            height=1,
            char="─",
            dont_extend_height=True,
            style="class:line.bright",
        )
        mobile_drawer = ConditionalContainer(
            content=HSplit([drawer_list, drawer_border]),
            filter=Condition(self._show_mobile_drawer),
        )

        peer_th = Window(
            content=FormattedTextControl(self._render_peers_table_header),
            height=1,
            wrap_lines=False,
            dont_extend_height=True,
            style="class:sidebar.th",
        )
        peer_th_line = Window(
            height=1,
            char="─",
            dont_extend_height=True,
            style="class:line.bright",
        )
        peer_list = Window(
            content=FormattedTextControl(
                lambda: self._get_peers_fragments(compute_sidebar_width(), False)
            ),
            wrap_lines=False,
            height=D(min=1, weight=1),
            style="class:sidebar",
        )
        v_divider = Window(width=1, char="│", style="class:line.bright")

        desktop_sidebar = ConditionalContainer(
            content=VSplit(
                [
                    HSplit(
                        [peer_th, peer_th_line, peer_list],
                        width=lambda: compute_sidebar_width(),
                    ),
                    v_divider,
                ]
            ),
            filter=Condition(self._show_desktop_sidebar),
        )

        chat_th = Window(
            content=FormattedTextControl(self._render_chat_header),
            height=1,
            wrap_lines=False,
            dont_extend_height=True,
            style="class:log.header",
        )
        chat_th_line = Window(
            height=1,
            char="─",
            dont_extend_height=True,
            style="class:line.bright",
        )

        log_control = _InteractiveLogControl(
            buffer=self._log_buffer,
            lexer=_FormattedLinesLexer(self._snapshot_lines),
            on_wheel=self._scroll_by,
            on_jump_ratio=self._scroll_to_ratio,
            get_window=lambda: self._log_window,
        )
        self._log_window = Window(
            content=log_control,
            wrap_lines=True,
            height=D(min=1, weight=1),
            style="class:log-pane",
            right_margins=[ScrollbarMargin(display_arrows=True)],
            get_vertical_scroll=self._compute_vertical_scroll,
        )
        right_pane = HSplit([chat_th, chat_th_line, self._log_window])

        middle_split = VSplit(
            [desktop_sidebar, right_pane],
            height=D(min=2, weight=1),
        )

        input_top_border = Window(
            height=1,
            char="─",
            dont_extend_height=True,
            style="class:line.bright",
        )
        input_bottom_border = Window(
            height=1,
            char="─",
            dont_extend_height=True,
            style="class:line.bar",
        )
        footer = Window(
            content=FormattedTextControl(self._render_footer),
            height=1,
            wrap_lines=False,
            dont_extend_height=True,
            style="class:footer",
        )

        root = HSplit(
            [
                header,
                top_border,
                mobile_drawer,
                middle_split,
                input_top_border,
                self._input_area,
                input_bottom_border,
                footer,
            ]
        )

        kb = KeyBindings()

        @kb.add("c-c")
        @kb.add("c-q")
        def _exit_app(event):
            event.app.exit()

        @kb.add("c-b")
        def _toggle_sidebar(event):
            self.toggle_peers_panel()

        @kb.add("pageup")
        @kb.add("c-up")
        def _scroll_up(event):
            self._scroll_by(-10)

        @kb.add("pagedown")
        @kb.add("c-down")
        def _scroll_down(event):
            self._scroll_by(10)

        @kb.add("end")
        def _scroll_bottom(event):
            self.scroll_to_bottom()

        app_kwargs = {
            "layout": Layout(root, focused_element=self._input_area),
            "key_bindings": kb,
            "style": TUI_STYLE,
            "full_screen": True,
            "mouse_support": True,
            "before_render": self._on_before_render,
        }
        if ColorDepth is not None:
            app_kwargs["color_depth"] = ColorDepth.DEPTH_24_BIT

        return Application(**app_kwargs)

    def _on_before_render(self, app) -> None:
        try:
            sz = app.output.get_size()
            dims = (sz.rows, sz.columns)
        except Exception:
            return
        if dims[0] > 0 and dims[1] > 0 and dims != self._last_dims:
            self._last_dims = dims
            try:
                app.renderer.clear()
            except Exception:
                pass

    def _watch_terminal_size(self) -> None:
        while not self._stop_watcher.is_set():
            time.sleep(0.12)
            if self._app is None or not self._app.is_running:
                continue
            try:
                sz = self._app.output.get_size()
                dims = (sz.rows, sz.columns)
            except Exception:
                continue
            if dims[0] > 0 and dims[1] > 0 and dims != self._last_dims:
                self._last_dims = dims
                try:
                    self._app.renderer.clear()
                except Exception:
                    pass
                self._app.invalidate()

    def _snapshot_lines(self) -> list[StyleAndTextTuples]:
        with self._lock:
            return list(self._rooms.get(self._current_room, []))

    def _visible_height(self) -> int:
        info = getattr(self._log_window, "render_info", None)
        if info is not None and info.window_height > 0:
            return info.window_height
        rows, _ = get_terminal_size_safe()
        return max(3, rows - 7)

    def _compute_vertical_scroll(self, window: Window) -> int:
        info = getattr(window, "render_info", None)
        vis_h = info.window_height if (info is not None and info.window_height > 0) else self._visible_height()
        with self._lock:
            room = self._current_room
            lines = self._rooms.get(room, [])
            max_top = max(0, len(lines) - vis_h)
            if self._room_auto_scroll.get(room, True):
                self._room_top_line[room] = max_top
                self._room_unseen[room] = False
                return max_top
            top = max(0, min(self._room_top_line.get(room, 0), max_top))
            self._room_top_line[room] = top
            if top >= max_top:
                self._room_auto_scroll[room] = True
                self._room_unseen[room] = False
            return top

    def _sync_buffer(self) -> None:
        with self._lock:
            room = self._current_room
            lines = self._rooms.get(room, [])
            total = len(lines)
            plain_lines = ["".join(chunk[1] for chunk in line) for line in lines]
            full_text = "\n".join(plain_lines)
            visible_h = self._visible_height()
            max_top = max(0, total - visible_h)

            if self._room_auto_scroll.get(room, True):
                self._room_top_line[room] = max_top
                self._room_unseen[room] = False
                cursor_pos = len(full_text)
            else:
                top = max(0, min(self._room_top_line.get(room, 0), max_top))
                self._room_top_line[room] = top
                if top >= max_top:
                    self._room_auto_scroll[room] = True
                    self._room_unseen[room] = False
                    cursor_pos = len(full_text)
                else:
                    target_row = min(total - 1, top) if total > 0 else 0
                    doc_tmp = Document(full_text)
                    cursor_pos = doc_tmp.translate_row_col_to_index(target_row, 0)

        self._log_buffer.set_document(
            Document(full_text, cursor_position=cursor_pos),
            bypass_readonly=True,
        )
        self.invalidate()

    def _scroll_by(self, delta: int) -> None:
        with self._lock:
            room = self._current_room
            total = len(self._rooms.get(room, []))
            max_top = max(0, total - self._visible_height())
            new_top = max(0, min(max_top, self._room_top_line.get(room, 0) + delta))
            self._room_top_line[room] = new_top
            auto = new_top >= max_top
            self._room_auto_scroll[room] = auto
            if auto:
                self._room_unseen[room] = False
        self._sync_buffer()

    def _scroll_to_ratio(self, ratio: float) -> None:
        with self._lock:
            room = self._current_room
            total = len(self._rooms.get(room, []))
            max_top = max(0, total - self._visible_height())
            new_top = int(round(max_top * ratio))
            self._room_top_line[room] = new_top
            auto = new_top >= max_top
            self._room_auto_scroll[room] = auto
            if auto:
                self._room_unseen[room] = False
        self._sync_buffer()

    def scroll_to_bottom(self) -> None:
        with self._lock:
            room = self._current_room
            self._room_auto_scroll[room] = True
            self._room_unseen[room] = False
        self._sync_buffer()

    def _render_header(self) -> StyleAndTextTuples:
        _, cols = get_terminal_size_safe()
        peer_count = self._get_peer_count()
        with self._lock:
            status = self._status
            partner = self._partner_label

        def _on_menu_click(mouse_event):
            if MouseEventType is not None and mouse_event.event_type == MouseEventType.MOUSE_UP:
                self.toggle_peers_panel()
                return None
            return NotImplemented

        is_drawer_open = self._show_mobile_drawer()
        menu_style = "class:header.menu.open" if is_drawer_open else "class:header.menu"
        menu_label = f" [=] Peers ({peer_count}) " if cols < COMPACT_BREAKPOINT else " [=] "

        status_style = "class:header.online" if status == "online" else "class:header.away"
        status_label = " [ONLINE]" if status == "online" else " [AWAY]"

        if cols < COMPACT_BREAKPOINT:
            short_room = (
                partner.replace("Chatting with ", "")
                .replace("Viewing ", "")
                .split(" (")[0]
            )
            return [
                (menu_style, menu_label, _on_menu_click),
                ("class:header", " "),
                ("class:header.user", self._self_name),
                (status_style, status_label),
                ("class:header.sep", " | "),
                ("class:header.room", short_room),
            ]

        return [
            (menu_style, menu_label, _on_menu_click),
            ("class:header.brand", " LAN CHAT P2P "),
            ("class:header", "  User: "),
            ("class:header.user", self._self_name),
            (status_style, status_label),
            ("class:header.sep", "  |  "),
            ("class:header", "View: "),
            ("class:header.room", partner),
        ]

    def _render_peers_table_header(self) -> StyleAndTextTuples:
        w = compute_sidebar_width()
        count = self._get_peer_count()
        left = f" PEER ({count})"
        right = "STATUS "
        gap = max(1, w - len(left) - len(right))
        return [
            ("class:sidebar.th", left),
            ("class:sidebar.th", " " * gap),
            ("class:sidebar.th.muted", right),
        ]

    def _render_chat_header(self) -> StyleAndTextTuples:
        with self._lock:
            partner = self._partner_label
            is_readonly = self._room_is_readonly
            room = self._current_room
            unseen = self._room_unseen.get(room, False)

        tokens: StyleAndTextTuples = [
            ("class:log.header.tag", " # "),
            ("class:log.header", partner),
        ]
        if room is not None and is_readonly:
            short_name = partner.replace("Viewing ", "").split(" (")[0]
            tokens.append(
                (
                    "class:log.header.readonly",
                    f"  [READ-ONLY — Type /chat {short_name} to chat]",
                )
            )
        if unseen:
            tokens.append(("class:log.header.alert", "  New messages below (End) "))
        return tokens

    def _render_footer(self) -> StyleAndTextTuples:
        _, cols = get_terminal_size_safe()
        if cols < COMPACT_BREAKPOINT:
            return [
                ("class:footer.key", " [=]"),
                ("class:footer", ": Peers  "),
                ("class:footer.key", "/chat"),
                ("class:footer", "  "),
                ("class:footer.key", "/clear"),
                ("class:footer", "  "),
                ("class:footer.key", "/leave"),
                ("class:footer", "  "),
                ("class:footer.key", "Ctrl+Q"),
                ("class:footer", ": Quit"),
            ]
        return [
            ("class:footer.key", " Click Row"),
            ("class:footer", ": View History  "),
            ("class:footer.key", "/chat <name>"),
            ("class:footer", ": Join Chat  "),
            ("class:footer.key", "/clear"),
            ("class:footer", ": Clear History  "),
            ("class:footer.key", "/leave"),
            ("class:footer", ": Lobby  "),
            ("class:footer.key", "Ctrl+Q"),
            ("class:footer", ": Quit"),
        ]

    def _handle_accept(self, buff: Buffer) -> bool:
        text = buff.text
        self.scroll_to_bottom()
        should_exit = self._on_submit(text)
        if should_exit:
            self._app.exit()
        return False

    def set_partner(self, partner_label: str | None) -> None:
        if partner_label is None:
            self.activate_room(None, None)

    def set_status(self, status: str) -> None:
        with self._lock:
            self._status = status
        self.invalidate()

    def append_fragments(
        self,
        fragments: StyleAndTextTuples,
        room_key: Hashable = _CURRENT_ROOM_SENTINEL,
    ) -> None:
        lines = self._split_fragments_to_lines(fragments)
        need_sync = False

        with self._lock:
            target_room = (
                self._current_room
                if room_key is _CURRENT_ROOM_SENTINEL
                else room_key
            )
            if target_room not in self._rooms:
                self._rooms[target_room] = []
                self._room_auto_scroll[target_room] = True
                self._room_top_line[target_room] = 0
                self._room_unseen[target_room] = False

            room_lines = self._rooms[target_room]
            room_lines.extend(lines)
            if len(room_lines) > 1000:
                overflow = len(room_lines) - 1000
                self._rooms[target_room] = room_lines[overflow:]
                self._room_top_line[target_room] = max(
                    0, self._room_top_line.get(target_room, 0) - overflow
                )

            if not self._room_auto_scroll.get(target_room, True):
                self._room_unseen[target_room] = True

            if target_room == self._current_room:
                need_sync = True

        if need_sync:
            self._sync_buffer()
        else:
            self.invalidate()

    def clear_room_lines(
        self,
        room_key: Hashable = _CURRENT_ROOM_SENTINEL,
        banner_fragments: StyleAndTextTuples | None = None,
    ) -> None:
        need_sync = False
        with self._lock:
            target_room = (
                self._current_room
                if room_key is _CURRENT_ROOM_SENTINEL
                else room_key
            )
            if target_room not in self._rooms:
                return
            self._rooms[target_room] = (
                self._split_fragments_to_lines(banner_fragments)
                if banner_fragments
                else []
            )
            self._room_top_line[target_room] = 0
            self._room_auto_scroll[target_room] = True
            self._room_unseen[target_room] = False
            if target_room == self._current_room:
                need_sync = True

        if need_sync:
            self._sync_buffer()
        else:
            self.invalidate()

    def invalidate(self) -> None:
        if self._app is not None and self._app.is_running:
            self._app.invalidate()

    def run(self) -> None:
        watcher = threading.Thread(target=self._watch_terminal_size, daemon=True)
        watcher.start()
        try:
            self._app.run()
        finally:
            self._stop_watcher.set()


class ConsoleUI:
    def __init__(self, use_prompt_toolkit: bool | None = None):
        self._print_lock = threading.Lock()
        self._prompt_lock = threading.Lock()
        self._current_prompt = "> "

    @property
    def uses_prompt_toolkit(self) -> bool:
        return False

    def set_prompt(self, prompt_text: str) -> None:
        with self._prompt_lock:
            self._current_prompt = prompt_text

    def stdout_context(self):
        return _NullContext()

    def prompt_line(self, prompt_text: str) -> str:
        self.set_prompt(prompt_text)
        return input(prompt_text)

    def show_notification(self, message: str) -> None:
        with self._print_lock:
            with self._prompt_lock:
                prompt_text = self._current_prompt
            sys.stdout.write(f"\r\033[2K{message}\n{prompt_text}")
            sys.stdout.flush()

    def show_line(self, message: str) -> None:
        with self._print_lock:
            sys.stdout.write(f"{message}\n")
            sys.stdout.flush()

    def show_progress(
        self,
        transfer_id: str,
        filename: str,
        percent: int,
        peer_name: str | None = None,
    ) -> None:
        target = f" ({peer_name})" if peer_name else ""
        self.show_notification(f"[*] File '{filename}'{target}: {percent}%")

    def refresh_input(self) -> None:
        pass


class _NullContext:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False


_default_ui: ConsoleUI | None = None


def set_default_ui(ui) -> None:
    global _default_ui
    _default_ui = ui