use pyo3::prelude::*;
use vt100::Parser;

#[derive(Clone, PartialEq, Eq)]
struct InternalStyle {
    fg: vt100::Color,
    bg: vt100::Color,
    bold: bool,
    italic: bool,
    underline: bool,
    inverse: bool,
}

fn convert_style(s: InternalStyle) -> (Option<String>, Option<String>, bool, bool, bool, bool) {
    let fg_str = match s.fg {
        vt100::Color::Default => None,
        vt100::Color::Idx(i) => Some(format!("color({})", i)),
        vt100::Color::Rgb(r, g, b) => Some(format!("#{:02x}{:02x}{:02x}", r, g, b)),
    };

    let bg_str = match s.bg {
        vt100::Color::Default => None,
        vt100::Color::Idx(i) => Some(format!("color({})", i)),
        vt100::Color::Rgb(r, g, b) => Some(format!("#{:02x}{:02x}{:02x}", r, g, b)),
    };

    (fg_str, bg_str, s.bold, s.italic, s.underline, s.inverse)
}

#[pyclass]
struct TerminalEngine {
    parser: Parser,
    cols: u16,
    rows: u16,
}

#[pymethods]
impl TerminalEngine {
    #[new]
    fn new(cols: u16, rows: u16) -> Self {
        TerminalEngine {
            parser: Parser::new(rows, cols, 0),
            cols,
            rows,
        }
    }

    fn process(&mut self, bytes: &[u8]) {
        self.parser.process(bytes);
    }

    fn resize(&mut self, cols: u16, rows: u16) {
        self.parser = Parser::new(rows, cols, 0);
        self.cols = cols;
        self.rows = rows;
    }

    fn cursor_position(&self) -> (u16, u16) {
        self.parser.screen().cursor_position()
    }

    fn hide_cursor(&self) -> bool {
        self.parser.screen().hide_cursor()
    }

    fn render_line(&self, y: u16, has_focus: bool) -> PyResult<Vec<(String, (Option<String>, Option<String>, bool, bool, bool, bool))>> {
        let mut segments = Vec::new();
        let screen = self.parser.screen();

        if y >= self.rows {
            return Ok(segments);
        }

        let mut current_text = String::new();
        let mut current_style: Option<InternalStyle> = None;

        let (cursor_row, cursor_col) = screen.cursor_position();
        let hide_cursor = screen.hide_cursor();

        for x in 0..self.cols {
            let (cell_data, style) = if let Some(cell) = screen.cell(y, x) {
                let c = cell.contents();
                let data = if c.is_empty() { " " } else { c };

                let mut inverse = cell.inverse();
                if has_focus && !hide_cursor && cursor_row == y && cursor_col == x {
                    inverse = !inverse;
                }

                (data, InternalStyle {
                    fg: cell.fgcolor(),
                    bg: cell.bgcolor(),
                    bold: cell.bold(),
                    italic: cell.italic(),
                    underline: cell.underline(),
                    inverse,
                })
            } else {
                let mut inverse = false;
                if has_focus && !hide_cursor && cursor_row == y && cursor_col == x {
                    inverse = true;
                }
                (" ", InternalStyle {
                    fg: vt100::Color::Default,
                    bg: vt100::Color::Default,
                    bold: false,
                    italic: false,
                    underline: false,
                    inverse,
                })
            };

            if current_style.is_none() {
                current_style = Some(style);
                current_text.push_str(cell_data);
            } else if Some(&style) == current_style.as_ref() {
                current_text.push_str(cell_data);
            } else {
                if let Some(s) = current_style {
                    segments.push((current_text, convert_style(s)));
                }
                current_style = Some(style);
                current_text = cell_data.to_string();
            }
        }

        if let Some(s) = current_style {
            segments.push((current_text, convert_style(s)));
        }

        Ok(segments)
    }
}

#[pymodule]
fn native(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<TerminalEngine>()?;
    Ok(())
}