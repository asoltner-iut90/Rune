from textual.app import ComposeResult
from textual.containers import Vertical

from core.app_icon import AppIcon


class Sidebar(Vertical):
    DEFAULT_CSS = """
    Sidebar {
        width: 2;
        height: 100%;
        background: #1a1a2e;
        border-right: solid $accent;
        padding: 1 0;
    }
    """

    def compose(self) -> ComposeResult:
        yield AppIcon("$")
        yield AppIcon("~")
        yield AppIcon("≡")