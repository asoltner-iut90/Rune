import os
import cv2
import json
import asyncio
import time
from textual.widgets import Static
from textual.app import ComposeResult
from textual import events
from textual.strip import Strip
from rich.text import Text
import native

from core.window import Window


class VideoPlayer(Window):

    def __init__(self, *args, **kwargs):
        super().__init__("Watcher", "W")
        self.file_path = args[0] if args else None
        
        # Audio / Contrôle MPV
        self.mpv_process = None
        self.reader = None
        self.writer = None
        self.ipc_path = f"/tmp/rune_video_mpv_{os.getpid()}.sock"
        
        # OpenCV / Vidéo
        self.cap = None
        self.fps = 30.0
        self.is_paused = True
        self.current_time_pos = 0.0
        
        # Cache de rendu
        self.cached_strips = []
        self.needs_immediate_seek = False
        self.cap_lock = asyncio.Lock()
        
        if self.file_path:
            self.border_title = f"W Watcher - {os.path.basename(self.file_path)}"

    def compose(self) -> ComposeResult:
        return []

    async def on_mount(self) -> None:
        if not self.file_path or not os.path.exists(self.file_path):
            return
            
        self.cap = cv2.VideoCapture(self.file_path)
        if not self.cap.isOpened():
            return
        self.fps = self.cap.get(cv2.CAP_PROP_FPS) or 30.0
        
        try:
            self.mpv_process = await asyncio.create_subprocess_exec(
                "mpv", "--no-video", "--keep-open=yes", f"--input-ipc-server={self.ipc_path}", self.file_path,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL
            )
            
            for _ in range(20):
                if os.path.exists(self.ipc_path):
                    break
                await asyncio.sleep(0.1)
                
            self.reader, self.writer = await asyncio.open_unix_connection(self.ipc_path)
            
            await self._send_command(["observe_property", 1, "time-pos"])
            await self._send_command(["observe_property", 2, "pause"])
            
            self.run_worker(self._mpv_reader_loop())
            self.run_worker(self._video_render_loop())
        except Exception:
            pass

    async def _send_command(self, command_args: list) -> None:
        if not self.writer:
            return
        payload = {"command": command_args}
        try:
            self.writer.write((json.dumps(payload) + "\n").encode())
            await self.writer.drain()
        except (OSError, ConnectionError):
            self.writer = None
            self.reader = None

    async def _mpv_reader_loop(self) -> None:
        while self.reader and not self.reader.at_eof():
            try:
                line = await self.reader.readline()
                if not line:
                    break
                msg = json.loads(line.decode())
                if msg.get("event") == "property-change":
                    prop_name = msg.get("name")
                    prop_data = msg.get("data")
                    if prop_name == "time-pos" and prop_data is not None:
                        if abs(prop_data - self.current_time_pos) > 0.5:
                            self.needs_immediate_seek = True
                        self.current_time_pos = prop_data
                    elif prop_name == "pause" and prop_data is not None:
                        self.is_paused = prop_data
            except Exception:
                break

    async def _video_render_loop(self) -> None:
        frame_duration = 1.0 / self.fps
        last_displayed_frame = -1
        
        while self.cap and self.cap.isOpened():
            target_frame = int(self.current_time_pos * self.fps)
            
            if self.is_paused:
                # Si la vidéo est en pause, on fait le rendu instantané lors du seek
                if target_frame != last_displayed_frame:
                    async with self.cap_lock:
                        await asyncio.to_thread(self.cap.set, cv2.CAP_PROP_POS_FRAMES, target_frame)
                        ret, frame = await asyncio.to_thread(self.cap.read)
                    if ret:
                        strips = self._process_frame_to_strips(frame)
                        if strips:
                            self.cached_strips = strips
                            self.refresh()
                        last_displayed_frame = target_frame
                await asyncio.sleep(0.05)
                continue
                
            start_time = time.time()
            
            # Recalage si seek ou retard
            async with self.cap_lock:
                if self.needs_immediate_seek:
                    await asyncio.to_thread(self.cap.set, cv2.CAP_PROP_POS_FRAMES, target_frame)
                    self.needs_immediate_seek = False
                
                ret, frame = await asyncio.to_thread(self.cap.read)
            
            if ret:
                # Processer la frame en direct
                strips = self._process_frame_to_strips(frame)
                if strips:
                    self.cached_strips = strips
                    self.refresh()
                
            elapsed = time.time() - start_time
            sleep_time = max(0.002, frame_duration - elapsed)
            await asyncio.sleep(sleep_time)

    def _process_frame_to_strips(self, frame) -> list[Strip] | None:
        cols = self.content_size.width
        rows = self.content_size.height
        if cols <= 0 or rows <= 0:
            return None
            
        target_width = cols
        target_height = rows * 2
        
        h, w = frame.shape[:2]
        img_ratio = w / h
        win_ratio = target_width / target_height
        
        if img_ratio > win_ratio:
            rw = target_width
            rh = int(rw / img_ratio)
        else:
            rh = target_height
            rw = int(rh * img_ratio)
            
        rw = max(1, rw)
        rh = max(1, rh)
        
        resized = cv2.resize(frame, (rw, rh), interpolation=cv2.INTER_NEAREST)
        rgb_frame = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        rgb_bytes = rgb_frame.tobytes()
        
        engine = native.ImageEngine(rw, rh)
        ansi_frame = engine.render_frame(rgb_bytes)
        
        strips = []
        options = self.app.console.options.update(width=cols, no_wrap=True)
        for line in ansi_frame.splitlines():
            text = Text.from_ansi(line)
            rendered_lines = self.app.console.render_lines(text, options)
            if rendered_lines:
                strips.append(Strip(rendered_lines[0]))
            else:
                strips.append(Strip([]))
        return strips

    def render_line(self, y: int) -> Strip:
        if not self.cached_strips:
            return Strip([])
            
        offset_y = (self.content_size.height - len(self.cached_strips)) // 2
        img_y = y - offset_y
        
        if 0 <= img_y < len(self.cached_strips):
            return self.cached_strips[img_y]
                
        return Strip([])

    async def on_key(self, event: events.Key) -> None:
        if event.key == "space":
            event.stop()
            await self._send_command(["cycle", "pause"])
        elif event.key == "left":
            event.stop()
            await self._send_command(["seek", -5, "relative"])
        elif event.key == "right":
            event.stop()
            await self._send_command(["seek", 5, "relative"])

    async def on_unmount(self) -> None:
        if self.writer:
            try:
                self.writer.close()
                await self.writer.wait_closed()
            except Exception:
                pass
        if self.mpv_process:
            try:
                self.mpv_process.terminate()
                await self.mpv_process.wait()
            except Exception:
                pass
        async with self.cap_lock:
            if self.cap:
                self.cap.release()
        if os.path.exists(self.ipc_path):
            try:
                os.remove(self.ipc_path)
            except Exception:
                pass
