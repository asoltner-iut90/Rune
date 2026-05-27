use pyo3::prelude::*;
use std::fmt::Write;

#[pyclass]
pub struct ImageEngine {
    width: u16,
    height: u16,
}

#[pymethods]
impl ImageEngine {
    #[new]
    fn new(width: u16, height: u16) -> Self {
        Self { width, height }
    }

    fn render_frame(&self, buffer: &[u8]) -> PyResult<String> {
        let w = self.width as usize;
        let h = self.height as usize;
        
        // Pré-allocation large pour éviter les réallocations dynamiques
        let mut frame = String::with_capacity(w * h * 15);
        
        // Cache pour le Color Batching
        let mut last_fg: Option<(u8, u8, u8)> = None;
        let mut last_bg: Option<(u8, u8, u8)> = None;

        for y in (0..h).step_by(2) {
            for x in 0..w {
                let top_idx = (y * w + x) * 3;
                let bot_idx = ((y + 1) * w + x) * 3;

                if bot_idx + 2 >= buffer.len() {
                    break;
                }

                let fg = (buffer[bot_idx], buffer[bot_idx + 1], buffer[bot_idx + 2]);
                let bg = (buffer[top_idx], buffer[top_idx + 1], buffer[top_idx + 2]);

                // On n'écrit le code couleur que si la couleur a changé (Batching)
                if Some(fg) != last_fg {
                    let _ = write!(frame, "\x1b[38;2;{};{};{}m", fg.0, fg.1, fg.2);
                    last_fg = Some(fg);
                }
                if Some(bg) != last_bg {
                    let _ = write!(frame, "\x1b[48;2;{};{};{}m", bg.0, bg.1, bg.2);
                    last_bg = Some(bg);
                }
                frame.push('▄');
            }
            frame.push_str("\x1b[0m\n");
            // Réinitialisation du cache à chaque ligne
            last_fg = None;
            last_bg = None;
        }
        Ok(frame)
    }
}