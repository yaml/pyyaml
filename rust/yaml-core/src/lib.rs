//! `yaml-scan-core`: reusable YAML 1.1 scan engine (scan kernel only).
//!
//! A faithful port of PyYAML's pure-Python `scanner.py` onto a `Vec<u32>`
//! (code-point) text model. No Python dependency: token descriptors cross
//! to Python in the `yaml._rust` binding (`src/lib.rs`), which also owns
//! every Python-visible formatting decision (`%r` rendering,
//! `bytes.decode`, `chr()` errors). Error sites therefore carry message
//! *templates* plus typed arguments, never rendered text.

//! Clippy: `result_large_err` is allowed crate-wide by design — scan faults
//! carry message templates plus context marks as values (cold paths only;
//! boxing them would churn every state-machine step for no runtime gain).
#![allow(clippy::result_large_err)]

pub mod scan;

/// A code-point position: mirrors `Reader.index/line/column` exactly
/// (column counts characters; `\uFEFF` advances index only).
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct MarkPos {
    pub index: usize,
    pub line: usize,
    pub column: usize,
}

/// A typed `%`-format argument for an error message template. The Python
/// facade renders these with real `%` formatting, so `%r` output is
/// byte-identical to the original without reimplementing `repr`.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ErrArg {
    /// A single character (always a valid scalar value at error sites).
    Char(u32),
    /// An integer (`%d`).
    Int(i64),
    /// A pre-rendered string (`%s`/`%r` of a plain string).
    Str(String),
    /// Code points rendered facade-side (`%r` of text that may hold lone
    /// surrogates, e.g. anchors/handles under validation).
    Codes(Vec<u32>),
}

/// An error message with deferred rendering.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Formatted {
    pub tpl: String,
    pub args: Vec<ErrArg>,
}

impl Formatted {
    pub fn new(tpl: &str) -> Self {
        Formatted { tpl: tpl.to_string(), args: Vec::new() }
    }
    pub fn arg(mut self, a: ErrArg) -> Self {
        self.args.push(a);
        self
    }
}

/// Scanner/parser error shape: mirrors `MarkedYAMLError`
/// `(context, context_mark, problem, problem_mark)`.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct EngineError {
    pub context: Option<Formatted>,
    pub context_mark: Option<MarkPos>,
    pub problem: Formatted,
    pub problem_mark: MarkPos,
}

impl EngineError {
    pub fn new(problem: Formatted, problem_mark: MarkPos) -> Self {
        EngineError { context: None, context_mark: None, problem, problem_mark }
    }
    /// Context with an explicit mark.
    pub fn ctx(mut self, context: Formatted, mark: MarkPos) -> Self {
        self.context = Some(context);
        self.context_mark = Some(mark);
        self
    }
    /// Context without a mark (mirrors `context_mark=None`).
    pub fn ctx_none(mut self, context: Formatted) -> Self {
        self.context = Some(context);
        self.context_mark = None;
        self
    }
}

/// Lossless code-point string: every `u32` a YAML escape can produce,
/// including lone surrogates (which Rust `char`/`String` cannot hold).
/// The binding converts these to Python `str` (fast path for valid
/// scalars, `surrogatepass` for the rest, `ValueError` past `0x10FFFF`).
#[derive(Debug, Clone, PartialEq, Eq, Default)]
pub struct YStr(pub Vec<u32>);

impl YStr {
    pub fn new() -> Self {
        YStr(Vec::new())
    }
    pub fn from_slice(v: &[u32]) -> Self {
        YStr(v.to_vec())
    }
    pub fn push(&mut self, c: u32) {
        self.0.push(c);
    }
    pub fn extend(&mut self, v: &[u32]) {
        self.0.extend_from_slice(v);
    }
    pub fn len(&self) -> usize {
        self.0.len()
    }
    pub fn is_empty(&self) -> bool {
        self.0.is_empty()
    }
}

/// True when every code point is a valid Unicode scalar value.
pub fn is_valid_scalar(v: &[u32]) -> bool {
    v.iter().all(|&c| char::from_u32(c).is_some())
}

/// Convert validated code points to a Rust `String`. Panics only on a core
/// bug (callers advance over pre-validated slices, or hold escape codes
/// handled at the boundary).
pub fn to_rust_string(v: &[u32]) -> String {
    v.iter().map(|&c| char::from_u32(c).expect("core slice holds valid scalars")).collect()
}
