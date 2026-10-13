//! `yaml._rust`: PyO3 binding over [`yaml_scan_core`].
//!
//! The binding owns every Python-visible conversion and formatting
//! decision, so the core stays Python-free:
//!
//! - `str` <-> code points, lossless through lone surrogates via a single
//!   `surrogatepass` round-trip (`ValueError` past `0x10FFFF`, mirroring
//!   `chr()`);
//! - tokens as plain tuples (built once per pull by the scanner facade);
//! - errors as `_ScanFault`/`_UriFault` payloads carrying message
//!   *templates* plus typed args; the Python facade renders `%`
//!   formatting, so `%r` output is byte-identical to the original.
//!
//! The single `unsafe` site policy of earlier ports does not apply here:
//! this binding uses only safe PyO3 APIs.

use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::types::{PyBytes, PyString};
use yaml_scan_core::scan::{
    DirectiveValue, ScanCore, ScanFault, Token as ScanToken, UriDecodeFault,
};
use yaml_scan_core::{EngineError, ErrArg, Formatted, MarkPos};

pyo3::create_exception!(yaml_rust, ScanFaultExc, pyo3::exceptions::PyException);
pyo3::create_exception!(yaml_rust, UriFaultExc, pyo3::exceptions::PyException);

// ---------------------------------------------------------------------------
// Lossless str <-> code points.
// ---------------------------------------------------------------------------

/// Python `str` to code points. Fast path borrows valid text with no
/// Python call; lone surrogates (`to_str` fails) fall back to one
/// `surrogatepass` encode plus CESU-8 decode (pairs stay split, exactly
/// like the codec pair does).
fn str_to_u32s(s: &Bound<'_, PyString>) -> PyResult<Vec<u32>> {
    match s.to_str() {
        Ok(text) => Ok(text.chars().map(|c| c as u32).collect()),
        Err(_) => {
            let bytes: Bound<'_, PyBytes> =
                s.call_method("encode", ("utf-8", "surrogatepass"), None)?.extract()?;
            Ok(decode_cesu8(bytes.as_bytes()))
        }
    }
}

fn decode_cesu8(b: &[u8]) -> Vec<u32> {
    let mut out = Vec::with_capacity(b.len());
    let mut i = 0;
    while i < b.len() {
        let b0 = b[i] as u32;
        if b0 < 0x80 {
            out.push(b0);
            i += 1;
        } else if b0 < 0xC0 {
            // Unreachable on encoder output; stay total.
            out.push(0xFFFD);
            i += 1;
        } else if b0 < 0xE0 {
            if i + 1 < b.len() {
                out.push(((b0 & 0x1F) << 6) | (b[i + 1] as u32 & 0x3F));
                i += 2;
            } else {
                out.push(0xFFFD);
                i += 1;
            }
        } else if b0 < 0xF0 {
            if i + 2 < b.len() {
                out.push(
                    ((b0 & 0x0F) << 12)
                        | ((b[i + 1] as u32 & 0x3F) << 6)
                        | (b[i + 2] as u32 & 0x3F),
                );
                i += 3;
            } else {
                out.push(0xFFFD);
                i = b.len();
            }
        } else if i + 3 < b.len() {
            out.push(
                ((b0 & 0x07) << 18)
                    | ((b[i + 1] as u32 & 0x3F) << 12)
                    | ((b[i + 2] as u32 & 0x3F) << 6)
                    | (b[i + 3] as u32 & 0x3F),
            );
            i += 4;
        } else {
            out.push(0xFFFD);
            i = b.len();
        }
    }
    out
}

/// Code points to Python `str`: fast path for valid scalars, CESU-8 +
/// `surrogatepass` decode for lone surrogates, `ValueError` past
/// `0x10FFFF` (mirrors `chr()` exactly, message verified on the host).
fn u32s_to_py<'py>(py: Python<'py>, v: &[u32]) -> PyResult<Bound<'py, PyString>> {
    if v.iter().all(|&c| char::from_u32(c).is_some()) {
        let s: String = v.iter().map(|&c| char::from_u32(c).unwrap()).collect();
        return Ok(PyString::new(py, &s));
    }
    if v.iter().any(|&c| c > 0x10FFFF) {
        return Err(PyValueError::new_err("chr() arg not in range(0x110000)"));
    }
    let mut b = Vec::with_capacity(v.len() * 3);
    for &c in v {
        if c < 0x80 {
            b.push(c as u8);
        } else if c < 0x800 {
            b.push((0xC0 | (c >> 6)) as u8);
            b.push((0x80 | (c & 0x3F)) as u8);
        } else if c < 0x10000 {
            b.push((0xE0 | (c >> 12)) as u8);
            b.push((0x80 | ((c >> 6) & 0x3F)) as u8);
            b.push((0x80 | (c & 0x3F)) as u8);
        } else {
            b.push((0xF0 | (c >> 18)) as u8);
            b.push((0x80 | ((c >> 12) & 0x3F)) as u8);
            b.push((0x80 | ((c >> 6) & 0x3F)) as u8);
            b.push((0x80 | (c & 0x3F)) as u8);
        }
    }
    let bytes = PyBytes::new(py, &b);
    bytes.call_method("decode", ("utf-8", "surrogatepass"), None)?.extract()
}

// ---------------------------------------------------------------------------
// Error payloads.
// ---------------------------------------------------------------------------

/// A mark as a plain `(index, line, column)` triple.
type MarkTriple = (usize, usize, usize);

fn mark_tuple(mark: &MarkPos) -> MarkTriple {
    (mark.index, mark.line, mark.column)
}

/// Rendered scan/parse fault: context and problem templates with args.
type FaultPayload =
    (Option<String>, Vec<PyObject>, Option<MarkTriple>, String, Vec<PyObject>, MarkTriple);

fn arg_to_py(py: Python<'_>, arg: &ErrArg) -> PyResult<PyObject> {
    match arg {
        ErrArg::Char(c) => Ok(u32s_to_py(py, &[*c])?.into_any().unbind()),
        ErrArg::Int(i) => Ok(i.into_pyobject(py)?.into_any().unbind()),
        ErrArg::Str(s) => Ok(PyString::new(py, s).into_any().unbind()),
        ErrArg::Codes(v) => Ok(u32s_to_py(py, v)?.into_any().unbind()),
    }
}

fn formatted_to_py(py: Python<'_>, f: &Formatted) -> PyResult<(String, Vec<PyObject>)> {
    let mut args = Vec::with_capacity(f.args.len());
    for a in &f.args {
        args.push(arg_to_py(py, a)?);
    }
    Ok((f.tpl.clone(), args))
}

fn engine_error_to_py(py: Python<'_>, e: &EngineError) -> PyResult<FaultPayload> {
    let (ctx_tpl, ctx_args) = match &e.context {
        Some(c) => {
            let (t, a) = formatted_to_py(py, c)?;
            (Some(t), a)
        }
        None => (None, Vec::new()),
    };
    let (prob_tpl, prob_args) = formatted_to_py(py, &e.problem)?;
    Ok((
        ctx_tpl,
        ctx_args,
        e.context_mark.as_ref().map(mark_tuple),
        prob_tpl,
        prob_args,
        mark_tuple(&e.problem_mark),
    ))
}

fn scan_fault_to_py(py: Python<'_>, fault: ScanFault) -> PyResult<PyErr> {
    match fault {
        ScanFault::Engine(e) => {
            let payload = engine_error_to_py(py, &e)?;
            Ok(ScanFaultExc::new_err(payload))
        }
        ScanFault::UriDecode(UriDecodeFault { codes, name, start_mark, mark }) => {
            Ok(UriFaultExc::new_err((
                codes,
                name,
                mark_tuple(&start_mark),
                mark_tuple(&mark),
            )))
        }
    }
}

// ---------------------------------------------------------------------------
// Tokens: core -> tuple.
// ---------------------------------------------------------------------------

/// Token tuple: `(tag, s1, s2, s3, b1, marks)`. Per-tag payloads mirror the
/// `yaml.tokens` constructors positionally; the facade builds the objects.
fn token_to_py(py: Python<'_>, tok: &ScanToken) -> PyResult<PyObject> {
    let empty = PyString::new(py, "");
    let (tag, s1, s2, s3, b1, start, end) = match tok {
        ScanToken::StreamStart { encoding, start, end } => (
            0,
            encoding.as_deref().map(|e| PyString::new(py, e)).unwrap_or_else(|| empty.clone()),
            empty.clone(),
            empty.clone(),
            false,
            start,
            end,
        ),
        ScanToken::StreamEnd { start, end } => {
            (1, empty.clone(), empty.clone(), empty.clone(), false, start, end)
        }
        ScanToken::Directive { name, value, start, end } => {
            let (v1, v2) = match value {
                DirectiveValue::Yaml(ma, mi) => {
                    (PyString::new(py, ma), PyString::new(py, mi))
                }
                DirectiveValue::Tag(h, p) => {
                    (PyString::new(py, h), PyString::new(py, p))
                }
                DirectiveValue::Other => (empty.clone(), empty.clone()),
            };
            (2, PyString::new(py, name), v1, v2, false, start, end)
        }
        ScanToken::DocumentStart { start, end } => {
            (3, empty.clone(), empty.clone(), empty.clone(), false, start, end)
        }
        ScanToken::DocumentEnd { start, end } => {
            (4, empty.clone(), empty.clone(), empty.clone(), false, start, end)
        }
        ScanToken::BlockSequenceStart { start, end } => {
            (5, empty.clone(), empty.clone(), empty.clone(), false, start, end)
        }
        ScanToken::BlockMappingStart { start, end } => {
            (6, empty.clone(), empty.clone(), empty.clone(), false, start, end)
        }
        ScanToken::BlockEnd { start, end } => {
            (7, empty.clone(), empty.clone(), empty.clone(), false, start, end)
        }
        ScanToken::FlowSequenceStart { start, end } => {
            (8, empty.clone(), empty.clone(), empty.clone(), false, start, end)
        }
        ScanToken::FlowMappingStart { start, end } => {
            (9, empty.clone(), empty.clone(), empty.clone(), false, start, end)
        }
        ScanToken::FlowSequenceEnd { start, end } => {
            (10, empty.clone(), empty.clone(), empty.clone(), false, start, end)
        }
        ScanToken::FlowMappingEnd { start, end } => {
            (11, empty.clone(), empty.clone(), empty.clone(), false, start, end)
        }
        ScanToken::BlockEntry { start, end } => {
            (12, empty.clone(), empty.clone(), empty.clone(), false, start, end)
        }
        ScanToken::FlowEntry { start, end } => {
            (13, empty.clone(), empty.clone(), empty.clone(), false, start, end)
        }
        ScanToken::Key { start, end } => {
            (14, empty.clone(), empty.clone(), empty.clone(), false, start, end)
        }
        ScanToken::Value { start, end } => {
            (15, empty.clone(), empty.clone(), empty.clone(), false, start, end)
        }
        ScanToken::Alias { value, start, end } => {
            (16, PyString::new(py, value), empty.clone(), empty.clone(), false, start, end)
        }
        ScanToken::Anchor { value, start, end } => {
            (17, PyString::new(py, value), empty.clone(), empty.clone(), false, start, end)
        }
        ScanToken::Tag { handle, suffix, start, end } => (
            18,
            handle.as_deref().map(|h| PyString::new(py, h)).unwrap_or_else(|| empty.clone()),
            u32s_to_py(py, &suffix.0)?,
            empty.clone(),
            handle.is_some(),
            start,
            end,
        ),
        ScanToken::Scalar { value, plain, style, start, end } => (
            19,
            u32s_to_py(py, &value.0)?,
            style.map(|c| PyString::new(py, &c.to_string())).unwrap_or_else(|| empty.clone()),
            empty.clone(),
            *plain,
            start,
            end,
        ),
    };
    let marks = (mark_tuple(start), mark_tuple(end));
    Ok((tag, s1, s2, s3, b1, marks).into_pyobject(py)?.into_any().unbind())
}

// ---------------------------------------------------------------------------
// Engine class.
// ---------------------------------------------------------------------------

/// Scan engine behind the `Scanner` facade: one object per scanner,
/// exactly like the original MRO-shared state.
#[pyclass]
struct Engine {
    scan: ScanCore,
}

#[pymethods]
impl Engine {
    #[new]
    #[pyo3(signature = (text, encoding=None))]
    fn new(text: Bound<'_, PyString>, encoding: Option<String>) -> PyResult<Self> {
        Ok(Engine {
            scan: ScanCore::new(str_to_u32s(&text)?, encoding),
        })
    }

    fn peek_token(&mut self, py: Python<'_>) -> PyResult<Option<PyObject>> {
        match self.scan.peek_token() {
            Ok(Some(tok)) => Ok(Some(token_to_py(py, &tok)?)),
            Ok(None) => Ok(None),
            Err(f) => Err(scan_fault_to_py(py, f)?),
        }
    }

    /// Drop the head token after a successful peek (mirrors `get_token`:
    /// the pop itself pulls nothing and cannot fail).
    fn consume_token(&mut self) {
        self.scan.pop_head();
    }

    fn next_token(&mut self, py: Python<'_>) -> PyResult<Option<PyObject>> {
        match self.scan.next_token() {
            Ok(Some(tok)) => Ok(Some(token_to_py(py, &tok)?)),
            Ok(None) => Ok(None),
            Err(f) => Err(scan_fault_to_py(py, f)?),
        }
    }

    fn has_token(&mut self, py: Python<'_>) -> PyResult<bool> {
        match self.scan.has_token() {
            Ok(v) => Ok(v),
            Err(f) => Err(scan_fault_to_py(py, f)?),
        }
    }
}
#[pymodule]
fn _rust(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<Engine>()?;
    m.add("ScanFault", m.py().get_type::<ScanFaultExc>())?;
    m.add("UriFault", m.py().get_type::<UriFaultExc>())?;
    Ok(())
}
