from core.pty_widget import PTYWidget
from core.text_editor import TextEditor

APP_REGISTRY = [
    {
        "name": "Terminal",
        "icon": "$",
        "class": PTYWidget,
        "description": "Linux terminal emulator",
    },
    {
        "name": "Editor",
        "icon": "📝",
        "class": TextEditor,
        "description": "Powerful source code and text editor",
    }
]