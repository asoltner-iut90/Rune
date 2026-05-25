from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.binding import Binding
from textual import events
from core.application_manager import ApplicationManager
from core.pty_widget import PTYWidget
from core.window import Window
from core.workspace import Workspace
from core.application_launcher import ApplicationLauncher
from core.registry import APP_REGISTRY
import asyncio
import json
import os

class Rune(App):
    ENABLE_COMMAND_PALETTE = False
    SOCKET_PATH = "/tmp/rune.sock"
    DEFAULT_CSS = """
    Rune.zoom-active Window {
        display: none;
    }

    Rune.zoom-active Window.zoomed {
        display: block;
    }
    """

    BINDINGS = [
        Binding("ctrl+up", "navigate('up')", show=False),
        Binding("ctrl+down", "navigate('down')", show=False),
        Binding("ctrl+left", "navigate('left')", show=False),
        Binding("ctrl+right", "navigate('right')", show=False),
        Binding("ctrl+n", "add_new_window()", show=False),
        Binding("ctrl+p", "show_launcher()", show=False),
        Binding("ctrl+f11", "toggle_zoom()", show=False),
    ]

    def __init__(self):
        super().__init__()
        self.workspace = Workspace()
        self.manager = ApplicationManager(self.workspace)

    def compose(self) -> ComposeResult:
        yield Horizontal(
            self.workspace
        )

    def on_mount(self) -> None:
        if self.screen.focusable:
            self.screen.focusable[0].focus()
        self.run_worker(self._start_ipc_server())

    def action_navigate(self, direction: str) -> None:
        focused = self.focused
        if not focused or not focused.can_focus:
            return

        current_reg = focused.region
        focusable_widgets = [w for w in self.screen.query("*") if w.focusable]
        candidates = [w for w in focusable_widgets if w is not focused]
        best_candidate = None

        if direction == "right":
            right_side = [w for w in candidates if w.region.x >= current_reg.right]
            if right_side:
                best_candidate = min(right_side, key=lambda w: w.region.x)
        elif direction == "left":
            left_side = [w for w in candidates if w.region.right <= current_reg.x]
            if left_side:
                best_candidate = max(left_side, key=lambda w: w.region.right)
        elif direction == "up":
            above = [w for w in candidates if w.region.bottom <= current_reg.y]
            if above:
                best_candidate = max(above, key=lambda w: w.region.bottom)
        elif direction == "down":
            below = [w for w in candidates if w.region.y >= current_reg.bottom]
            if below:
                best_candidate = min(below, key=lambda w: w.region.bottom)

        if best_candidate:
            best_candidate.focus()

    def action_add_new_window(self):
        new = PTYWidget(command=["bash"])
        self.manager.add_application(new)
        new.focus()

    def action_show_launcher(self) -> None:
        def handle_selection(app_entry: dict | None) -> None:
            if app_entry:
                new_app = app_entry["class"]()
                self.manager.add_application(new_app)
                new_app.focus()

        self.push_screen(ApplicationLauncher(APP_REGISTRY), handle_selection)

    def action_toggle_zoom(self):
        focused = self.focused
        if not focused or not focused.can_focus:
            return

        if not isinstance(focused, Window):
            return

        if self.has_class("zoom-active"):
            self.remove_class("zoom-active")
            focused.remove_class("zoomed")
        else:
            self.add_class("zoom-active")
            focused.add_class("zoomed")

    async def _start_ipc_server(self) -> None:
        if os.path.exists(self.SOCKET_PATH):
            os.remove(self.SOCKET_PATH)

        self.ipc_server = await asyncio.start_unix_server(
            self._handle_ipc_client,
            path=self.SOCKET_PATH
        )
        async with self.ipc_server:
            await self.ipc_server.serve_forever()

    async def _handle_ipc_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        try:
            data = await reader.read(4096)
            if data:
                payload = json.loads(data.decode())
                if payload.get("action") == "open":
                    self.call_later(self._open_app_by_name, payload.get("app"))
        except Exception:
            pass
        finally:
            writer.close()
            await writer.wait_closed()

    def _open_app_by_name(self, name: str) -> None:
        for app in APP_REGISTRY:
            if app["name"].lower() == name.lower():
                new_app = app["class"]()
                self.manager.add_application(new_app)
                new_app.focus()
                break

    async def on_unmount(self) -> None:
        if os.path.exists(self.SOCKET_PATH):
            os.remove(self.SOCKET_PATH)