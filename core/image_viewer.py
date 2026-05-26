import os
from PIL import Image
from textual.widgets import Static
from textual.app import ComposeResult
from rich.text import Text
import native

from core.window import Window


class ImageViewer(Window):
    DEFAULT_CSS = """
    ImageViewer Static {
        border: none;
        height: 100%;
        width: 100%;
        overflow: hidden;
    }
    """

    def __init__(self, *args, **kwargs):
        super().__init__("Image Viewer", "🖼️")
        self.file_path = args[0] if args else None
        self.static_canvas = Static()
        self.pil_image = None

        if self.file_path:
            self.border_title = f"🖼️ Viewer - {os.path.basename(self.file_path)}"

    def compose(self) -> ComposeResult:
        yield self.static_canvas

    def on_mount(self) -> None:
        if self.file_path and os.path.exists(self.file_path):
            try:
                self.pil_image = Image.open(self.file_path).convert("RGB")
            except Exception:
                self.static_canvas.update("Error: Could not load image.")
        else:
            self.static_canvas.update("No image loaded.")

    def on_resize(self, event) -> None:
        self.render_image()

    def render_image(self) -> None:
        if not self.pil_image:
            return

        cols = self.content_size.width
        rows = self.content_size.height

        if cols <= 0 or rows <= 0:
            return

        # 1 character cell = 1 pixel wide, 2 pixels high
        target_width = cols
        target_height = rows * 2

        try:
            img_ratio = self.pil_image.width / self.pil_image.height
            win_ratio = target_width / target_height

            if img_ratio > win_ratio:
                w = target_width
                h = int(w / img_ratio)
            else:
                h = target_height
                w = int(h * img_ratio)

            w = max(1, w)
            h = max(1, h)

            resized_img = self.pil_image.resize((w, h), Image.Resampling.BILINEAR)
            rgb_bytes = resized_img.tobytes()

            engine = native.ImageEngine(w, h)
            ansi_str = engine.render_frame(rgb_bytes)

            self.static_canvas.update(Text.from_ansi(ansi_str))
        except Exception as e:
            self.static_canvas.update(f"Render error: {e}")