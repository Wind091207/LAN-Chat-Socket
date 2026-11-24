"""Thread-safe Console UI wrapper supporting prompt_toolkit input preservation."""

from __future__ import annotations

import sys
import threading

try:
    from prompt_toolkit import PromptSession
    from prompt_toolkit.formatted_text import ANSI
    from prompt_toolkit.patch_stdout import patch_stdout

    HAS_PROMPT_TOOLKIT = True
except ImportError:
    PromptSession = None
    ANSI = None
    patch_stdout = None
    HAS_PROMPT_TOOLKIT = False

RESET = "\033[0m"
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"


class ConsoleUI:
    """Synchronize terminal output and keep active user input intact across threads."""

    def __init__(self, use_prompt_toolkit: bool | None = None):
        self._print_lock = threading.Lock()
        self._prompt_lock = threading.Lock()
        self._current_prompt = "> "

        if use_prompt_toolkit is None:
            is_tty = sys.stdin.isatty() and sys.stdout.isatty()
            self._use_ptk = HAS_PROMPT_TOOLKIT and is_tty
        else:
            self._use_ptk = bool(use_prompt_toolkit and HAS_PROMPT_TOOLKIT)

        self._session = PromptSession() if self._use_ptk else None

    @property
    def uses_prompt_toolkit(self) -> bool:
        """Return True when prompt_toolkit PromptSession is active."""
        return self._use_ptk and self._session is not None

    def set_prompt(self, prompt_text: str) -> None:
        """Store the active prompt string for fallback redraws."""
        with self._prompt_lock:
            self._current_prompt = prompt_text

    def stdout_context(self):
        """Return patch_stdout context manager when prompt_toolkit is active."""
        if self.uses_prompt_toolkit and patch_stdout is not None:
            return patch_stdout(raw=True)
        return _NullContext()

    def prompt_line(self, prompt_text: str) -> str:
        """Read a line from the user without losing partial input on async prints."""
        self.set_prompt(prompt_text)
        if self.uses_prompt_toolkit and self._session is not None and ANSI is not None:
            return self._session.prompt(ANSI(prompt_text))
        return input(prompt_text)

    def show_notification(self, message: str) -> None:
        """Print an asynchronous notification above the active input prompt."""
        with self._print_lock:
            if self.uses_prompt_toolkit:
                sys.stdout.write(f"{message}\n")
                sys.stdout.flush()
            else:
                with self._prompt_lock:
                    prompt_text = self._current_prompt
                sys.stdout.write(f"\r\033[2K{message}\n{prompt_text}")
                sys.stdout.flush()

    def show_line(self, message: str) -> None:
        """Print a synchronous line under the print lock."""
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
        """Display a percentage progress update for a file transfer."""
        target = f" ({peer_name})" if peer_name else ""
        color = GREEN if percent >= 100 else CYAN
        self.show_notification(
            f"{color}[*] File '{filename}'{target}: {percent}%{RESET}"
        )

    def refresh_input(self) -> None:
        """Trigger a prompt_toolkit UI redraw if a session is running."""
        if self._session is None:
            return
        app = getattr(self._session, "app", None)
        if app is not None and getattr(app, "is_running", False):
            app.invalidate()


class _NullContext:
    """No-op context manager used when prompt_toolkit is unavailable."""

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False


_default_ui: ConsoleUI | None = None


def _get_default_ui() -> ConsoleUI:
    """Return or initialize the global ConsoleUI instance."""
    global _default_ui
    if _default_ui is None:
        _default_ui = ConsoleUI()
    return _default_ui


def set_default_ui(ui: ConsoleUI) -> None:
    """Register the active ConsoleUI instance."""
    global _default_ui
    _default_ui = ui


def show_notification(message: str) -> None:
    """Display an asynchronous notification via the active ConsoleUI."""
    _get_default_ui().show_notification(message)


def show_progress(
    transfer_id: str,
    filename: str,
    percent: int,
    peer_name: str | None = None,
) -> None:
    """Display a file transfer progress update via the active ConsoleUI."""
    _get_default_ui().show_progress(transfer_id, filename, percent, peer_name=peer_name)


def refresh_input() -> None:
    """Refresh the active input prompt via the active ConsoleUI."""
    _get_default_ui().refresh_input()