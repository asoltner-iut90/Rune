from textual.widget import Widget


class AppIcon(Widget):
    can_focus = True
    DEFAULT_CSS = """
    AppIcon {
        width: 1;
        height: 1;
        margin-bottom: 1;
        color: $text;
        text-align: center;
    }
    AppIcon:focus {
        color: $accent;
        background: $primary;
    }
    """

    def __init__(self, icon: str):
        super().__init__()
        self.icon = icon

    def render(self) -> str:
        return self.icon
