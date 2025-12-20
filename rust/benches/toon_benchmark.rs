use _toonverter_core::encoder::encode_toon_root;
use _toonverter_core::ir::ToonValue;
use _toonverter_core::lexer::ToonLexer;
use _toonverter_core::parser::ToonParser;
use criterion::{black_box, criterion_group, criterion_main, Criterion};
use indexmap::IndexMap;

fn generate_large_toon(size: usize) -> String {
    let mut s = String::new();
    s.push_str("root:\n");
    for i in 0..size {
        s.push_str(&format!("  item_{}:\n", i));
        s.push_str(&format!("    name: \"Item {}\"\n", i));
        s.push_str(&format!("    value: {}\n", i * 10));
        s.push_str("    tags:\n");
        s.push_str("      - tag1\n");
        s.push_str("      - tag2\n");
    }
    s
}

fn generate_large_ir(size: usize) -> ToonValue {
    let mut root_map = IndexMap::new();
    for i in 0..size {
        let mut item_map = IndexMap::new();
        item_map.insert("name".to_string(), ToonValue::String(format!("Item {}", i)));
        item_map.insert("value".to_string(), ToonValue::Integer((i * 10) as i64));
        item_map.insert(
            "tags".to_string(),
            ToonValue::List(vec![
                ToonValue::String("tag1".to_string()),
                ToonValue::String("tag2".to_string()),
            ]),
        );
        root_map.insert(format!("item_{}", i), ToonValue::Dict(item_map));
    }
    ToonValue::Dict(root_map)
}

fn bench_lexer(c: &mut Criterion) {
    let mut group = c.benchmark_group("lexer");
    for size in [10, 100, 1000, 10000].iter() {
        let input = generate_large_toon(*size);
        group.bench_with_input(
            criterion::BenchmarkId::new("items", size),
            &input,
            |b, input| {
                b.iter(|| {
                    let lexer = ToonLexer::new(black_box(input), 2);
                    for _ in lexer {}
                })
            },
        );
    }
    group.finish();
}

fn bench_parser(c: &mut Criterion) {
    let mut group = c.benchmark_group("parser");
    for size in [10, 100, 1000, 10000].iter() {
        let input = generate_large_toon(*size);
        group.bench_with_input(
            criterion::BenchmarkId::new("items", size),
            &input,
            |b, input| {
                b.iter(|| {
                    let lexer = ToonLexer::new(black_box(input), 2);
                    let mut parser = ToonParser::new(lexer);
                    let _ = parser.parse_root().unwrap();
                })
            },
        );
    }
    group.finish();
}

fn bench_encoder(c: &mut Criterion) {
    let mut group = c.benchmark_group("encoder");
    for size in [10, 100, 1000, 10000].iter() {
        let ir = generate_large_ir(*size);
        group.bench_with_input(
            criterion::BenchmarkId::new("items", size),
            &ir,
            |b, ir_val| {
                b.iter(|| {
                    let _ = encode_toon_root(black_box(ir_val), 2, ",");
                })
            },
        );
    }
    group.finish();
}

criterion_group!(benches, bench_lexer, bench_parser, bench_encoder);
criterion_main!(benches);
