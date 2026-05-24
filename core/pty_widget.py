import os
import pty
import asyncio
import fcntl
import termios
import struct
import subprocess

from textual.widget import Widget
from textual.strip import Strip
from rich.segment import Segment
from rich.style import Style
import native  # Conservé selon ton code original


class PTYWidget(Widget):
    can_focus = True

    DEFAULT_CSS = """
    PTYWidget {
        border: solid $accent;
        height: 100%;
        width: 100%;
    }
    PTYWidget:focus {
        border: solid $primary;
    }
    """

    def __init__(self, command: list[str] = None, **kwargs):
        super().__init__(**kwargs)
        self.command = command or ["bash"]
        self.master_fd = None
        self.process = None
        self._terminal = None
        self._style_cache = {}
        self._loop = None  # On garde une référence à la boucle de rendering

    def on_mount(self) -> None:
        rows = self.content_size.height or 24
        cols = self.content_size.width or 80

        self._terminal = native.TerminalEngine(cols, rows)

        self.master_fd, slave_fd = pty.openpty()
        self._set_pty_size(rows, cols)

        # 1. Rendre le master_fd NON-BLOQUANT pour l'intégration avec asyncio
        fl = fcntl.fcntl(self.master_fd, fcntl.F_GETFL)
        fcntl.fcntl(self.master_fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)

        self.process = subprocess.Popen(
            self.command,
            stdin=slave_fd, stdout=slave_fd, stderr=slave_fd,
            close_fds=True, start_new_session=True
        )
        os.close(slave_fd)

        # 2. Utiliser add_reader plutôt qu'un worker de thread
        self._loop = asyncio.get_running_loop()
        self._loop.add_reader(self.master_fd, self._on_pty_read)

    def _on_pty_read(self) -> None:
        """Callback déclenché dès que le PTY a des données disponibles."""
        try:
            data = os.read(self.master_fd, 65536)
            if data:
                self._terminal.process(data)
                self.refresh()
        except OSError:
            # Le PTY a probablement été fermé, on ignore l'erreur de lecture
            pass

    def on_resize(self, event) -> None:
        if self.master_fd and self._terminal:
            rows = self.content_size.height
            cols = self.content_size.width

            if rows > 0 and cols > 0:
                self._terminal.resize(cols, rows)
                self._set_pty_size(rows, cols)
                self.refresh()

    async def on_unmount(self) -> None:
        # 1. On retire immédiatement le reader de la boucle d'événements
        if self.master_fd and self._loop:
            self._loop.remove_reader(self.master_fd)

        # 2. On tue brutalement le processus (SIGKILL) car bash ignore SIGTERM
        if self.process:
            self.process.kill()  # Nettoyage forcé
            self.process.wait()  # On attend qu'il devienne un zombie nettoyé

        # 3. On ferme le descripteur proprement
        if self.master_fd:
            try:
                os.close(self.master_fd)
            except OSError:
                pass

    # ─── Input & Rendu (Inchangés) ────────────────────────────────────────────

    def on_key(self, event) -> None:
        if not self.master_fd:
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