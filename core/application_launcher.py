from textual.screen import ModalScreen
from textual.containers import Vertical
from textual.widgets import Input, OptionList
from textual.widgets.option_list import Option
from textual.app import ComposeResult
from textual.events import Key


class ApplicationLauncher(ModalScreen):
    DEFAULT_CSS = """
    ApplicationLauncher {
        align: center top;
        background: rgba(0, 0, 0, 0.5);
    }

    #launcher-box {
        width: 60;
        height: auto;
        max-height: 15;
        margin-top: 4;
        background: $surface;
        border: solid $primary;
        padding: 1;
    }

    #launcher-input {
        width: 100%;
        margin-bottom: 1;
    }

    #launcher-options {
        width: 100%;
        height: auto;
        max-height: 8;
        border: none;
    }
    """

    def __init__(self, apps_registry: list[dict]):
        super().__init__()
        self.registry = apps_registry
        self.filtered_apps = []

    def compose(self) -> ComposeResult:
        with Vertical(id="launcher-box"):
            yield Input(placeholder="Search application...", id="launcher-input")
            yield OptionList(id="launcher-options")

    def on_mount(self) -> None:
        self.query_one("#launcher-input", Input).focus()
        self.update_list("")

    def on_input_changed(self, event: Input.Changed) -> None:
        self.update_list(event.value)

    def update_list(self, query: str) -> None:
        options_list = self.query_one("#launcher-options", OptionList)
        options_list.clear_options()

        query = query.lower().strip()
        self.filtered_apps = []

        for app in self.registry:
            if not query or query in app["name"].lower() or query in app["description"].lower():
                self.filtered_apps.append(app)
                options_list.add_option(Option(f"{app['icon']} {app['name']} - {app['description']}"))

    def on_input_submitted(self, event: Input.Submitted) -> None:
        options_list = self.query_one("#launcher-options", OptionList)
        if options_list.option_count > 0:
            index = options_list.highlighted if options_list.highlighted is not None else 0
            if 0 <= index < len(self.filtered_apps):
                self.dismiss(self.filtered_apps[index])

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        if 0 <= event.index < len(self.filtered_apps):
            selected_app = self.filtered_apps[event.index]
            self.dismiss(selected_app)

    def on_key(self, event: Key) -> None:
        if event.key == "escape":
            self.dismiss(None)
        elif event.key in ("down", "up"):
            options_list = self.query_one("#launcher-options", OptionList)
            if event.key == "down":
                options_list.action_cursor_down()
            elif event.key == "up":
                options_list.action_cursor_up()
            event.stop()