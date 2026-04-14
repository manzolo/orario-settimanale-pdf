#!/bin/bash
set -e

CSV_FILE="${1:-orario.csv}"
BASE="${CSV_FILE%.csv}"
HTML_FILE="${BASE}.html"
OUTPUT_FILE="${BASE}.pdf"

echo "→ Generazione HTML da ${CSV_FILE}..."
python3 genera_html.py "$CSV_FILE"

echo "→ Generazione PDF con WeasyPrint..."
python3 -m weasyprint "$HTML_FILE" "$OUTPUT_FILE"

echo "✓ PDF generato: $OUTPUT_FILE ($(du -h "$OUTPUT_FILE" | cut -f1))"
