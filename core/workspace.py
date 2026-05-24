from textual.widget import Widget
from core.application import Application


class Workspace(Widget):
    DEFAULT_CSS = """
    Workspace {
        height: 1fr;
        layout: horizontal;
        width: 1fr;
    }
    """

    def __init__(self, *children):
        super().__init__(*children)

    def add_window(self, window: Application):
        self.mount(window)
