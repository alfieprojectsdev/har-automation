#!/bin/bash
#
# Simple version: Extract ONLY summary tables from remaining HAR PDFs
# Use this if the enhanced version fails or is too slow
#

set -e

# Remaining IDs to process
REMAINING="17176 17181 17180 17023 17014 17020 14959 14921 16788 14448 14563 14341 14174 14165 17760 17768 17635 17633 17283 17119"

DOCS_DIR="/home/finch/repos/hasadmin/docs"
OUTPUT_DIR="/tmp"

cd "$DOCS_DIR"

echo "Extracting summary tables from 20 remaining HAR PDFs..."
echo "Output: $OUTPUT_DIR/har_*_summary.txt"
echo ""

COUNT=0
TOTAL=20

for id in $REMAINING; do
    # Find the PDF file (first match only)
    PDF=$(find . -maxdepth 1 -type f -name "HAS-*-25-${id}.pdf" -print -quit)

    if [[ -z "$PDF" ]]; then
        echo "⚠ Warning: PDF not found for assessment $id"
        continue
    fi

    ((COUNT++))
    echo "[$COUNT/$TOTAL] Extracting $id from ${PDF#./}..."

    if timeout 180 gemini -p "@${PDF#./} Extract only the summary table with Assessment ID, Category, Feature Type, Location, and all hazard assessment columns. Format as tab-separated text." \
        2>&1 | grep -v "^\[" | grep -v "^Loaded" \
        > "$OUTPUT_DIR/har_${id}_summary.txt"; then

        echo "  ✓ Success: $OUTPUT_DIR/har_${id}_summary.txt"
    else
        echo "  ✗ Failed or timeout"
    fi

    # Pause between requests
    sleep 2
done

echo ""
echo "Extraction complete!"
echo "Check $OUTPUT_DIR/har_*_summary.txt for results"
echo ""
echo "To verify:"
echo "  ls -lh $OUTPUT_DIR/har_*_summary.txt | wc -l"
