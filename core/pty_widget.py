import os
import pty
import asyncio
import fcntl
import termios
import struct
import subprocess

from textual.strip import Strip
from rich.segment import Segment
from rich.style import Style
import native

from core.application import Application


class PTYWidget(Application):
    can_focus = True

    def __init__(self, command: list[str] = None):
        super().__init__("Terminal", "$")
        self.command = command or ["bash"]
        self.master_fd = None
        self.process = None
        self._terminal = None
        self._style_cache = {}
        self._loop = None  # keep a reference to the rendering loop

    def on_mount(self) -> None:
        rows = self.content_size.height or 24
        cols = self.content_size.width or 80

        self._terminal = native.TerminalEngine(cols, rows)

        self.master_fd, slave_fd = pty.openpty()
        self._set_pty_size(rows, cols)

        # Make the master_fd non-blocking for asyncio integration
        fl = fcntl.fcntl(self.master_fd, fcntl.F_GETFL)
        fcntl.fcntl(self.master_fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)

        self.process = subprocess.Popen(
            self.command,
            stdin=slave_fd, stdout=slave_fd, stderr=slave_fd,
            close_fds=True, start_new_session=True
        )
        os.close(slave_fd)

        # Use add_reader instead of a worker thread
        self._loop = asyncio.get_running_loop()
        self._loop.add_reader(self.master_fd, self._on_pty_read)

    def _on_pty_read(self) -> None:
        """Callback triggered when PTY has data available."""
        try:
            data = os.read(self.master_fd, 65536)
            if data:
                self._terminal.process(data)
                self.refresh()
            else:
                self.remove()
        except OSError:
            self.remove()

    def on_resize(self, event) -> None:
        if self.master_fd and self._terminal:
            rows = self.content_size.height
            cols = self.content_size.width

            if rows > 0 and cols > 0:
                self._terminal.resize(cols, rows)
                self._set_pty_size(rows, cols)
                self.refresh()

    async def on_unmount(self) -> None:
        await super().on_unmount()
        # Remove the reader from the event loop immediately
        if self.master_fd and self._loop:
            self._loop.remove_reader(self.master_fd)

        # Kill the process forcibly
        if self.process:
            self.process.kill()
            self.process.wait()

        # Close the file descriptor
        if self.master_fd:
            try:
                os.close(self.master_fd)
            except OSError:
                pass

    # ─── Input & Rendering (Unchanged) ───────────────────────────────────────

    def on_key(self, event) -> None:
        if not self.master_fd:
            return
        if event.key == "ctrl+n":
            return
        data = self._key_to_bytes(event.key)
        if data:
            event.stop()
            os.write(self.master_fd, data)

    def render_line(self, y: int) -> Strip:
        if not self._terminal:
            return Strip([Segment(" " * self.size.width)])

        optimized_segments = self._terminal.render_line(y, self.has_focus)
        segments = []
        style_cache = self._style_cache

        for text, (fg, bg, bold, italic, underline, inverse) in optimized_segments:
            style_key = (fg, bg, bold, italic, underline, inverse)
            style = style_cache.get(style_key)
            if style is None:
                style = Style(
                    color=fg, bgcolor=bg, bold=bold, italic=italic,
                    underline=underline, reverse=inverse
                )
                style_cache[style_key] = style
            segments.append(Segment(text, style))

        return Strip(segments)

    def _set_pty_size(self, rows: int, cols: int) -> None:
        try:
            fcntl.ioctl(self.master_fd, termios.TIOCSWINSZ, struct.pack("HHHH", rows, cols, 0, 0))
        except OSError:
            pass

    def _key_to_bytes(self, key: str) -> bytes | None:
        mapping = {
            "space": b" ", "enter": b"\r", "escape": b"\x1b", "tab": b"\t",
            "backspace": b"\x7f", "up": b"\x1b[A", "down": b"\x1b[B",
            "right": b"\x1b[C", "left": b"\x1b[D", "home": b"\x1b[H",
            "end": b"\x1b[F", "delete": b"\x1b[3~", "pageup": b"\x1b[5~",
            "pagedown": b"\x1b[6~",
        }

        if key in mapping:
            return mapping[key]
        if key.startswith("ctrl+"):
            c = key.split("+")[1].lower()
            if len(c) == 1:
                return bytes([ord(c) - 96])
        if len(key) == 1:
            return key.encode()
        return None
