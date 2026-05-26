import os
from textual.widgets import TextArea, Input
from textual.screen import ModalScreen
from textual.containers import Vertical
from textual.app import ComposeResult
from textual.binding import Binding
from core.window import Window


class SaveAsModal(ModalScreen):
    DEFAULT_CSS = """
    SaveAsModal {
        align: center middle;
        background: rgba(0, 0, 0, 0.5);
    }

    #save-box {
        width: 50;
        height: auto;
        background: $surface;
        border: solid $primary;
        padding: 1;
    }

    #save-input {
        width: 100%;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="save-box"):
            yield Input(placeholder="Enter file path to save...", id="save-input")

    def on_mount(self) -> None:
        self.query_one("#save-input", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        path = event.value.strip()
        if path:
            self.dismiss(path)
        else:
            self.dismiss(None)

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.dismiss(None)


class TextEditor(Window):
    BINDINGS = [
        Binding("ctrl+s", "save_file", "Save"),
    ]

    DEFAULT_CSS = """
    TextEditor TextArea, TextEditor TextArea:focus {
        border: none;
        height: 100%;
        width: 100%;
    }
    """

    def __init__(self, *args, **kwargs):
        super().__init__("Editor", "📝")
        self.file_path = args[0] if args else None
        self.text_area = TextArea(show_line_numbers=True)
        self._initial_load = True
        self._is_dirty = False
        self._update_title()

    def compose(self) -> ComposeResult:
        yield self.text_area

    def on_mount(self) -> None:
        if self.file_path and os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    self.text_area.load_text(f.read())
                self._detect_language()
            except Exception:
                pass
        self._initial_load = False
        self.text_area.focus()

    def on_text_area_changed(self, event: TextArea.Changed) -> None:
        if not self._initial_load:
            self._is_dirty = True
            self._update_title()

    def _update_title(self) -> None:
        base = os.path.basename(self.file_path) if self.file_path else "Untitled"
        indicator = " * " if self._is_dirty else ""
        self.border_title = f"📝 Editor - {base}{indicator}"

    def _detect_language(self) -> None:
        if not self.file_path:
            return
        _, ext = os.path.splitext(self.file_path)
        mapping = {
            ".py": "python",
            ".rs": "rust",
            ".json": "json",
            ".md": "markdown",
            ".toml": "toml",
            ".yaml": "yaml",
            ".sh": "bash",
        }
        lang = mapping.get(ext.lower())
        if lang:
            self.text_area.language = lang

    def action_save_file(self) -> None:
        if self.file_path:
            self._execute_save(self.file_path)
        else:
            def handle_path(path: str | None) -> None:
                if path:
                    self.file_path = path
                    self._detect_language()
                    self._execute_save(path)

            self.app.push_screen(SaveAsModal(), handle_path)

    def _execute_save(self, path: str) -> None:
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.text_area.text)
            self._is_dirty = False
            self._update_title()
        except OSError:
            pass