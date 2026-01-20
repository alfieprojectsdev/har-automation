# HAR PDF Extraction Scripts

Two bash scripts for extracting data from the remaining 20 approved HAR PDFs.

---

## Quick Start

### Option 1: Enhanced Extraction (Recommended)

Extracts **both** summary tables and actual HAR text for validation:

```bash
cd /home/finch/repos/hasadmin/har-automation
chmod +x extract_remaining_hars.sh
./extract_remaining_hars.sh
```

**Output:**
- `/tmp/har_extractions/har_{ID}_summary.txt` - Summary table
- `/tmp/har_extractions/har_{ID}_har.txt` - Actual HAR explanation text
- `/tmp/har_extractions/har_{ID}_full.txt` - Raw Gemini output

**Time:** ~15-20 minutes (20 PDFs × 30-60s each)

### Option 2: Simple Extraction (Faster)

Extracts **only** summary tables:

```bash
cd /home/finch/repos/hasadmin/har-automation
chmod +x extract_summaries_simple.sh
./extract_summaries_simple.sh
```

**Output:**
- `/tmp/har_{ID}_summary.txt` - Summary table only

**Time:** ~10-15 minutes (20 PDFs × 30-45s each)

---

## What Gets Extracted

### Already Processed (8 PDFs - will be skipped)

These were extracted in Phase 1 validation:
- 14157 (Feb, Kanlaon)
- 14216 (Feb, Taal)
- 14541 (Mar, Camiguin de Babuyanes)
- 14936 (May, Hibok-hibok)
- 8845 (Jul, Hibok-hibok)
- 17175 (Jul, Banahaw)
- 17642 (Aug, Pinatubo)
- 17810 (Sep, Earthquake-only)

### Remaining to Extract (20 PDFs)

| ID | Month | Status |
|----|-------|--------|
| 17176 | Jul | Pending |
| 17181 | Jul | Pending |
| 17180 | Jul | Pending |
| 17023 | Jun | Pending |
| 17014 | Jun | Pending |
| 17020 | Jun | Pending |
| 14959 | May | Pending |
| 14921 | May | Pending |
| 16788 | May | Pending |
| 14448 | Mar | Pending |
| 14563 | Mar | Pending |
| 14341 | Feb | Pending |
| 14174 | Feb | Pending |
| 14165 | Feb | Pending |
| 17760 | Sep | Pending |
| 17768 | Sep | Pending |
| 17635 | Aug | Pending |
| 17633 | Aug | Pending |
| 17283 | Jul | Pending |
| 17119 | Jul | Pending |

---

## Enhanced Extraction Benefits

### Why Extract Both Summary Table AND HAR Text?

**Summary table** = Input data for our pipeline
**HAR text** = Expected output to validate against

Having both allows us to:

1. **Generate HAR** from summary table using our pipeline
2. **Compare** our generated HAR vs. approved PHIVOLCS HAR
3. **Calculate quality score** for each assessment
4. **Identify gaps** in specific volcano/hazard combinations
5. **Validate improvements** after implementing Phase 2 volcano hazards

### Example Workflow with Enhanced Extraction

```bash
# 1. Extract all data
./extract_remaining_hars.sh

# 2. Check what volcanoes we got
grep -h "Nearest Active Volcano" /tmp/har_extractions/har_*_summary.txt | \
  sed 's/.*of //' | sed 's/ Volcano//' | sort | uniq -c

# 3. Validate a specific assessment
cd /home/finch/repos/hasadmin/har-automation
source .venv/bin/activate

# Add extracted data to validate_manual_extraction.py
# Run validation
python3 validate_manual_extraction.py 17176

# 4. Compare with approved HAR
diff <(cat har_17176_*.txt) <(cat /tmp/har_extractions/har_17176_har.txt)
```

---

## Troubleshooting

### Script fails with "Permission denied"

```bash
chmod +x extract_remaining_hars.sh
chmod +x extract_summaries_simple.sh
```

### Gemini timeouts

Increase timeout in script:
```bash
# Edit the script
nano extract_remaining_hars.sh

# Change this line:
TIMEOUT=180

# To:
TIMEOUT=300  # 5 minutes
```

### Rate limiting

The script includes 2-second pauses between requests. If you still hit rate limits:
```bash
# Edit the script and increase sleep time:
sleep 5  # Instead of sleep 2
```

### Missing PDFs

```bash
# Check what PDFs are in docs directory
ls -1 /home/finch/repos/hasadmin/docs/HAS-*-25-*.pdf | wc -l

# Should be 28 total
```

### Verify extractions succeeded

```bash
# Count extracted files
ls /tmp/har_extractions/har_*_summary.txt | wc -l
# Should be 20

# Check file sizes (should all be > 0)
ls -lh /tmp/har_extractions/har_*_summary.txt
```

---

## Advanced Usage

### Extract specific assessments only

```bash
# Edit extract_summaries_simple.sh
# Change REMAINING variable to only include specific IDs:
REMAINING="17176 17181"  # Only these two
```

### Process in parallel (faster but more resource-intensive)

```bash
# Extract 4 PDFs at a time
cd /home/finch/repos/hasadmin/docs

for id in 17176 17181 17180 17023; do
    PDF=$(ls HAS-*-25-${id}.pdf 2>/dev/null | head -1)
    (timeout 180 gemini -p "@${PDF} Extract summary table..." > /tmp/har_${id}_summary.txt 2>&1) &
done

wait  # Wait for all background jobs
```

### Re-extract with different prompt

If default extraction quality is poor, try this enhanced prompt:

```bash
gemini -p "@HAS-Feb-25-14216.pdf

You are extracting data from a PHIVOLCS Hazard Assessment Report PDF.

Task 1: Extract the assessment summary table that appears near the top of the document.
- Include ALL columns: Assessment ID, Category, Feature Type, Location, Ground Rupture, Liquefaction, Earthquake-Induced Landslide, Tsunami, Nearest Active Volcano, Lahar, Pyroclastic Flow, Lava Flow, Base Surge, Ballistic Projectiles
- Format as tab-separated values
- Keep exact status text (e.g., 'Safe; Approximately 683 meters west of...')

Task 2: Extract the EXPLANATION AND RECOMMENDATION section verbatim.
- Start from 'EXPLANATION AND RECOMMENDATION' header
- Include all numbered points
- Stop before 'This assessment supersedes'

Separate Task 1 and Task 2 outputs with: ===HAR_TEXT===" > /tmp/test.txt
```

---

## Next Steps After Extraction

1. **Review extracted data quality**
   ```bash
   head -20 /tmp/har_extractions/har_17176_summary.txt
   ```

2. **Identify volcano types in new samples**
   ```bash
   grep -i "taal\|mayon\|pinatubo" /tmp/har_extractions/har_*_summary.txt
   ```

3. **Add high-value samples to validation script**
   - Prioritize: Taal with prone hazards, Pinatubo with zones, Mayon with prone levels
   - Add to `validate_manual_extraction.py`

4. **Run validation after Phase 2 implementation**
   - Test proximity-hazard volcano improvements
   - Measure quality score changes

---

## Script Maintenance

### Adding new PDFs

If new approved HARs are added:

1. Update `PROCESSED` array in scripts
2. Add new IDs to extraction list
3. Re-run extraction

### Cleaning up old extractions

```bash
# Remove all extracted files
rm -rf /tmp/har_extractions/
rm /tmp/har_*_summary.txt

# Or remove specific assessment
rm /tmp/har_extractions/har_17176_*
```

---

**Created:** 2025-12-18
**Purpose:** Batch extraction for Phase 1+ validation testing
**Status:** Ready to use
