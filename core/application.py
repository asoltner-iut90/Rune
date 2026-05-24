from textual.widget import Widget


class Application(Widget):

    DEFAULT_CSS = """
    Application {
        border: solid $accent;
        height: 1fr;
        width: 1fr;
    }
    Application:focus {
        border: solid $primary;
    }
    """

    def __init__(self, name:str, icon:str,):
        super().__init__(name=name)
        assert len(icon) == 1 , "Icon must be a single character"
        self.icon: str = icon
        self.border_title: str = f"{icon} {name}"

    async def on_unmount(self) -> None:
        if self.has_class("zoomed"):
            self.app.remove_class("zoom-active")
