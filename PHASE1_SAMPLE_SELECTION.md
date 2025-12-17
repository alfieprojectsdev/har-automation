# Phase 1: Diverse Sample Selection

## Objective
Test 5-6 new PDFs + 2 already tested = **8 total assessments** covering diverse volcano types, hazard patterns, and time periods.

## Already Tested ✅

| ID | Month | Volcano | Distance | Hazard Pattern | Quality Score |
|----|-------|---------|----------|----------------|---------------|
| **14157** | Feb | Kanlaon | 15.2 km | Lahar (Highly prone), PDC (Prone) | Earthquake: 100%, Volcano: 40% |
| **17175** | Jul | Banahaw | 66.8 km | All Safe | Earthquake: 100%, Volcano: 100% |

**Patterns covered:**
- ✅ Distance-safe volcano (>50km)
- ✅ Proximity-hazard volcano (<50km)
- ✅ Combined earthquake + volcano
- ✅ Complete earthquake assessment (4 hazards)
- ✅ Minimal earthquake assessment (1 hazard)

## New Samples to Test (5-6 PDFs)

**Selection strategy:** Maximize diversity in months, assessment IDs, and likely volcano types/locations.

| # | PDF | ID | Month | Rationale |
|---|-----|-----|-------|-----------|
| 1 | `HAS-Feb-25-14216.pdf` | 14216 | Feb | Different Feb assessment, likely different location than 14157 |
| 2 | `HAS-Mar-25-14541.pdf` | 14541 | Mar | March data, mid-range ID |
| 3 | `HAS-May-25-14936.pdf` | 14936 | May | May data, different season |
| 4 | `HAS-Jul-25-8845.pdf` | 8845 | Jul | **Unusually low ID** - may be special case or backlog |
| 5 | `HAS-Aug-25-17642.pdf` | 17642 | Aug | August data, high ID |
| 6 | `HAS-Sep-25-17810.pdf` | 17810 | Sep | Latest month, highest ID |

## What We're Looking For

### Volcano Types (High Priority)
- 🎯 **Taal** - Special rules: PDZ (4km radius), base surge, fissure zone
- 🎯 **Pinatubo** - Special rules: 5 lahar zones
- 🎯 **Mayon** - Special rules: Highly/Moderately/Least prone lahar classifications
- 🎯 **Bulusan, Hibok-Hibok, Smith** - Other active volcanoes
- ✅ Kanlaon - Already tested
- ✅ Banahaw - Already tested

### Hazard Patterns
- ✅ All Safe (distance-safe) - Covered by 17175
- ✅ Mixed Prone/Safe - Covered by 14157
- 🎯 All Highly Prone - Not yet tested
- 🎯 PDZ violations - Not yet tested
- 🎯 Earthquake-only (no volcano) - Not yet tested
- 🎯 Volcano-only (no earthquake) - Not yet tested

### Assessment Types
- ✅ Combined Earthquake + Volcano - Covered
- 🎯 Single category only
- 🎯 Multiple sites in one assessment
- 🎯 Critical facilities (schools, hospitals)

## Extraction Workflow

### Step 1: Extract Summary Tables (User Action)

For each of the 6 new PDFs, run:

```bash
cd /home/finch/repos/hasadmin/docs

# Extract assessment 14216
timeout 180 gemini -p "@HAS-Feb-25-14216.pdf Extract only the summary table with Assessment ID, Category, Feature Type, Location, and all hazard assessment columns. Format as tab-separated text." 2>&1 | grep -v "^\[" | grep -v "^Loaded" > /tmp/har_14216_summary.txt

# Extract assessment 14541
timeout 180 gemini -p "@HAS-Mar-25-14541.pdf Extract only the summary table with Assessment ID, Category, Feature Type, Location, and all hazard assessment columns. Format as tab-separated text." 2>&1 | grep -v "^\[" | grep -v "^Loaded" > /tmp/har_14541_summary.txt

# Extract assessment 14936
timeout 180 gemini -p "@HAS-May-25-14936.pdf Extract only the summary table with Assessment ID, Category, Feature Type, Location, and all hazard assessment columns. Format as tab-separated text." 2>&1 | grep -v "^\[" | grep -v "^Loaded" > /tmp/har_14936_summary.txt

# Extract assessment 8845
timeout 180 gemini -p "@HAS-Jul-25-8845.pdf Extract only the summary table with Assessment ID, Category, Feature Type, Location, and all hazard assessment columns. Format as tab-separated text." 2>&1 | grep -v "^\[" | grep -v "^Loaded" > /tmp/har_8845_summary.txt

# Extract assessment 17642
timeout 180 gemini -p "@HAS-Aug-25-17642.pdf Extract only the summary table with Assessment ID, Category, Feature Type, Location, and all hazard assessment columns. Format as tab-separated text." 2>&1 | grep -v "^\[" | grep -v "^Loaded" > /tmp/har_17642_summary.txt

# Extract assessment 17810
timeout 180 gemini -p "@HAS-Sep-25-17810.pdf Extract only the summary table with Assessment ID, Category, Feature Type, Location, and all hazard assessment columns. Format as tab-separated text." 2>&1 | grep -v "^\[" | grep -v "^Loaded" > /tmp/har_17810_summary.txt

# Verify extractions
ls -lh /tmp/har_*_summary.txt
```

**Time estimate:** 3-5 minutes per PDF × 6 PDFs = **18-30 minutes total**

### Step 2: Review Extracted Data

```bash
# Quick preview of each extraction
for id in 14216 14541 14936 8845 17642 17810; do
  echo "=== Assessment $id ==="
  head -5 /tmp/har_${id}_summary.txt
  echo ""
done
```

### Step 3: Add to Validation Script

I'll update `validate_manual_extraction.py` with the extracted data.

### Step 4: Run Validation

```bash
cd /home/finch/repos/hasadmin/har-automation
source .venv/bin/activate

# Validate each sample
python3 validate_manual_extraction.py 14216
python3 validate_manual_extraction.py 14541
python3 validate_manual_extraction.py 14936
python3 validate_manual_extraction.py 8845
python3 validate_manual_extraction.py 17642
python3 validate_manual_extraction.py 17810
```

## Expected Outcomes

### Discovery Goals
- [ ] Identify which volcanoes are in the samples (Taal? Pinatubo? Mayon?)
- [ ] Find new hazard patterns not yet tested
- [ ] Identify edge cases or special assessment types
- [ ] Document quality scores for each pattern
- [ ] Confirm gaps are consistent across samples

### Pattern Analysis
After validation, we'll categorize findings:

**Pattern A: Distance-Safe Volcano**
- Example: 17175 (Banahaw, 66.8km)
- Quality: 100%
- Status: ✅ Production-ready

**Pattern B: Proximity-Hazard Volcano**
- Example: 14157 (Kanlaon, 15.2km, Lahar Highly Prone)
- Quality: 40%
- Status: ❌ Needs implementation

**Pattern C: ???** (New patterns from samples)

### Success Criteria
- ✅ 8 total assessments tested (2 existing + 6 new)
- ✅ At least 3 different volcano types identified
- ✅ At least 1 of each: Taal, Pinatubo, or Mayon (if available)
- ✅ Clear pattern categorization
- ✅ Documented gaps with specific examples

## Next Steps After Phase 1

Based on findings, we'll prioritize Phase 2 implementation:

**High Priority** (if gaps confirmed):
1. PDZ assessment logic
2. Lahar assessment with special cases
3. Pyroclastic Flow assessment
4. Avoidance recommendation logic

**Medium Priority** (if new patterns found):
5. Volcano-specific rules (Taal, Pinatubo, Mayon)
6. Edge case handling

---

**Status:** Ready for extraction
**Action Required:** User runs Gemini extraction commands for 6 PDFs
**Time Estimate:** 20-30 minutes for extraction + 5 minutes for validation
