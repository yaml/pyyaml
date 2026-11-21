//! YAML 1.1 scanner: character stream to tokens.
//!
//! Faithful port of PyYAML 6.0.2 `lib/yaml/scanner.py`. The text model is
//! `Vec<u32>` (code points); positions (`index`/`line`/`column`) follow
//! `Reader.forward` exactly. Token payloads are lossless `YStr` values;
//! error sites return templates + typed args (rendered by the Python
//! facade, so `%r` output is byte-identical without reimplementing `repr`).

use super::{EngineError, ErrArg, Formatted, MarkPos, YStr};
use std::collections::VecDeque;

// ---------------------------------------------------------------------------
// Token descriptors (cross to Python in the binding as tuples).
// ---------------------------------------------------------------------------

/// Directive value: YAML carries decimal number strings (facade `int()`s
/// them, so huge values stay exact); TAG carries handle + prefix.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum DirectiveValue {
    Yaml(String, String),
    Tag(String, String),
    Other,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Token {
    StreamStart { encoding: Option<String>, start: MarkPos, end: MarkPos },
    StreamEnd { start: MarkPos, end: MarkPos },
    Directive { name: String, value: DirectiveValue, start: MarkPos, end: MarkPos },
    DocumentStart { start: MarkPos, end: MarkPos },
    DocumentEnd { start: MarkPos, end: MarkPos },
    BlockSequenceStart { start: MarkPos, end: MarkPos },
    BlockMappingStart { start: MarkPos, end: MarkPos },
    BlockEnd { start: MarkPos, end: MarkPos },
    FlowSequenceStart { start: MarkPos, end: MarkPos },
    FlowMappingStart { start: MarkPos, end: MarkPos },
    FlowSequenceEnd { start: MarkPos, end: MarkPos },
    FlowMappingEnd { start: MarkPos, end: MarkPos },
    BlockEntry { start: MarkPos, end: MarkPos },
    FlowEntry { start: MarkPos, end: MarkPos },
    Key { start: MarkPos, end: MarkPos },
    Value { start: MarkPos, end: MarkPos },
    Alias { value: String, start: MarkPos, end: MarkPos },
    Anchor { value: String, start: MarkPos, end: MarkPos },
    Tag { handle: Option<String>, suffix: YStr, start: MarkPos, end: MarkPos },
    Scalar { value: YStr, plain: bool, style: Option<char>, start: MarkPos, end: MarkPos },
}

/// Token-kind discriminant for `check_token` groups (fieldless, `Copy`).
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum TokenKind {
    StreamStart,
    StreamEnd,
    Directive,
    DocumentStart,
    DocumentEnd,
    BlockSequenceStart,
    BlockMappingStart,
    BlockEnd,
    FlowSequenceStart,
    FlowMappingStart,
    FlowSequenceEnd,
    FlowMappingEnd,
    BlockEntry,
    FlowEntry,
    Key,
    Value,
    Alias,
    Anchor,
    Tag,
    Scalar,
}

impl Token {
    /// Discriminant of a token for kind-group checks.
    pub fn kind(&self) -> TokenKind {
        match self {
            Token::StreamStart { .. } => TokenKind::StreamStart,
            Token::StreamEnd { .. } => TokenKind::StreamEnd,
            Token::Directive { .. } => TokenKind::Directive,
            Token::DocumentStart { .. } => TokenKind::DocumentStart,
            Token::DocumentEnd { .. } => TokenKind::DocumentEnd,
            Token::BlockSequenceStart { .. } => TokenKind::BlockSequenceStart,
            Token::BlockMappingStart { .. } => TokenKind::BlockMappingStart,
            Token::BlockEnd { .. } => TokenKind::BlockEnd,
            Token::FlowSequenceStart { .. } => TokenKind::FlowSequenceStart,
            Token::FlowMappingStart { .. } => TokenKind::FlowMappingStart,
            Token::FlowSequenceEnd { .. } => TokenKind::FlowSequenceEnd,
            Token::FlowMappingEnd { .. } => TokenKind::FlowMappingEnd,
            Token::BlockEntry { .. } => TokenKind::BlockEntry,
            Token::FlowEntry { .. } => TokenKind::FlowEntry,
            Token::Key { .. } => TokenKind::Key,
            Token::Value { .. } => TokenKind::Value,
            Token::Alias { .. } => TokenKind::Alias,
            Token::Anchor { .. } => TokenKind::Anchor,
            Token::Tag { .. } => TokenKind::Tag,
            Token::Scalar { .. } => TokenKind::Scalar,
        }
    }
}

/// Errors needing Python-side decoding: `%`-escape groups that are not
/// valid UTF-8. The facade runs `bytes.decode` itself so the
/// `UnicodeDecodeError` text is exact.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct UriDecodeFault {
    pub codes: Vec<u8>,
    pub name: String,
    pub start_mark: MarkPos,
    pub mark: MarkPos,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ScanFault {
    Engine(EngineError),
    UriDecode(UriDecodeFault),
}

impl From<EngineError> for ScanFault {
    fn from(e: EngineError) -> Self {
        ScanFault::Engine(e)
    }
}

// ---------------------------------------------------------------------------
// Character classes (mirror the Python `in '...'` sets).
// ---------------------------------------------------------------------------

fn is_break(ch: u32) -> bool {
    matches!(ch, 0x0D | 0x0A | 0x85 | 0x2028 | 0x2029)
}

fn is_break_or_nul(ch: u32) -> bool {
    ch == 0 || is_break(ch)
}


fn is_blank(ch: u32) -> bool {
    matches!(ch, 0x20 | 0x09) || is_break(ch)
}

fn is_blank_or_nul(ch: u32) -> bool {
    ch == 0 || is_blank(ch)
}

fn is_digit(ch: u32) -> bool {
    (b'0' as u32..=b'9' as u32).contains(&ch)
}

fn is_alpha(ch: u32) -> bool {
    (b'0' as u32..=b'9' as u32).contains(&ch)
        || (b'A' as u32..=b'Z' as u32).contains(&ch)
        || (b'a' as u32..=b'z' as u32).contains(&ch)
}

fn is_alphanum_dash_underscore(ch: u32) -> bool {
    is_alpha(ch) || ch == b'-' as u32 || ch == b'_' as u32
}

fn is_hex(ch: u32) -> bool {
    is_digit(ch)
        || (b'A' as u32..=b'F' as u32).contains(&ch)
        || (b'a' as u32..=b'f' as u32).contains(&ch)
}

fn is_uri_char(ch: u32) -> bool {
    // Python set '-;/?:@&=+$,_.!~*\'()[]%'.
    is_alpha(ch)
        || matches!(
            ch,
            0x2D | 0x3B | 0x2F | 0x3F | 0x3A | 0x40 | 0x26 | 0x3D | 0x2B | 0x24 | 0x2C
            | 0x5F | 0x2E | 0x21 | 0x7E | 0x2A | 0x27 | 0x28 | 0x29 | 0x5B | 0x5D | 0x25
        )
}

fn is_anchor_char(ch: u32) -> bool {
    is_alpha(ch) || ch == b'-' as u32 || ch == b'_' as u32
}

// ---------------------------------------------------------------------------
// Scanner.
// ---------------------------------------------------------------------------

#[derive(Debug, Clone)]
struct SimpleKey {
    token_number: usize,
    required: bool,
    index: usize,
    line: usize,
    column: usize,
    mark: MarkPos,
}

#[derive(Debug, Clone)]
pub struct ScanCore {
    text: Vec<u32>,
    encoding: Option<String>,
    index: usize,
    line: usize,
    column: usize,
    done: bool,
    flow_level: i64,
    tokens: VecDeque<Token>,
    tokens_taken: usize,
    indent: i64,
    indents: Vec<i64>,
    allow_simple_key: bool,
    possible_simple_keys: Vec<(i64, SimpleKey)>,
}

const ESCAPE_REPLACEMENTS: &[(u32, u32)] = &[
    (b'0' as u32, 0x00),
    (b'a' as u32, 0x07),
    (b'b' as u32, 0x08),
    (b't' as u32, 0x09),
    (0x09, 0x09),
    (b'n' as u32, 0x0A),
    (b'v' as u32, 0x0B),
    (b'f' as u32, 0x0C),
    (b'r' as u32, 0x0D),
    (b'e' as u32, 0x1B),
    (b' ' as u32, 0x20),
    (b'"' as u32, 0x22),
    (b'\\' as u32, 0x5C),
    (b'/' as u32, 0x2F),
    (b'N' as u32, 0x85),
    (b'_' as u32, 0xA0),
    (b'L' as u32, 0x2028),
    (b'P' as u32, 0x2029),
];

fn escape_replacement(ch: u32) -> Option<u32> {
    ESCAPE_REPLACEMENTS.iter().find(|&&(k, _)| k == ch).map(|&(_, v)| v)
}

fn escape_code_len(ch: u32) -> Option<usize> {
    match ch {
        0x78 => Some(2), // x
        0x75 => Some(4), // u
        0x55 => Some(8), // U
        _ => None,
    }
}

impl ScanCore {
    pub fn new(text: Vec<u32>, encoding: Option<String>) -> Self {
        let mut core = ScanCore {
            text,
            encoding,
            index: 0,
            line: 0,
            column: 0,
            done: false,
            flow_level: 0,
            tokens: VecDeque::new(),
            tokens_taken: 0,
            indent: -1,
            indents: Vec::new(),
            allow_simple_key: true,
            possible_simple_keys: Vec::new(),
        };
        core.fetch_stream_start();
        core
    }

    // -- reader primitives -------------------------------------------------

    fn get_mark(&self) -> MarkPos {
        MarkPos { index: self.index, line: self.line, column: self.column }
    }

    /// Peek the i-th character (NUL past the end, mirroring the sentinel).
    fn peek(&self, i: usize) -> u32 {
        *self.text.get(self.pos() + i).unwrap_or(&0)
    }

    fn pos(&self) -> usize {
        // `index` counts consumed characters from the start, and the core
        // always consumes from position 0 with no compaction, so the read
        // position equals `index`.
        self.index
    }

    fn prefix(&self, length: usize) -> Vec<u32> {
        let start = self.pos();
        let end = (start + length).min(self.text.len());
        self.text[start..end].to_vec()
    }

    /// Advance, maintaining index/line/column exactly like `Reader.forward`.
    fn forward(&mut self, mut length: usize) {
        while length > 0 {
            let ch = self.peek(0);
            self.index += 1;
            if ch == 0x0A || ch == 0x85 || ch == 0x2028 || ch == 0x2029
                || (ch == 0x0D && self.peek(0) != 0x0A)
            {
                // Note: after `index += 1` the "current" character for the
                // `\r\n` check is the NEXT one; `peek(0)` now reads it.
                self.line += 1;
                self.column = 0;
            } else if ch != 0xFEFF {
                self.column += 1;
            }
            length -= 1;
        }
    }

    // -- public pulls (own the need_more/fetch loop) -----------------------

    fn need_more_tokens(&mut self) -> Result<bool, ScanFault> {
        if self.done {
            return Ok(false);
        }
        if self.tokens.is_empty() {
            return Ok(true);
        }
        self.stale_possible_simple_keys()?;
        if self.next_possible_simple_key() == Some(self.tokens_taken) {
            return Ok(true);
        }
        Ok(false)
    }

    /// Fill until at least one token is queued (or the stream ends).
    fn fill(&mut self) -> Result<(), ScanFault> {
        while self.need_more_tokens()? {
            self.fetch_more_tokens()?;
        }
        Ok(())
    }

    /// Peek the head token without consuming.
    pub fn peek_token(&mut self) -> Result<Option<Token>, ScanFault> {
        self.fill()?;
        Ok(self.tokens.front().cloned())
    }

    /// Drop the head token without pulling more (the facade peeks first,
    /// so the pop itself is infallible, exactly like the original).
    pub fn pop_head(&mut self) {
        if self.tokens.pop_front().is_some() {
            self.tokens_taken += 1;
        }
    }

    /// Pop the head token.
    pub fn next_token(&mut self) -> Result<Option<Token>, ScanFault> {
        self.fill()?;
        if let Some(tok) = self.tokens.pop_front() {
            self.tokens_taken += 1;
            Ok(Some(tok))
        } else {
            Ok(None)
        }
    }

    /// Whether any token remains (pulls until decidable).
    pub fn has_token(&mut self) -> Result<bool, ScanFault> {
        self.fill()?;
        Ok(!self.tokens.is_empty())
    }

    // -- simple keys --------------------------------------------------------
    // Insertion-ordered `(flow_level, key)` pairs: mirrors the Python dict
    // (replacement keeps position, iteration is insertion order, which
    // decides which stale required key reports first).

    fn next_possible_simple_key(&self) -> Option<usize> {
        self.possible_simple_keys
            .iter()
            .map(|(_, k)| k.token_number)
            .min()
    }

    fn stale_possible_simple_keys(&mut self) -> Result<(), ScanFault> {
        let mut stale_levels = Vec::new();
        for (level, key) in &self.possible_simple_keys {
            if key.line != self.line || self.index as i64 - key.index as i64 > 1024 {
                if key.required {
                    let here = self.get_mark();
                    return Err(EngineError::new(
                        Formatted::new("could not find expected ':'"),
                        here,
                    )
                    .ctx(
                        Formatted::new("while scanning a simple key"),
                        key.mark,
                    )
                    .into());
                }
                stale_levels.push(*level);
            }
        }
        self.possible_simple_keys
            .retain(|(level, _)| !stale_levels.contains(level));
        Ok(())
    }

    fn find_key_index(&self, level: i64) -> Option<usize> {
        self.possible_simple_keys.iter().position(|(l, _)| *l == level)
    }

    fn save_possible_simple_key(&mut self) -> Result<(), ScanFault> {
        let required = self.flow_level == 0 && self.indent == self.column as i64;
        if self.allow_simple_key {
            self.remove_possible_simple_key()?;
            let token_number = self.tokens_taken + self.tokens.len();
            let key = SimpleKey {
                token_number,
                required,
                index: self.index,
                line: self.line,
                column: self.column,
                mark: self.get_mark(),
            };
            // Dict-assignment semantics: replace in place, else append.
            if let Some(i) = self.find_key_index(self.flow_level) {
                self.possible_simple_keys[i].1 = key;
            } else {
                self.possible_simple_keys.push((self.flow_level, key));
            }
        }
        Ok(())
    }

    fn take_key(&mut self, level: i64) -> Option<SimpleKey> {
        self.find_key_index(level)
            .map(|i| self.possible_simple_keys.remove(i).1)
    }

    fn remove_possible_simple_key(&mut self) -> Result<(), ScanFault> {
        if let Some(key) = self.take_key(self.flow_level) {
            if key.required {
                let mark = self.get_mark();
                return Err(EngineError::new(
                    Formatted::new("could not find expected ':'"),
                    mark,
                )
                .ctx(Formatted::new("while scanning a simple key"), key.mark)
                .into());
            }
        }
        Ok(())
    }

    // -- indentation --------------------------------------------------------

    fn unwind_indent(&mut self, column: i64) {
        if self.flow_level != 0 {
            return;
        }
        while self.indent > column {
            let mark = self.get_mark();
            if let Some(ind) = self.indents.pop() {
                self.indent = ind;
            } else {
                self.indent = -1;
            }
            self.tokens.push_back(Token::BlockEnd { start: mark, end: mark });
        }
    }

    fn add_indent(&mut self, column: i64) -> bool {
        if self.indent < column {
            self.indents.push(self.indent);
            self.indent = column;
            return true;
        }
        false
    }

    // -- fetchers ------------------------------------------------------------

    fn fetch_more_tokens(&mut self) -> Result<(), ScanFault> {
        self.scan_to_next_token();
        self.stale_possible_simple_keys()?;
        self.unwind_indent(self.column as i64);
        let ch = self.peek(0);
        if ch == 0 {
            return self.fetch_stream_end();
        }
        if ch == b'%' as u32 && self.check_directive() {
            return self.fetch_directive();
        }
        if ch == b'-' as u32 && self.check_document_start() {
            return self.fetch_document_start();
        }
        if ch == b'.' as u32 && self.check_document_end() {
            return self.fetch_document_end();
        }
        if ch == b'[' as u32 {
            return self.fetch_flow_sequence_start();
        }
        if ch == b'{' as u32 {
            return self.fetch_flow_mapping_start();
        }
        if ch == b']' as u32 {
            return self.fetch_flow_sequence_end();
        }
        if ch == b'}' as u32 {
            return self.fetch_flow_mapping_end();
        }
        if ch == b',' as u32 {
            return self.fetch_flow_entry();
        }
        if ch == b'-' as u32 && self.check_block_entry() {
            return self.fetch_block_entry();
        }
        if ch == b'?' as u32 && self.check_key() {
            return self.fetch_key();
        }
        if ch == b':' as u32 && self.check_value() {
            return self.fetch_value();
        }
        if ch == b'*' as u32 {
            return self.fetch_alias();
        }
        if ch == b'&' as u32 {
            return self.fetch_anchor();
        }
        if ch == b'!' as u32 {
            return self.fetch_tag();
        }
        if ch == b'|' as u32 && self.flow_level == 0 {
            return self.fetch_literal();
        }
        if ch == b'>' as u32 && self.flow_level == 0 {
            return self.fetch_folded();
        }
        if ch == b'\'' as u32 {
            return self.fetch_single();
        }
        if ch == b'"' as u32 {
            return self.fetch_double();
        }
        if self.check_plain() {
            return self.fetch_plain();
        }
        let mark = self.get_mark();
        Err(EngineError::new(
            Formatted::new("found character %r that cannot start any token")
                .arg(ErrArg::Char(ch)),
            mark,
        )
        .ctx_none(Formatted::new("while scanning for the next token"))
        .into())
    }

    fn fetch_stream_start(&mut self) {
        let mark = self.get_mark();
        self.tokens.push_back(Token::StreamStart {
            encoding: self.encoding.clone(),
            start: mark,
            end: mark,
        });
    }

    fn fetch_stream_end(&mut self) -> Result<(), ScanFault> {
        self.unwind_indent(-1);
        self.remove_possible_simple_key()?;
        self.allow_simple_key = false;
        self.possible_simple_keys.clear();
        let mark = self.get_mark();
        self.tokens.push_back(Token::StreamEnd { start: mark, end: mark });
        self.done = true;
        Ok(())
    }

    fn fetch_directive(&mut self) -> Result<(), ScanFault> {
        self.unwind_indent(-1);
        self.remove_possible_simple_key()?;
        self.allow_simple_key = false;
        let tok = self.scan_directive()?;
        self.tokens.push_back(tok);
        Ok(())
    }

    fn fetch_document_start(&mut self) -> Result<(), ScanFault> {
        self.fetch_document_indicator(true)
    }

    fn fetch_document_end(&mut self) -> Result<(), ScanFault> {
        self.fetch_document_indicator(false)
    }

    fn fetch_document_indicator(&mut self, start: bool) -> Result<(), ScanFault> {
        self.unwind_indent(-1);
        self.remove_possible_simple_key()?;
        self.allow_simple_key = false;
        let start_mark = self.get_mark();
        self.forward(3);
        let end_mark = self.get_mark();
        if start {
            self.tokens.push_back(Token::DocumentStart { start: start_mark, end: end_mark });
        } else {
            self.tokens.push_back(Token::DocumentEnd { start: start_mark, end: end_mark });
        }
        Ok(())
    }

    fn fetch_flow_sequence_start(&mut self) -> Result<(), ScanFault> {
        self.fetch_flow_collection_start(true)
    }

    fn fetch_flow_mapping_start(&mut self) -> Result<(), ScanFault> {
        self.fetch_flow_collection_start(false)
    }

    fn fetch_flow_collection_start(&mut self, seq: bool) -> Result<(), ScanFault> {
        self.save_possible_simple_key()?;
        self.flow_level += 1;
        self.allow_simple_key = true;
        let start_mark = self.get_mark();
        self.forward(1);
        let end_mark = self.get_mark();
        if seq {
            self.tokens.push_back(Token::FlowSequenceStart { start: start_mark, end: end_mark });
        } else {
            self.tokens.push_back(Token::FlowMappingStart { start: start_mark, end: end_mark });
        }
        Ok(())
    }

    fn fetch_flow_sequence_end(&mut self) -> Result<(), ScanFault> {
        self.fetch_flow_collection_end(true)
    }

    fn fetch_flow_mapping_end(&mut self) -> Result<(), ScanFault> {
        self.fetch_flow_collection_end(false)
    }

    fn fetch_flow_collection_end(&mut self, seq: bool) -> Result<(), ScanFault> {
        self.remove_possible_simple_key()?;
        self.flow_level -= 1;
        self.allow_simple_key = false;
        let start_mark = self.get_mark();
        self.forward(1);
        let end_mark = self.get_mark();
        if seq {
            self.tokens.push_back(Token::FlowSequenceEnd { start: start_mark, end: end_mark });
        } else {
            self.tokens.push_back(Token::FlowMappingEnd { start: start_mark, end: end_mark });
        }
        Ok(())
    }

    fn fetch_flow_entry(&mut self) -> Result<(), ScanFault> {
        self.allow_simple_key = true;
        self.remove_possible_simple_key()?;
        let start_mark = self.get_mark();
        self.forward(1);
        let end_mark = self.get_mark();
        self.tokens.push_back(Token::FlowEntry { start: start_mark, end: end_mark });
        Ok(())
    }

    fn fetch_block_entry(&mut self) -> Result<(), ScanFault> {
        if self.flow_level == 0 {
            if !self.allow_simple_key {
                let mark = self.get_mark();
                return Err(EngineError::new(
                    Formatted::new("sequence entries are not allowed here"),
                    mark,
                )
                .into());
            }
            if self.add_indent(self.column as i64) {
                let mark = self.get_mark();
                self.tokens.push_back(Token::BlockSequenceStart { start: mark, end: mark });
            }
        }
        self.allow_simple_key = true;
        self.remove_possible_simple_key()?;
        let start_mark = self.get_mark();
        self.forward(1);
        let end_mark = self.get_mark();
        self.tokens.push_back(Token::BlockEntry { start: start_mark, end: end_mark });
        Ok(())
    }

    fn fetch_key(&mut self) -> Result<(), ScanFault> {
        if self.flow_level == 0 {
            if !self.allow_simple_key {
                let mark = self.get_mark();
                return Err(EngineError::new(
                    Formatted::new("mapping keys are not allowed here"),
                    mark,
                )
                .into());
            }
            if self.add_indent(self.column as i64) {
                let mark = self.get_mark();
                self.tokens.push_back(Token::BlockMappingStart { start: mark, end: mark });
            }
        }
        self.allow_simple_key = self.flow_level == 0;
        self.remove_possible_simple_key()?;
        let start_mark = self.get_mark();
        self.forward(1);
        let end_mark = self.get_mark();
        self.tokens.push_back(Token::Key { start: start_mark, end: end_mark });
        Ok(())
    }

    fn fetch_value(&mut self) -> Result<(), ScanFault> {
        if let Some(key) = self.take_key(self.flow_level) {
            let at = key.token_number - self.tokens_taken;
            self.tokens.insert(at, Token::Key { start: key.mark, end: key.mark });
            if self.flow_level == 0 && self.add_indent(key.column as i64) {
                let at = key.token_number - self.tokens_taken;
                self.tokens.insert(
                    at,
                    Token::BlockMappingStart { start: key.mark, end: key.mark },
                );
            }
            self.allow_simple_key = false;
        } else {
            if self.flow_level == 0 {
                if !self.allow_simple_key {
                    let mark = self.get_mark();
                    return Err(EngineError::new(
                        Formatted::new("mapping values are not allowed here"),
                        mark,
                    )
                    .into());
                }
                if self.add_indent(self.column as i64) {
                    let mark = self.get_mark();
                    self.tokens.push_back(Token::BlockMappingStart { start: mark, end: mark });
                }
                self.allow_simple_key = self.flow_level == 0;
            }
            self.remove_possible_simple_key()?;
        }
        let start_mark = self.get_mark();
        self.forward(1);
        let end_mark = self.get_mark();
        self.tokens.push_back(Token::Value { start: start_mark, end: end_mark });
        Ok(())
    }

    fn fetch_alias(&mut self) -> Result<(), ScanFault> {
        self.save_possible_simple_key()?;
        self.allow_simple_key = false;
        let tok = self.scan_anchor(true)?;
        self.tokens.push_back(tok);
        Ok(())
    }

    fn fetch_anchor(&mut self) -> Result<(), ScanFault> {
        self.save_possible_simple_key()?;
        self.allow_simple_key = false;
        let tok = self.scan_anchor(false)?;
        self.tokens.push_back(tok);
        Ok(())
    }

    fn fetch_tag(&mut self) -> Result<(), ScanFault> {
        self.save_possible_simple_key()?;
        self.allow_simple_key = false;
        let tok = self.scan_tag()?;
        self.tokens.push_back(tok);
        Ok(())
    }

    fn fetch_literal(&mut self) -> Result<(), ScanFault> {
        self.fetch_block_scalar('|')
    }

    fn fetch_folded(&mut self) -> Result<(), ScanFault> {
        self.fetch_block_scalar('>')
    }

    fn fetch_block_scalar(&mut self, style: char) -> Result<(), ScanFault> {
        self.allow_simple_key = true;
        self.remove_possible_simple_key()?;
        let tok = self.scan_block_scalar(style)?;
        self.tokens.push_back(tok);
        Ok(())
    }

    fn fetch_single(&mut self) -> Result<(), ScanFault> {
        self.fetch_flow_scalar('\'')
    }

    fn fetch_double(&mut self) -> Result<(), ScanFault> {
        self.fetch_flow_scalar('"')
    }

    fn fetch_flow_scalar(&mut self, style: char) -> Result<(), ScanFault> {
        self.save_possible_simple_key()?;
        self.allow_simple_key = false;
        let tok = self.scan_flow_scalar(style)?;
        self.tokens.push_back(tok);
        Ok(())
    }

    fn fetch_plain(&mut self) -> Result<(), ScanFault> {
        self.save_possible_simple_key()?;
        self.allow_simple_key = false;
        let tok = self.scan_plain()?;
        self.tokens.push_back(tok);
        Ok(())
    }

    // -- checkers ------------------------------------------------------------

    fn check_directive(&self) -> bool {
        self.column == 0
    }

    fn check_document_start(&self) -> bool {
        if self.column != 0 {
            return false;
        }
        self.prefix(3) == [b'-' as u32, b'-' as u32, b'-' as u32]
            && is_blank_or_nul(self.peek(3))
    }

    fn check_document_end(&self) -> bool {
        if self.column != 0 {
            return false;
        }
        self.prefix(3) == [b'.' as u32, b'.' as u32, b'.' as u32]
            && is_blank_or_nul(self.peek(3))
    }

    fn check_block_entry(&self) -> bool {
        is_blank_or_nul(self.peek(1))
    }

    fn check_key(&self) -> bool {
        if self.flow_level != 0 {
            return true;
        }
        is_blank_or_nul(self.peek(1))
    }

    fn check_value(&self) -> bool {
        if self.flow_level != 0 {
            return true;
        }
        is_blank_or_nul(self.peek(1))
    }

    fn check_plain(&self) -> bool {
        let ch = self.peek(0);
        !matches!(
            ch,
            0 | 0x20 | 0x09 | 0x0D | 0x0A | 0x85 | 0x2028 | 0x2029 | 0x2D | 0x3F | 0x3A
            | 0x2C | 0x5B | 0x5D | 0x7B | 0x7D | 0x23 | 0x26 | 0x2A | 0x21 | 0x7C
            | 0x3E | 0x27 | 0x22 | 0x25 | 0x40 | 0x60
        ) || (!is_blank_or_nul(self.peek(1))
            && (ch == 0x2D || (self.flow_level == 0 && (ch == 0x3F || ch == 0x3A))))
    }

    // -- scanners -------------------------------------------------------------

    fn scan_to_next_token(&mut self) {
        if self.index == 0 && self.peek(0) == 0xFEFF {
            self.forward(1);
        }
        let mut found = false;
        while !found {
            while self.peek(0) == 0x20 {
                self.forward(1);
            }
            if self.peek(0) == b'#' as u32 {
                while !is_break_or_nul(self.peek(0)) {
                    self.forward(1);
                }
            }
            if !self.scan_line_break().is_empty() {
                if self.flow_level == 0 {
                    self.allow_simple_key = true;
                }
            } else {
                found = true;
            }
        }
    }

    fn scan_directive(&mut self) -> Result<Token, ScanFault> {
        let start_mark = self.get_mark();
        self.forward(1);
        let name = self.scan_directive_name(&start_mark)?;
        // NOTE: the original computes end_mark after the value but before
        // the ignored line; directives other than YAML/TAG set it right
        // after the name (before skipping to end of line).
        let (value, end_mark) = if name == "YAML" {
            let (major, minor) = self.scan_yaml_directive_value(&start_mark)?;
            (DirectiveValue::Yaml(major, minor), self.get_mark())
        } else if name == "TAG" {
            let (handle, prefix) = self.scan_tag_directive_value(&start_mark)?;
            (DirectiveValue::Tag(handle, prefix), self.get_mark())
        } else {
            let end_mark = self.get_mark();
            while !is_break_or_nul(self.peek(0)) {
                self.forward(1);
            }
            (DirectiveValue::Other, end_mark)
        };
        self.scan_directive_ignored_line(&start_mark)?;
        Ok(Token::Directive { name, value, start: start_mark, end: end_mark })
    }

    fn scan_directive_name(&mut self, start_mark: &MarkPos) -> Result<String, ScanFault> {
        let mut length = 0;
        while is_alphanum_dash_underscore(self.peek(length)) {
            length += 1;
        }
        if length == 0 {
            let ch = self.peek(0);
            let mark = self.get_mark();
            return Err(EngineError::new(
                Formatted::new(
                    "expected alphabetic or numeric character, but found %r",
                )
                .arg(ErrArg::Char(ch)),
                mark,
            )
            .ctx(
                Formatted::new("while scanning a directive"),
                *start_mark,
            )
            .into());
        }
        let value = super::to_rust_string(&self.prefix(length));
        self.forward(length);
        let ch = self.peek(0);
        if ch != 0 && ch != 0x20 && ch != 0x0D && ch != 0x0A && ch != 0x85 && ch != 0x2028 && ch != 0x2029
        {
            let mark = self.get_mark();
            return Err(EngineError::new(
                Formatted::new(
                    "expected alphabetic or numeric character, but found %r",
                )
                .arg(ErrArg::Char(ch)),
                mark,
            )
            .ctx(
                Formatted::new("while scanning a directive"),
                *start_mark,
            )
            .into());
        }
        Ok(value)
    }

    fn scan_yaml_directive_value(
        &mut self,
        start_mark: &MarkPos,
    ) -> Result<(String, String), ScanFault> {
        while self.peek(0) == 0x20 {
            self.forward(1);
        }
        let major = self.scan_yaml_directive_number(start_mark)?;
        if self.peek(0) != b'.' as u32 {
            let ch = self.peek(0);
            let mark = self.get_mark();
            return Err(EngineError::new(
                Formatted::new("expected a digit or '.', but found %r")
                    .arg(ErrArg::Char(ch)),
                mark,
            )
            .ctx(Formatted::new("while scanning a directive"), *start_mark)
            .into());
        }
        self.forward(1);
        let minor = self.scan_yaml_directive_number(start_mark)?;
        let ch = self.peek(0);
        if ch != 0 && ch != 0x20 && ch != 0x0D && ch != 0x0A && ch != 0x85 && ch != 0x2028 && ch != 0x2029
        {
            let mark = self.get_mark();
            return Err(EngineError::new(
                Formatted::new("expected a digit or ' ', but found %r")
                    .arg(ErrArg::Char(ch)),
                mark,
            )
            .ctx(Formatted::new("while scanning a directive"), *start_mark)
            .into());
        }
        Ok((major, minor))
    }

    fn scan_yaml_directive_number(&mut self, start_mark: &MarkPos) -> Result<String, ScanFault> {
        let ch = self.peek(0);
        if !is_digit(ch) {
            let mark = self.get_mark();
            return Err(EngineError::new(
                Formatted::new("expected a digit, but found %r").arg(ErrArg::Char(ch)),
                mark,
            )
            .ctx(Formatted::new("while scanning a directive"), *start_mark)
            .into());
        }
        let mut length = 0;
        while is_digit(self.peek(length)) {
            length += 1;
        }
        let value = super::to_rust_string(&self.prefix(length));
        self.forward(length);
        Ok(value)
    }

    fn scan_tag_directive_value(
        &mut self,
        start_mark: &MarkPos,
    ) -> Result<(String, String), ScanFault> {
        while self.peek(0) == 0x20 {
            self.forward(1);
        }
        let handle = self.scan_tag_directive_handle(start_mark)?;
        while self.peek(0) == 0x20 {
            self.forward(1);
        }
        let prefix = self.scan_tag_directive_prefix(start_mark)?;
        Ok((handle, prefix))
    }

    fn scan_tag_directive_handle(&mut self, start_mark: &MarkPos) -> Result<String, ScanFault> {
        let value = self.scan_tag_handle("directive", start_mark)?;
        let ch = self.peek(0);
        if ch != 0x20 {
            let mark = self.get_mark();
            return Err(EngineError::new(
                Formatted::new("expected ' ', but found %r").arg(ErrArg::Char(ch)),
                mark,
            )
            .ctx(Formatted::new("while scanning a directive"), *start_mark)
            .into());
        }
        Ok(value)
    }

    fn scan_tag_directive_prefix(&mut self, start_mark: &MarkPos) -> Result<String, ScanFault> {
        let value = self.scan_tag_uri("directive", start_mark)?;
        let ch = self.peek(0);
        if ch != 0 && ch != 0x20 && ch != 0x0D && ch != 0x0A && ch != 0x85 && ch != 0x2028 && ch != 0x2029
        {
            let mark = self.get_mark();
            return Err(EngineError::new(
                Formatted::new("expected ' ', but found %r").arg(ErrArg::Char(ch)),
                mark,
            )
            .ctx(Formatted::new("while scanning a directive"), *start_mark)
            .into());
        }
        Ok(super::to_rust_string(&value.0))
    }

    fn scan_directive_ignored_line(&mut self, start_mark: &MarkPos) -> Result<(), ScanFault> {
        while self.peek(0) == 0x20 {
            self.forward(1);
        }
        if self.peek(0) == b'#' as u32 {
            while !is_break_or_nul(self.peek(0)) {
                self.forward(1);
            }
        }
        let ch = self.peek(0);
        if !is_break_or_nul(ch) {
            let mark = self.get_mark();
            return Err(EngineError::new(
                Formatted::new("expected a comment or a line break, but found %r")
                    .arg(ErrArg::Char(ch)),
                mark,
            )
            .ctx(Formatted::new("while scanning a directive"), *start_mark)
            .into());
        }
        self.scan_line_break();
        Ok(())
    }

    fn scan_anchor(&mut self, alias: bool) -> Result<Token, ScanFault> {
        let start_mark = self.get_mark();
        let name = if alias { "alias" } else { "anchor" };
        self.forward(1);
        let mut length = 0;
        while is_anchor_char(self.peek(length)) {
            length += 1;
        }
        if length == 0 {
            let ch = self.peek(0);
            let mark = self.get_mark();
            return Err(EngineError::new(
                Formatted::new(
                    "expected alphabetic or numeric character, but found %r",
                )
                .arg(ErrArg::Char(ch)),
                mark,
            )
            .ctx(
                Formatted::new(&format!("while scanning an {name}")),
                start_mark,
            )
            .into());
        }
        let value = super::to_rust_string(&self.prefix(length));
        self.forward(length);
        let ch = self.peek(0);
        if ch != 0
            && ch != 0x20
            && ch != 0x09
            && ch != 0x0D
            && ch != 0x0A
            && ch != 0x85
            && ch != 0x2028
            && ch != 0x2029
            && ch != b'?' as u32
            && ch != b':' as u32
            && ch != b',' as u32
            && ch != b']' as u32
            && ch != b'}' as u32
            && ch != b'%' as u32
            && ch != b'@' as u32
            && ch != b'`' as u32
        {
            let mark = self.get_mark();
            return Err(EngineError::new(
                Formatted::new(
                    "expected alphabetic or numeric character, but found %r",
                )
                .arg(ErrArg::Char(ch)),
                mark,
            )
            .ctx(
                Formatted::new(&format!("while scanning an {name}")),
                start_mark,
            )
            .into());
        }
        let end_mark = self.get_mark();
        if alias {
            Ok(Token::Alias { value, start: start_mark, end: end_mark })
        } else {
            Ok(Token::Anchor { value, start: start_mark, end: end_mark })
        }
    }

    fn scan_tag(&mut self) -> Result<Token, ScanFault> {
        let start_mark = self.get_mark();
        let ch = self.peek(1);
        let (handle, suffix) = if ch == b'<' as u32 {
            self.forward(2);
            let suffix = self.scan_tag_uri("tag", &start_mark)?;
            if self.peek(0) != b'>' as u32 {
                let c = self.peek(0);
                let mark = self.get_mark();
                return Err(EngineError::new(
                    Formatted::new("expected '>', but found %r").arg(ErrArg::Char(c)),
                    mark,
                )
                .ctx(Formatted::new("while parsing a tag"), start_mark)
                .into());
            }
            self.forward(1);
            (None, suffix)
        } else if ch == 0 || ch == 0x20 || ch == 0x09 || is_break(ch) {
            self.forward(1);
            (None, YStr(vec![b'!' as u32]))
        } else {
            let mut length = 1;
            let mut use_handle = false;
            let mut c = ch;
            while c != 0 && c != 0x20 && c != 0x0D && c != 0x0A && c != 0x85 && c != 0x2028 && c != 0x2029
            {
                if c == b'!' as u32 {
                    use_handle = true;
                    break;
                }
                length += 1;
                c = self.peek(length);
            }
            let handle = if use_handle {
                Some(self.scan_tag_handle("tag", &start_mark)?)
            } else {
                self.forward(1);
                Some("!".to_string())
            };
            let suffix = self.scan_tag_uri("tag", &start_mark)?;
            (handle, suffix)
        };
        let ch = self.peek(0);
        if ch != 0 && ch != 0x20 && ch != 0x0D && ch != 0x0A && ch != 0x85 && ch != 0x2028 && ch != 0x2029
        {
            let mark = self.get_mark();
            return Err(EngineError::new(
                Formatted::new("expected ' ', but found %r").arg(ErrArg::Char(ch)),
                mark,
            )
            .ctx(Formatted::new("while scanning a tag"), start_mark)
            .into());
        }
        let end_mark = self.get_mark();
        Ok(Token::Tag { handle, suffix, start: start_mark, end: end_mark })
    }

    fn scan_block_scalar(&mut self, style: char) -> Result<Token, ScanFault> {
        let folded = style == '>';
        let mut chunks: Vec<u32> = Vec::new();
        let start_mark = self.get_mark();
        self.forward(1);
        let (chomping, increment) = self.scan_block_scalar_indicators(&start_mark)?;
        self.scan_block_scalar_ignored_line(&start_mark)?;
        let mut min_indent = self.indent + 1;
        if min_indent < 1 {
            min_indent = 1;
        }
        let indent: i64;
        let mut breaks: Vec<u32>;
        let mut end_mark: MarkPos;
        if let Some(inc) = increment {
            indent = min_indent + inc - 1;
            let (b, e) = self.scan_block_scalar_breaks(indent);
            breaks = b;
            end_mark = e;
        } else {
            let (b, max_indent, e) = self.scan_block_scalar_indentation();
            breaks = b;
            end_mark = e;
            indent = min_indent.max(max_indent);
        }
        let mut line_break: Vec<u32> = Vec::new();
        while self.column as i64 == indent && self.peek(0) != 0 {
            chunks.extend_from_slice(&breaks);
            let leading_non_space = self.peek(0) != 0x20 && self.peek(0) != 0x09;
            let mut length = 0;
            while !is_break_or_nul(self.peek(length)) {
                length += 1;
            }
            chunks.extend_from_slice(&self.prefix(length));
            self.forward(length);
            line_break = self.scan_line_break();
            let (b, e) = self.scan_block_scalar_breaks(indent);
            breaks = b;
            end_mark = e;
            if self.column as i64 == indent && self.peek(0) != 0 {
                if folded
                    && line_break == [0x0A]
                    && leading_non_space
                    && self.peek(0) != 0x20
                    && self.peek(0) != 0x09
                {
                    if breaks.is_empty() {
                        chunks.push(0x20);
                    }
                } else {
                    chunks.extend_from_slice(&line_break);
                }
            } else {
                break;
            }
        }
        if chomping != Some(false) {
            chunks.extend_from_slice(&line_break);
        }
        if chomping == Some(true) {
            chunks.extend_from_slice(&breaks);
        }
        Ok(Token::Scalar {
            value: YStr(chunks),
            plain: false,
            style: Some(style),
            start: start_mark,
            end: end_mark,
        })
    }

    fn scan_block_scalar_indicators(
        &mut self,
        start_mark: &MarkPos,
    ) -> Result<(Option<bool>, Option<i64>), ScanFault> {
        let mut chomping: Option<bool> = None;
        let mut increment: Option<i64> = None;
        let mut ch = self.peek(0);
        if ch == b'+' as u32 || ch == b'-' as u32 {
            chomping = Some(ch == b'+' as u32);
            self.forward(1);
            ch = self.peek(0);
            if (b'0' as u32) <= ch && ch <= (b'9' as u32) {
                let v = (ch - b'0' as u32) as i64;
                if v == 0 {
                    let mark = self.get_mark();
                    return Err(EngineError::new(
                        Formatted::new(
                            "expected indentation indicator in the range 1-9, but found 0",
                        ),
                        mark,
                    )
                    .ctx(
                        Formatted::new("while scanning a block scalar"),
                        *start_mark,
                    )
                    .into());
                }
                increment = Some(v);
                self.forward(1);
            }
        } else if (b'0' as u32) <= ch && ch <= (b'9' as u32) {
            let v = (ch - b'0' as u32) as i64;
            if v == 0 {
                let mark = self.get_mark();
                return Err(EngineError::new(
                    Formatted::new(
                        "expected indentation indicator in the range 1-9, but found 0",
                    ),
                    mark,
                )
                .ctx(
                    Formatted::new("while scanning a block scalar"),
                    *start_mark,
                )
                .into());
            }
            increment = Some(v);
            self.forward(1);
            ch = self.peek(0);
            if ch == b'+' as u32 || ch == b'-' as u32 {
                chomping = Some(ch == b'+' as u32);
                self.forward(1);
            }
        }
        ch = self.peek(0);
        if ch != 0 && ch != 0x20 && ch != 0x0D && ch != 0x0A && ch != 0x85 && ch != 0x2028 && ch != 0x2029
        {
            let mark = self.get_mark();
            return Err(EngineError::new(
                Formatted::new(
                    "expected chomping or indentation indicators, but found %r",
                )
                .arg(ErrArg::Char(ch)),
                mark,
            )
            .ctx(
                Formatted::new("while scanning a block scalar"),
                *start_mark,
            )
            .into());
        }
        Ok((chomping, increment))
    }

    fn scan_block_scalar_ignored_line(&mut self, start_mark: &MarkPos) -> Result<(), ScanFault> {
        while self.peek(0) == 0x20 {
            self.forward(1);
        }
        if self.peek(0) == b'#' as u32 {
            while !is_break_or_nul(self.peek(0)) {
                self.forward(1);
            }
        }
        let ch = self.peek(0);
        if !is_break_or_nul(ch) {
            let mark = self.get_mark();
            return Err(EngineError::new(
                Formatted::new("expected a comment or a line break, but found %r")
                    .arg(ErrArg::Char(ch)),
                mark,
            )
            .ctx(
                Formatted::new("while scanning a block scalar"),
                *start_mark,
            )
            .into());
        }
        self.scan_line_break();
        Ok(())
    }

    fn scan_block_scalar_indentation(&mut self) -> (Vec<u32>, i64, MarkPos) {
        let mut chunks: Vec<u32> = Vec::new();
        let mut max_indent: i64 = 0;
        let mut end_mark = self.get_mark();
        while self.peek(0) == 0x20 || is_break(self.peek(0)) {
            if self.peek(0) != 0x20 {
                chunks.extend_from_slice(&self.scan_line_break());
                end_mark = self.get_mark();
            } else {
                self.forward(1);
                if self.column as i64 > max_indent {
                    max_indent = self.column as i64;
                }
            }
        }
        (chunks, max_indent, end_mark)
    }

    fn scan_block_scalar_breaks(&mut self, indent: i64) -> (Vec<u32>, MarkPos) {
        let mut chunks: Vec<u32> = Vec::new();
        let mut end_mark = self.get_mark();
        while (self.column as i64) < indent && self.peek(0) == 0x20 {
            self.forward(1);
        }
        while is_break(self.peek(0)) {
            chunks.extend_from_slice(&self.scan_line_break());
            end_mark = self.get_mark();
            while (self.column as i64) < indent && self.peek(0) == 0x20 {
                self.forward(1);
            }
        }
        (chunks, end_mark)
    }

    fn scan_flow_scalar(&mut self, style: char) -> Result<Token, ScanFault> {
        let double = style == '"';
        let mut chunks: Vec<u32> = Vec::new();
        let start_mark = self.get_mark();
        let quote = self.peek(0);
        self.forward(1);
        chunks.extend_from_slice(&self.scan_flow_scalar_non_spaces(double, &start_mark)?);
        while self.peek(0) != quote {
            chunks.extend_from_slice(&self.scan_flow_scalar_spaces(double, &start_mark)?);
            chunks.extend_from_slice(&self.scan_flow_scalar_non_spaces(double, &start_mark)?);
        }
        self.forward(1);
        let end_mark = self.get_mark();
        Ok(Token::Scalar {
            value: YStr(chunks),
            plain: false,
            style: Some(style),
            start: start_mark,
            end: end_mark,
        })
    }

    fn scan_flow_scalar_non_spaces(
        &mut self,
        double: bool,
        start_mark: &MarkPos,
    ) -> Result<Vec<u32>, ScanFault> {
        let mut chunks: Vec<u32> = Vec::new();
        loop {
            let mut length = 0;
            while !matches!(
                self.peek(length),
                0x27 | 0x22 | 0x5C | 0 | 0x20 | 0x09 | 0x0D | 0x0A | 0x85 | 0x2028 | 0x2029
            ) {
                length += 1;
            }
            if length > 0 {
                chunks.extend_from_slice(&self.prefix(length));
                self.forward(length);
            }
            let ch = self.peek(0);
            if !double && ch == 0x27 && self.peek(1) == 0x27 {
                chunks.push(0x27);
                self.forward(2);
            } else if (double && ch == 0x27) || (!double && (ch == 0x22 || ch == 0x5C)) {
                chunks.push(ch);
                self.forward(1);
            } else if double && ch == 0x5C {
                self.forward(1);
                let ch = self.peek(0);
                if let Some(rep) = escape_replacement(ch) {
                    chunks.push(rep);
                    self.forward(1);
                } else if let Some(length) = escape_code_len(ch) {
                    self.forward(1);
                    for k in 0..length {
                        if !is_hex(self.peek(k)) {
                            let c = self.peek(k);
                            let mark = self.get_mark();
                            return Err(EngineError::new(
                                Formatted::new(
                                    "expected escape sequence of %d hexadecimal numbers, but found %r",
                                )
                                .arg(ErrArg::Int(length as i64))
                                .arg(ErrArg::Char(c)),
                                mark,
                            )
                            .ctx(
                                Formatted::new("while scanning a double-quoted scalar"),
                                *start_mark,
                            )
                            .into());
                        }
                    }
                    let hex = super::to_rust_string(&self.prefix(length));
                    let code = u32::from_str_radix(&hex, 16).unwrap_or(0);
                    chunks.push(code);
                    self.forward(length);
                } else if is_break(ch) {
                    self.scan_line_break();
                    chunks.extend_from_slice(&self.scan_flow_scalar_breaks(double, start_mark)?);
                } else {
                    let mark = self.get_mark();
                    return Err(EngineError::new(
                        Formatted::new("found unknown escape character %r")
                            .arg(ErrArg::Char(ch)),
                        mark,
                    )
                    .ctx(
                        Formatted::new("while scanning a double-quoted scalar"),
                        *start_mark,
                    )
                    .into());
                }
            } else {
                return Ok(chunks);
            }
        }
    }

    fn scan_flow_scalar_spaces(
        &mut self,
        double: bool,
        start_mark: &MarkPos,
    ) -> Result<Vec<u32>, ScanFault> {
        let mut chunks: Vec<u32> = Vec::new();
        let mut length = 0;
        while self.peek(length) == 0x20 || self.peek(length) == 0x09 {
            length += 1;
        }
        let whitespaces = self.prefix(length);
        self.forward(length);
        let ch = self.peek(0);
        if ch == 0 {
            let mark = self.get_mark();
            return Err(EngineError::new(
                Formatted::new("found unexpected end of stream"),
                mark,
            )
            .ctx(
                Formatted::new("while scanning a quoted scalar"),
                *start_mark,
            )
            .into());
        } else if is_break(ch) {
            let line_break = self.scan_line_break();
            let breaks = self.scan_flow_scalar_breaks(double, start_mark)?;
            if line_break != [0x0A] {
                chunks.extend_from_slice(&line_break);
            } else if breaks.is_empty() {
                chunks.push(0x20);
            }
            chunks.extend_from_slice(&breaks);
        } else {
            chunks.extend_from_slice(&whitespaces);
        }
        Ok(chunks)
    }

    fn scan_flow_scalar_breaks(
        &mut self,
        _double: bool,
        start_mark: &MarkPos,
    ) -> Result<Vec<u32>, ScanFault> {
        let mut chunks: Vec<u32> = Vec::new();
        loop {
            let prefix = self.prefix(3);
            if (prefix == [0x2D, 0x2D, 0x2D] || prefix == [0x2E, 0x2E, 0x2E])
                && (self.peek(3) == 0
                    || self.peek(3) == 0x20
                    || self.peek(3) == 0x09
                    || is_break(self.peek(3)))
            {
                let mark = self.get_mark();
                return Err(EngineError::new(
                    Formatted::new("found unexpected document separator"),
                    mark,
                )
                .ctx(
                    Formatted::new("while scanning a quoted scalar"),
                    *start_mark,
                )
                .into());
            }
            while self.peek(0) == 0x20 || self.peek(0) == 0x09 {
                self.forward(1);
            }
            if is_break(self.peek(0)) {
                chunks.extend_from_slice(&self.scan_line_break());
            } else {
                return Ok(chunks);
            }
        }
    }

    fn scan_plain(&mut self) -> Result<Token, ScanFault> {
        let mut chunks: Vec<u32> = Vec::new();
        let start_mark = self.get_mark();
        let mut end_mark = start_mark;
        let indent = self.indent + 1;
        let mut spaces: Vec<u32> = Vec::new();
        loop {
            if self.peek(0) == b'#' as u32 {
                break;
            }
            let mut length = 0;
            loop {
                let ch = self.peek(length);
                let mut stop = ch == 0 || ch == 0x20 || ch == 0x09 || is_break(ch);
                if !stop
                    && ch == b':' as u32
                    && {
                        let n = self.peek(length + 1);
                        n == 0 || n == 0x20 || n == 0x09 || is_break(n)
                            || (self.flow_level != 0
                                && (n == b',' as u32
                                    || n == b'[' as u32
                                    || n == b']' as u32
                                    || n == b'{' as u32
                                    || n == b'}' as u32))
                    }
                {
                    stop = true;
                }
                if !stop
                    && self.flow_level != 0
                    && (ch == b',' as u32
                        || ch == b'?' as u32
                        || ch == b'[' as u32
                        || ch == b']' as u32
                        || ch == b'{' as u32
                        || ch == b'}' as u32)
                {
                    stop = true;
                }
                if stop {
                    break;
                }
                length += 1;
            }
            if length == 0 {
                break;
            }
            self.allow_simple_key = false;
            chunks.extend_from_slice(&spaces);
            chunks.extend_from_slice(&self.prefix(length));
            self.forward(length);
            end_mark = self.get_mark();
            spaces = self.scan_plain_spaces(indent, &start_mark)?;
            if spaces.is_empty()
                || self.peek(0) == b'#' as u32
                || (self.flow_level == 0 && (self.column as i64) < indent)
            {
                break;
            }
        }
        Ok(Token::Scalar {
            value: YStr(chunks),
            plain: true,
            style: None,
            start: start_mark,
            end: end_mark,
        })
    }

    fn scan_plain_spaces(
        &mut self,
        indent: i64,
        start_mark: &MarkPos,
    ) -> Result<Vec<u32>, ScanFault> {
        let mut chunks: Vec<u32> = Vec::new();
        let mut length = 0;
        while self.peek(length) == 0x20 {
            length += 1;
        }
        let whitespaces = self.prefix(length);
        self.forward(length);
        let ch = self.peek(0);
        if is_break(ch) {
            let line_break = self.scan_line_break();
            self.allow_simple_key = true;
            let prefix = self.prefix(3);
            if (prefix == [0x2D, 0x2D, 0x2D] || prefix == [0x2E, 0x2E, 0x2E])
                && (self.peek(3) == 0
                    || self.peek(3) == 0x20
                    || self.peek(3) == 0x09
                    || is_break(self.peek(3)))
            {
                return Ok(Vec::new());
            }
            let mut breaks: Vec<u32> = Vec::new();
            while self.peek(0) == 0x20 || is_break(self.peek(0)) {
                if self.peek(0) == 0x20 {
                    self.forward(1);
                } else {
                    breaks.extend_from_slice(&self.scan_line_break());
                    let prefix = self.prefix(3);
                    if (prefix == [0x2D, 0x2D, 0x2D] || prefix == [0x2E, 0x2E, 0x2E])
                        && (self.peek(3) == 0
                            || self.peek(3) == 0x20
                            || self.peek(3) == 0x09
                            || is_break(self.peek(3)))
                    {
                        return Ok(Vec::new());
                    }
                }
            }
            if line_break != [0x0A] {
                chunks.extend_from_slice(&line_break);
            } else if breaks.is_empty() {
                chunks.push(0x20);
            }
            chunks.extend_from_slice(&breaks);
        } else if !whitespaces.is_empty() {
            chunks.extend_from_slice(&whitespaces);
        }
        let _ = (indent, start_mark);
        Ok(chunks)
    }

    fn scan_tag_handle(&mut self, name: &str, start_mark: &MarkPos) -> Result<String, ScanFault> {
        let ch = self.peek(0);
        if ch != b'!' as u32 {
            let mark = self.get_mark();
            return Err(EngineError::new(
                Formatted::new("expected '!', but found %r").arg(ErrArg::Char(ch)),
                mark,
            )
            .ctx(
                Formatted::new(&format!("while scanning a {name}")),
                *start_mark,
            )
            .into());
        }
        let mut length = 1;
        let mut ch = self.peek(length);
        if ch != 0x20 {
            while is_alphanum_dash_underscore(ch) {
                length += 1;
                ch = self.peek(length);
            }
            if ch != b'!' as u32 {
                self.forward(length);
                let mark = self.get_mark();
                return Err(EngineError::new(
                    Formatted::new("expected '!', but found %r").arg(ErrArg::Char(ch)),
                    mark,
                )
                .ctx(
                    Formatted::new(&format!("while scanning a {name}")),
                    *start_mark,
                )
                .into());
            }
            length += 1;
        }
        let value = super::to_rust_string(&self.prefix(length));
        self.forward(length);
        Ok(value)
    }

    fn scan_tag_uri(&mut self, name: &str, start_mark: &MarkPos) -> Result<YStr, ScanFault> {
        let mut chunks: Vec<u32> = Vec::new();
        let mut length = 0;
        let mut ch = self.peek(length);
        while is_uri_char(ch) {
            if ch == b'%' as u32 {
                chunks.extend_from_slice(&self.prefix(length));
                self.forward(length);
                length = 0;
                chunks.extend_from_slice(&self.scan_uri_escapes(name, start_mark)?);
            } else {
                length += 1;
            }
            ch = self.peek(length);
        }
        if length > 0 {
            chunks.extend_from_slice(&self.prefix(length));
            self.forward(length);
        }
        if chunks.is_empty() {
            let mark = self.get_mark();
            return Err(EngineError::new(
                Formatted::new("expected URI, but found %r").arg(ErrArg::Char(ch)),
                mark,
            )
            .ctx(
                Formatted::new(&format!("while parsing a {name}")),
                *start_mark,
            )
            .into());
        }
        Ok(YStr(chunks))
    }

    fn scan_uri_escapes(&mut self, name: &str, start_mark: &MarkPos) -> Result<Vec<u32>, ScanFault> {
        let mut codes: Vec<u8> = Vec::new();
        let mark = self.get_mark();
        while self.peek(0) == b'%' as u32 {
            self.forward(1);
            for k in 0..2 {
                if !is_hex(self.peek(k)) {
                    let c = self.peek(k);
                    let m = self.get_mark();
                    return Err(EngineError::new(
                        Formatted::new(
                            "expected URI escape sequence of 2 hexadecimal numbers, but found %r",
                        )
                        .arg(ErrArg::Char(c)),
                        m,
                    )
                    .ctx(
                        Formatted::new(&format!("while scanning a {name}")),
                        *start_mark,
                    )
                    .into());
                }
            }
            let hex = super::to_rust_string(&self.prefix(2));
            codes.push(u8::from_str_radix(&hex, 16).unwrap_or(0));
            self.forward(2);
        }
        match std::str::from_utf8(&codes) {
            Ok(s) => Ok(s.chars().map(|c| c as u32).collect()),
            Err(_) => Err(ScanFault::UriDecode(UriDecodeFault {
                codes,
                name: name.to_string(),
                start_mark: *start_mark,
                mark,
            })),
        }
    }

    fn scan_line_break(&mut self) -> Vec<u32> {
        let ch = self.peek(0);
        if ch == 0x0D || ch == 0x0A || ch == 0x85 {
            if self.prefix(2) == [0x0D, 0x0A] {
                self.forward(2);
            } else {
                self.forward(1);
            }
            vec![0x0A]
        } else if ch == 0x2028 || ch == 0x2029 {
            self.forward(1);
            vec![ch]
        } else {
            Vec::new()
        }
    }
}
