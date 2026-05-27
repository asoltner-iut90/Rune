from core.pty_widget import PTYWidget
from core.text_editor import TextEditor
from core.image_viewer import ImageViewer
from core.music_player import MusicPlayer
from core.video_player import VideoPlayer

APP_REGISTRY = [
    {
        "name": "Terminal",
        "icon": "$",
        "class": PTYWidget,
        "description": "Linux terminal emulator",
    },
    {
        "name": "Editor",
        "icon": "≡",
        "class": TextEditor,
        "description": "Powerful source code and text editor",
    },
    {
        "name": "Viewer",
        "icon": "#",
        "class": ImageViewer,
        "description": "High-performance image viewer",
    },
    {
        "name": "Player",
        "icon": ">",
        "class": MusicPlayer,
        "description": "Headless audio player via MPV",
    },
    {
        "name": "Watcher",
        "icon": "W",
        "class": VideoPlayer,
        "description": "High-performance ASCII video player",
    }
]