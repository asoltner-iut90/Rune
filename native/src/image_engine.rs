use pyo3::prelude::*;

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
        let mut frame = String::with_capacity((self.width as usize) * (self.height as usize) * 20);
        let w = self.width as usize;

        for y in (0..self.height as usize).step_by(2) {
            for x in 0..w {
                let top_idx = (y * w + x) * 3;
                let bot_idx = ((y + 1) * w + x) * 3;

                if bot_idx + 2 >= buffer.len() {
                    break;
                }

                frame.push_str(&format!(
                    "\x1b[38;2;{};{};{}m\x1b[48;2;{};{};{}m▄",
                    buffer[bot_idx], buffer[bot_idx + 1], buffer[bot_idx + 2],
                    buffer[top_idx], buffer[top_idx + 1], buffer[top_idx + 2]
                ));
            }
            frame.push_str("\x1b[0m\n");
        }
        Ok(frame)
    }
}