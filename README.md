# Rune Desktop Environment

Rune is a lightweight, high-performance Text User Interface (TUI) Desktop Environment and window multiplexer built on top of the Textual framework. Designed to run completely within a Linux virtual console (TTY) or standard terminal emulators, Rune avoids unportable Unicode characters and graphical dependencies, offering a driving terminal-centric workspace.

## Features

- **Dynamic Window Management**: Multi-window horizontal workspace layout with robust focus handling, explicit layout navigation, and a global zoom mode (`Ctrl + Z`).
- **IPC-Driven Application Launching**: A built-in Unix socket server allows running and spawning applications inside the environment directly from external shell scripts or terminal windows.
- **Single-Instance Enforcement**: Prevents resource conflict by tracking instance state through an exclusive system file lock (`/tmp/rune.lock`).
- **TTY-Optimized Media Engines**: Includes specialized text, image, and music widgets designed to operate safely inside restricted-character consoles.

## Integrated Applications

- **Terminal Emulator (PTYWidget)**: A native-powered terminal wrapper connecting to a pseudo-terminal (PTY) system, exposing seamless shell interactions and injecting environment IPC capabilities.
- **Text Editor (TextEditor)**: Code and plain-text editor featuring dynamic syntax detection, real-time modification indicators, and interactive modal file management.
- **Image Viewer (ImageViewer)**: High-performance image render engine supporting static graphics and multi-frame animations through specialized rendering matrix caches.
- **Music Player (MusicPlayer)**: A headless audio execution interface harnessing mpv over custom Unix sockets, complete with an ASCII dot-matrix wave visualizer designed for raw TTY compliance.

## System Keybindings

| Keybinding | Action |
| :--- | :--- |
| `Ctrl + P` | Open / Toggle Application Search Launcher |
| `Ctrl + Z` | Toggle Zoom on Active Window |
| `Ctrl + W` | Close Active Window |
| `Ctrl + Up` | Navigate focus to the window above |
| `Ctrl + Down` | Navigate focus to the window below |
| `Ctrl + Left` | Navigate focus to the window on the left |
| `Ctrl + Right` | Navigate focus to the window on the right |

## Project Structure

```
├── bin/
│   └── rune                   # External IPC Python helper executable
├── core/
│   ├── application_launcher.py# Search overlay modal for system apps
│   ├── application_manager.py # Main registry and lifecycle supervisor
│   ├── image_viewer.py        # ASCII image pipeline
│   ├── music_player.py        # Audio front-end controlling MPV 
│   ├── pty_widget.py          # Terminal multiplexer backend
│   ├── registry.py            # Global application dictionary
│   ├── rune.py                # Main app class definition
│   ├── taskbar.py             # Lower status utility block and live clock
│   ├── text_editor.py         # Editing container with saving dialogs
│   ├── window.py              # Structural widget window layout base
│   └── workspace.py           # Core horizontal docking canvas
├── native/
│   ├── src/                   # Rust source files for optimized engines
│   ├── Cargo.toml             # Rust package configuration
│   └── pyproject.toml         # Maturin build system configuration
├── main.py                    # Main app entry point
├── requirements.txt           # Python package requirements
└── TODO.md                    # Future tasks list
```

## Inter-Process Communication (IPC)

Rune runs a continuous internal UNIX socket stream handler mapped to `/tmp/rune.sock`. The standalone companion script `rune` (located in `bin/`) acts as an external control layer. You can command the desktop environment from any external shell session or sub-terminal to open applications instantly.

### Usage Protocol

```bash
# General syntax (from the project root)
./bin/rune run <app_name> [args...]

# Launch a text file directly into Rune's editor from a shell
./bin/rune run editor /path/to/source.py

# Open an image or animated GIF in the image viewer
./bin/rune run viewer /path/to/image.png

# Queue a music file into the player interface
./bin/rune run player /path/to/track.mp3
```

> [!NOTE]
> Within a terminal instance spawned inside Rune, the `bin` directory is automatically prepended to the system `PATH`. You can therefore execute commands directly using `rune run ...` without specifying the path prefix.

## Installation & Compilation

### System Dependencies

To run Rune successfully inside a standard Linux installation or TTY console, you will need the following system tools:

- **Python 3.10+**
- **Rust Toolchain (`cargo`, `rustc`)**: Required to compile the native modules.
- **mpv**: System audio execution framework, must be available in the system path for the music player.

### Step 1: Install Python Requirements

Install the required Python modules using pip:

```bash
pip install -r requirements.txt
```

### Step 2: Compile the Native Extension

The native module uses **Maturin** to compile the Rust extension for Python. 

1. Install Maturin:
   ```bash
   pip install maturin
   ```

2. Compile and install the extension in your environment:
   ```bash
   # Build and install locally in development mode (optimized release version)
   cd native && maturin develop --release
   ```

### Step 3: Run the Application

Once the native module is built, launch the desktop environment from the root folder:

```bash
python main.py
```