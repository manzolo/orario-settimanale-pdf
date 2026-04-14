#!/bin/bash
set -e

OUTPUT_FILE="orario.pdf"

echo "→ Generazione HTML da orario.csv..."
python3 genera_html.py orario.csv

echo "→ Generazione PDF con WeasyPrint..."
python3 -m weasyprint orario.html "$OUTPUT_FILE"

echo "✓ PDF generato: $OUTPUT_FILE ($(du -h "$OUTPUT_FILE" | cut -f1))"
