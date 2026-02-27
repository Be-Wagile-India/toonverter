#![no_main]
use libfuzzer_sys::fuzz_target;
use _toonverter_core::lexer::ToonLexer;
use _toonverter_core::parser::ToonParser;

fuzz_target!(|data: &[u8]| {
    if let Ok(s) = std::str::from_utf8(data) {
        let lexer = ToonLexer::new(s, 2);
        let mut parser = ToonParser::new(lexer);
        let _ = parser.parse_root();
    }
});
