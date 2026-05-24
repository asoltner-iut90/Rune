from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.binding import Binding

from core.application_manager import ApplicationManager
from core.pty_widget import PTYWidget
from core.workspace import Workspace

class Rune(App):

    DEFAULT_CSS = """
    Rune.zoom-active Application {
        display: none;
    }

    Rune.zoom-active Application.zoomed {
        display: block;
    }
    """

    BINDINGS = [
        Binding("ctrl+up", "navigate('up')", show=False),
        Binding("ctrl+down", "navigate('down')", show=False),
        Binding("ctrl+left", "navigate('left')", show=False),
        Binding("ctrl+right", "navigate('right')", show=False),
        Binding("ctrl+n", "add_new_window()", show=False),
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
                best_candidate = min(below, key=lambda w: w.region.y)

        if best_candidate:
            best_candidate.focus()

    def action_add_new_window(self):
        new = PTYWidget(command=["bash"])
        self.manager.add_application(new)
        new.focus()

    def action_toggle_zoom(self):
        focused = self.focused
        if not focused or not focused.can_focus:
            return

        if self.has_class("zoom-active"):
            self.remove_class("zoom-active")
            focused.remove_class("zoomed")
        else:
            self.add_class("zoom-active")
            focused.add_class("zoomed")



