#!/bin/bash
#
# Extract summary tables and HAR text from remaining approved HAR PDFs
#

set -e  # Exit on error

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
DOCS_DIR="/home/finch/repos/hasadmin/docs"
OUTPUT_DIR="/tmp/har_extractions"
TIMEOUT=180

mkdir -p "$OUTPUT_DIR"

# Already processed in Phase 1
PROCESSED=(14157 14216 14541 14936 8845 17175 17642 17810)

is_processed() {
    local id=$1
    for processed_id in "${PROCESSED[@]}"; do
        [[ "$id" == "$processed_id" ]] && return 0
    done
    return 1
}

extract_id() {
    local filename=$1
    echo "$filename" | sed 's/.*HAS-.*-25-//' | sed 's/.pdf//'
}

extract_pdf() {
    local pdf_path=$1
    local assessment_id=$2

    echo -e "${YELLOW}[Processing]${NC} Assessment $assessment_id"

    local prompt="@${pdf_path} Extract the following from this HAR document:

1. SUMMARY TABLE: Extract the assessment summary table with Assessment ID, Category, Feature Type, Location, and all hazard assessment columns.

2. HAR TEXT: Extract the complete EXPLANATION AND RECOMMENDATION section text verbatim.

Separate the two sections with a line containing only: ===HAR_TEXT==="

    if timeout "$TIMEOUT" gemini -p "$prompt" 2>&1 \
        | grep -v "^\[" | grep -v "^Loaded" \
        > "${OUTPUT_DIR}/har_${assessment_id}_full.txt"; then

        if grep -q "===HAR_TEXT===" "${OUTPUT_DIR}/har_${assessment_id}_full.txt"; then
            sed '/===HAR_TEXT===/q' "${OUTPUT_DIR}/har_${assessment_id}_full.txt" \
                | head -n -1 > "${OUTPUT_DIR}/har_${assessment_id}_summary.txt"

            sed -n '/===HAR_TEXT===/,$p' "${OUTPUT_DIR}/har_${assessment_id}_full.txt" \
                | tail -n +2 > "${OUTPUT_DIR}/har_${assessment_id}_har.txt"

            echo -e "${GREEN}[✓ Success]${NC} Assessment $assessment_id"
        else
            cp "${OUTPUT_DIR}/har_${assessment_id}_full.txt" \
               "${OUTPUT_DIR}/har_${assessment_id}_summary.txt"
            echo -e "${YELLOW}[⚠ Warning]${NC} No separator found"
        fi
        return 0
    else
        echo -e "${RED}[✗ Failed]${NC} Assessment $assessment_id"
        return 1
    fi
}

echo "========================================="
echo "HAR PDF Extraction Script"
echo "========================================="

mapfile -t PDF_FILES < <(
    find "$DOCS_DIR" -maxdepth 1 -type f -name 'HAS-*-25-*.pdf' -print | sort
)

if [[ ${#PDF_FILES[@]} -eq 0 ]]; then
    echo -e "${RED}Error: No HAR PDFs found${NC}"
    exit 1
fi

TOTAL=0
SKIPPED=0
SUCCESS=0
FAILED=0

for pdf_file in "${PDF_FILES[@]}"; do
    assessment_id=$(extract_id "$(basename "$pdf_file")")
    ((TOTAL++))

    if is_processed "$assessment_id"; then
        echo -e "${YELLOW}[Skipped]${NC} Assessment $assessment_id"
        ((SKIPPED++))
        continue
    fi

    if extract_pdf "$pdf_file" "$assessment_id"; then
        ((SUCCESS++))
    else
        ((FAILED++))
    fi

    sleep 2
done

echo ""
echo "Extraction Summary"
echo "------------------"
echo "Total: $TOTAL"
echo "Skipped: $SKIPPED"
echo -e "Success: ${GREEN}$SUCCESS${NC}"
echo -e "Failed: ${RED}$FAILED${NC}"

if [[ $SUCCESS -gt 0 ]]; then
    echo ""
    echo "Extracted assessments:"
    find "$OUTPUT_DIR" -maxdepth 1 -type f -name 'har_*_summary.txt' -print \
      | sed 's|.*/har_|  |' \
      | sed 's/_summary.txt//' \
      | sort -n
fi

[[ $FAILED -gt 0 ]] && exit 1
echo -e "${GREEN}All extractions completed successfully!${NC}"
