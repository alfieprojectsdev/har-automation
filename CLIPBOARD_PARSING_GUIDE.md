# Clipboard Parsing Guide - OHAS Native Format

**Date:** 2025-12-12
**Status:** ✅ IMPLEMENTED AND TESTED

---

## Overview

The HAR Automation Pipeline now supports **direct copy-paste from OHAS browser**, handling the messy real-world format exactly as it appears when you select and copy assessment tables.

## The Problem

When copying from OHAS/HASAdmin in a browser, you don't get a clean table - you get:

```
Hazard Assessment
Displaying 1-1 of 1 result.
Assessment
Category
Feature Type
Location
Active Fault
Liquefaction
Landslide
Tsunami
Nearest Active Volcano
Nearest Potentially Active Volcano
Fissure
Lahar
Pyroclastic Flow
Base Surge
Lava Flow
Ballistic Projectile
Volcanic Tsunami

24916    Earthquake    Polygon    121.073821,14.600733    Safe; Approximately 35 meters west of the Valley Fault System: West Valley Fault    --    --    --    --    --    --    --    --    --    --    --    --
No Files Attached
```

**Challenges:**
- Headers are on individual lines (not in a table row)
- Data values are separated by multiple spaces
- Long text fields contain spaces and special characters
- Extra header/footer text ("Hazard Assessment", "No Files Attached")
- Difficult to select just the table data

## The Solution

The `TableParser` now **auto-detects** this format and parses it correctly:

### Detection Logic

```python
if 'Hazard Assessment' in text or 'Displaying' in text:
    # OHAS native format
    return TableParser._parse_ohas_native(text)
```

### Parsing Strategy

1. **Skip header fluff**: "Hazard Assessment", "Displaying 1-1 of..."
2. **Collect column headers**: Parse individual lines until we hit a data row
3. **Find data rows**: Lines starting with digits (assessment ID)
4. **Split values**: Use regex `\s{2,}|\t` to split on multiple spaces or tabs
5. **Stop at footer**: "No Files Attached" or similar

### Code Implementation

```python
@staticmethod
def _parse_ohas_native(text: str) -> List[Assessment]:
    """Parse OHAS native copy-paste format."""

    # Find header start
    for i, line in enumerate(lines):
        if line.lower() in ['assessment', 'category', 'feature type']:
            header_start_idx = i
            break

    # Collect headers (one per line)
    headers = []
    for i in range(header_start_idx, len(lines)):
        if re.match(r'^\d+\s+', line):  # Data row starts
            data_start_idx = i
            break
        headers.append(line.lower())

    # Parse data rows
    for line in data_rows:
        values = re.split(r'\s{2,}|\t', line)
        row_data = dict(zip(headers, values))
        assessment = parse_row_data(row_data)
```

---

## Usage

### Quick Start

1. **Go to OHAS/HASAdmin** in your browser
2. **Select the assessment table**:
   - Start from "Hazard Assessment" header
   - End at "No Files Attached" footer
   - Don't worry about selecting perfectly!
3. **Copy**: Ctrl+C (Windows/Linux) or Cmd+C (Mac)
4. **Run**:
   ```bash
   cd /home/finch/repos/hasadmin/har-automation
   python3 example_clipboard.py
   ```

### Example Output

```
============================================================
HAR Generator - Clipboard Mode
============================================================

Loading hazard rules schema...
✓ Schema loaded: 6 earthquake rules, 11 volcano rules

Reading assessment data from clipboard...
✓ Found 1 assessment(s)
  - Assessment 24916 (Earthquake)

Generating HAR(s)...

============================================================
HAR 1/1: Assessment 24916
============================================================
EARTHQUAKE HAZARD ASSESSMENT

Based on the vicinity map and coordinates provided, the assessment is as follows:

EXPLANATION AND RECOMMENDATION

1. Ground Rupture: Safe; Approximately 35 meters west of the Valley Fault System: West Valley Fault. Ground rupture hazard assessment is the distance to the nearest known active fault. The recommended buffer zone, or Zone of Avoidance, against ground rupture hazard is at least 5 meters on both sides of the active fault or from its zone of deformation.

This assessment supersedes all previous reports issued for this site.

For more information on geohazards in the Philippines, please visit HazardHunterPH (https://hazardhunter.georisk.gov.ph/) and GeoAnalyticsPH (https://geoanalytics.georisk.gov.ph/).

✓ Saved to: har_24916_earthquake.txt

============================================================
✓ Generated 1 HAR(s) successfully!
============================================================
```

---

## Supported Variations

The parser handles:

### 1. Single Assessment
```
Assessment
Category
...
24916    Earthquake    Polygon    ...
```

### 2. Multiple Assessments
```
Assessment
Category
...
24916    Earthquake    Polygon    ...
24917    Volcano       Polygon    ...
```

### 3. Mixed Hazards
```
24916    Earthquake    Polygon    ...    Safe; ...    High Potential    --    --
24917    Volcano       Polygon    ...    --          --                Safe  --
```

### 4. With/Without Footer
Works whether you include "No Files Attached" or not.

### 5. Extra Whitespace
```
Assessment
Category

24916    Earthquake    Polygon    ...
```

---

## Field Name Mapping

The parser normalizes various field name formats:

| OHAS Field | Normalized Name | Variations Accepted |
|-----------|-----------------|---------------------|
| Assessment | `assessment` | "Assessment", "Assessment No", "ID" |
| Active Fault | `active_fault` | "Active Fault", "Ground Rupture" |
| Nearest Active Volcano | `nearest_active_volcano` | "Nearest Volcano", "Active Volcano" |
| Pyroclastic Flow | `pyroclastic_flow` | "Pyroclastic Flow", "PDC", "Pyroclastic Density Current" |
| Ballistic Projectile | `ballistic_projectile` | "Ballistic Projectile", "Ballistic Projectiles" |

**Full list:** See `TableParser.FIELD_MAPPINGS` in `src/parser/table_parser.py`

---

## Error Handling

### Common Issues and Solutions

#### Issue: "Could not find column headers"

**Cause:** The text doesn't contain recognized header keywords.

**Solution:** Make sure your clipboard includes the column headers (Assessment, Category, etc.)

```bash
# Good:
Assessment
Category
24916    Earthquake

# Bad:
24916    Earthquake    # Missing headers
```

#### Issue: "No valid assessment data found"

**Cause:** Data row format is incorrect or assessment ID is missing.

**Solution:** Ensure data rows start with numeric assessment ID.

```bash
# Good:
24916    Earthquake    Polygon    121.073821,14.600733

# Bad:
Earthquake    Polygon    121.073821,14.600733    # Missing ID
```

#### Issue: "Failed to parse clipboard"

**Cause:** Clipboard is empty or contains unrecognized format.

**Solution:**
1. Check clipboard has content
2. Try copying again from OHAS
3. Ensure you're copying the assessment table section

---

## Testing

Test the parser with the exact format:

```bash
cd /home/finch/repos/hasadmin/har-automation
python3 test_ohas_format.py
```

**Expected output:**
```
Testing OHAS native format parsing...
============================================================
✓ Successfully parsed 1 assessment(s)

Assessment ID: 24916
Category: Earthquake
Feature Type: Polygon
Location: 121.073821,14.600733

Earthquake Hazards:
  Active Fault: Safe; Approximately 35 meters west of the Valley Fault System: West Valley Fault
  Liquefaction: --
  ...

============================================================
✓ Test passed! OHAS format parsing works correctly.
```

---

## Comparison with HAM Filename Tools

| Feature | HAM Filename Tools | HAR Automation |
|---------|-------------------|----------------|
| **Clipboard Input** | ✅ Yes | ✅ Yes |
| **Auto-paste on open** | ✅ Yes (Chrome ext) | ❌ Manual copy/paste |
| **Format Detection** | Single format | ✅ **4 formats** (OHAS, Markdown, TSV, Field) |
| **Multi-row Support** | ❌ No | ✅ Yes |
| **OHAS Native Format** | ❌ No | ✅ **Yes** |
| **Field Mapping** | Fixed | ✅ **Flexible** (handles variations) |

---

## Implementation Files

| File | Purpose | Lines |
|------|---------|-------|
| `src/parser/table_parser.py` | Core parsing logic | ~450 |
| `src/parser/ohas_parser.py` | OHASParser with clipboard methods | ~230 |
| `example_clipboard.py` | Clipboard workflow example | ~100 |
| `test_ohas_format.py` | Test with real OHAS format | ~60 |

---

## Future Enhancements

### Planned

- [ ] **Auto-paste on startup** (like HAM tools Chrome extension)
- [ ] **Batch file processing** - Read multiple OHAS exports from folder
- [ ] **Web interface** - Paste into web form, get HAR instantly
- [ ] **Browser extension** - Direct OHAS → HAR in browser

### Under Consideration

- [ ] **Screenshot OCR** - Parse OHAS screenshots directly
- [ ] **PDF parsing** - Extract assessments from HAR PDFs (for validation)
- [ ] **Excel support** - Parse OHAS exports in Excel format

---

## Tips for Assessors

### Best Practices

1. **Select generously**: Include the entire section from "Hazard Assessment" to "No Files Attached"
2. **Don't clean the text**: The parser handles messy input - copying extra text is fine
3. **Copy one request at a time**: Each OHAS request page has its own assessment table
4. **Check the output**: Review generated HARs before submitting

### Keyboard Shortcuts

**Windows/Linux:**
- Select all: `Ctrl + A` (in the assessment table area)
- Copy: `Ctrl + C`

**Mac:**
- Select all: `Cmd + A`
- Copy: `Cmd + C`

### Workflow Optimization

```
Old workflow (manual):
1. Copy assessment data from OHAS         [30 sec]
2. Open HAR template in Word              [30 sec]
3. Type/paste explanations manually       [10-15 min]
4. Format and review                      [5 min]
Total: ~15-20 minutes per assessment

New workflow (automated):
1. Copy assessment table from OHAS        [30 sec]
2. Run: python3 example_clipboard.py      [5 sec]
3. Review generated HAR                   [2 min]
Total: ~3 minutes per assessment

Time saved: 12-17 minutes per assessment (75-85% reduction)
```

---

## Success Metrics

### Test Results

✅ **Single assessment**: Parses correctly
✅ **Multiple assessments**: Parses all rows
✅ **Long text fields**: Preserved intact
✅ **Special characters**: Handled correctly (`;`, `,`, `:`)
✅ **Empty fields** (`--`): Recognized as "not assessed"
✅ **Header variations**: All accepted
✅ **Extra whitespace**: Ignored

### Real-World Validation

Tested with Assessment 24916:
- **Input**: OHAS native copy-paste format
- **Parsed**: Successfully extracted all fields
- **Generated**: Valid HAR text with correct explanations
- **Time**: < 1 second

---

**Status:** ✅ Production ready for OHAS clipboard input
**Next:** Integrate with OHAS workflow and collect user feedback
