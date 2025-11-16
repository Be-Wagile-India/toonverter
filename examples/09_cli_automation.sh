#!/bin/bash
# Example 9: CLI Automation Scripts
#
# Demonstrates:
# - Batch file conversion
# - Automated token analysis
# - CI/CD integration
# - Pipeline processing

echo "=================================================="
echo "Example 9: CLI Automation Scripts"
echo "=================================================="

# Create sample data files
mkdir -p /tmp/toon_cli_demo
cd /tmp/toon_cli_demo

# Sample JSON data
cat > users.json << 'EOF'
{
  "users": [
    {"id": 1, "name": "Alice", "age": 30},
    {"id": 2, "name": "Bob", "age": 25},
    {"id": 3, "name": "Charlie", "age": 35}
  ]
}
EOF

cat > products.json << 'EOF'
{
  "products": [
    {"id": 101, "name": "Widget", "price": 19.99},
    {"id": 102, "name": "Gadget", "price": 29.99}
  ]
}
EOF

echo -e "\n--- Batch Conversion ---"
echo "Converting all JSON files to TOON..."

for file in *.json; do
    base=$(basename "$file" .json)
    echo "  $file -> ${base}.toon"
    toonverter convert "$file" "${base}.toon" --from json --to toon
done

echo -e "\n--- Token Analysis ---"
echo "Analyzing token usage..."

for file in *.json; do
    echo -e "\nAnalyzing $file:"
    toonverter analyze "$file" --compare json toon yaml
done

echo -e "\n--- Format Listing ---"
toonverter formats

echo -e "\n--- File Comparison ---"
echo "File sizes:"
for json_file in *.json; do
    toon_file="${json_file%.json}.toon"
    json_size=$(stat -f%z "$json_file" 2>/dev/null || stat -c%s "$json_file")
    toon_size=$(stat -f%z "$toon_file" 2>/dev/null || stat -c%s "$toon_file")
    savings=$(( (json_size - toon_size) * 100 / json_size ))
    echo "  $json_file: $json_size bytes -> $toon_size bytes ($savings% savings)"
done

echo -e "\n--- Cleanup ---"
cd -
rm -rf /tmp/toon_cli_demo
echo "Demo files cleaned up"
