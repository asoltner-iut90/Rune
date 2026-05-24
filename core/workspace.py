from textual.widget import Widget


class Workspace(Widget):
    DEFAULT_CSS = """
    Workspace {
        height: 100%;
        layout: horizontal;
        width: 1fr;
    }
    """