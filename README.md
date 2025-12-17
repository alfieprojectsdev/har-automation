# HAR Automation Pipeline

Automated pipeline for generating Hazard Assessment Reports (HAR) from OHAS assessment data.

## Overview

This pipeline automates the generation of HAR text by:
1. Parsing OHAS assessment data (earthquake and volcano hazards)
2. Matching assessment statuses to official PHIVOLCS explanations and recommendations
3. Generating properly formatted HAR text following official templates

### Key Features

- **Rule-based system** - Uses `hazard_rules_schema_refined.json` with exact official wordings
- **Paired explanations and recommendations** - Follows actual HAR structure where explanations and recommendations form cohesive text blocks
- **Volcano-specific rules** - Handles special cases (Pinatubo lahar zones, Mayon prone classifications, Taal PDZ)
- **Flexible input** - Accepts JSON, dictionaries, or future HTML table parsing
- **Multiple output formats** - Plain text, Markdown, JSON

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     HAR Generator Pipeline                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 1. OHAS PARSER                                                   │
│    Parse assessment data from OHAS                               │
│    Extract: hazard statuses, coordinates, volcano info          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. SCHEMA LOADER                                                 │
│    Load hazard_rules_schema_refined.json                         │
│    Validate structure and completeness                           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. DECISION ENGINE                                               │
│    Apply decision logic workflow                                 │
│    Match statuses to conditions                                  │
│    Combine explanations + recommendations as paired units        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. OUTPUT FORMATTER                                              │
│    Generate final HAR text                                       │
│    Format: Plain text, Markdown, JSON                           │
└─────────────────────────────────────────────────────────────────┘
```

## Installation

### Using uv (Recommended)

```bash
cd har-automation

# Create virtual environment
uv venv

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
uv pip install pyperclip

# Install xclip (required for clipboard on Linux)
sudo apt-get install xclip
```

### Using pip

```bash
cd har-automation

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install xclip (required for clipboard on Linux)
sudo apt-get install xclip
```

## Quick Start

### Method 1: Direct Input (No Clipboard Required)

```bash
# 1. Run the generator
python3 generate_har.py

# 2. Paste your summary table from OHAS (Ctrl+Shift+V)
# 3. Press Ctrl+D (Linux/Mac) or Ctrl+Z then Enter (Windows)

# ✓ Generated HARs are saved to files and printed
```

### Method 2: Clipboard Mode (Requires xclip)

```bash
# 1. Go to OHAS/HASAdmin in browser
# 2. Select and copy the entire assessment section (Ctrl+C or Cmd+C)
#    - Include "Hazard Assessment" header
#    - Include "No Files Attached" footer
#    - Don't worry about selecting perfectly - parser handles messy input
# 3. Run:
python3 example_clipboard.py

# ✓ Generated HARs are saved to files and printed
```

**Example of what to copy:**
```
Hazard Assessment
Displaying 1-1 of 1 result.
Assessment
Category
...
24916    Earthquake    Polygon    121.073821...
No Files Attached
```

**The parser handles:**
- Multiple assessments (rows)
- Messy spacing and formatting
- Headers on individual lines
- Long text fields with semicolons/commas

### Method 3: Python API

```python
from src.parser import OHASParser, SchemaLoader
from src.pipeline import DecisionEngine

# 1. Load schema
loader = SchemaLoader()
schema = loader.load()

# 2. Parse from clipboard (auto-detects format)
assessments = OHASParser.parse_from_clipboard()

# Or parse from dict/JSON
assessment = OHASParser.parse_from_dict({
    "id": 24918,
    "category": "Earthquake",
    "feature_type": "Polygon",
    "location": "120.989669,14.537869",
    "earthquake": {
        "active_fault": "Safe; Approximately 7.1 km west of Valley Fault System",
        "liquefaction": "High Potential",
        "tsunami": "Prone; Within the tsunami inundation zone"
    }
})

# 3. Generate HAR
engine = DecisionEngine(schema)
har = engine.process_assessment(assessment)

# 4. Output
print(har.to_text())
```

## Supported Input Formats

The parser **automatically detects** and handles multiple formats:

### 1. OHAS Native Format (Most Common - Direct Browser Copy)

This is what you actually get when copying from OHAS browser:

```
Hazard Assessment
Displaying 1-1 of 1 result.
Assessment
Category
Feature Type
Location
Active Fault
Liquefaction
...
24916    Earthquake    Polygon    121.073821,14.600733    Safe; Approximately 35 meters...    --    --
No Files Attached
```

**Features:**
- ✅ Handles messy header/data separation
- ✅ Parses headers on individual lines
- ✅ Stops at "No Files Attached" footer
- ✅ Handles multi-space separators
- ✅ Preserves long text fields ("Safe; Approximately 35 meters...")

### 2. Markdown Table (from Obsidian Webclipper)
```markdown
| Assessment | Category   | Feature Type | Location              | Active Fault                | Liquefaction   |
|------------|------------|--------------|------------------------|----------------------------|----------------|
| 24918      | Earthquake | Polygon      | 120.989669,14.537869  | Safe; Approximately 7.1 km | High Potential |
| 24919      | Volcano    | Polygon      | 120.988964,14.537753  | --                         | --             |
```

### 2. Tab-Separated (Copy from Browser)
```
Assessment	Category	Feature Type	Location	Active Fault
24918	Earthquake	Polygon	120.989669,14.537869	Safe; Approximately 7.1 km
```

### 3. Field-Based (Like HAM Filename Tools)
```
Assessment: 24918
Category: Earthquake
Feature Type: Polygon
Location: 120.989669,14.537869
Active Fault: Safe; Approximately 7.1 kilometers west of Valley Fault System
Liquefaction: High Potential
```

### 4. JSON/Dict (Programmatic)
```python
{
    "id": 24918,
    "category": "Earthquake",
    "earthquake": {...}
}
```

**All formats work with clipboard parsing!** Just copy from OHAS and run the script.

## Examples

### Clipboard Example (Recommended)

```bash
# Copy OHAS table, then:
python3 example_clipboard.py
```

### API Examples

See `example.py` for complete examples:

```bash
python3 example.py
```

This runs:
1. **Earthquake Assessment** - Generate HAR for earthquake hazards
2. **Volcano Assessment** - Generate HAR for volcano hazards

## Project Structure

```
har-automation/
├── src/
│   ├── models/
│   │   ├── assessment.py          # Assessment data models
│   │   ├── schema.py              # Schema structure models
│   │   └── har_output.py          # HAR output models
│   ├── parser/
│   │   ├── ohas_parser.py         # Parse OHAS data
│   │   └── schema_loader.py       # Load hazard rules schema
│   ├── pipeline/
│   │   ├── decision_engine.py     # Core decision logic
│   │   └── condition_matcher.py   # Match statuses to conditions
│   └── __init__.py
├── tests/
│   ├── test_parser.py
│   ├── test_engine.py
│   └── fixtures/
├── example.py                     # Usage examples
├── README.md
└── requirements.txt
```

## Data Models

### Assessment

```python
@dataclass
class Assessment:
    id: int
    category: AssessmentCategory  # EARTHQUAKE or VOLCANO
    feature_type: FeatureType      # POLYGON, POINT, or LINE
    location: Coordinate
    earthquake: Optional[EarthquakeAssessment] = None
    volcano: Optional[VolcanoAssessment] = None
    vicinity_map_provided: bool = False
```

### HAR Output

```python
@dataclass
class HAROutput:
    category: AssessmentCategory
    intro: str
    sections: List[HARSection]  # Each hazard as a section
    common_statements: List[ExplanationRecommendation]
    supersedes: str
    additional_recommendations: List[str]

    def to_text(self) -> str:
        """Generate plain text HAR"""

    def to_dict(self) -> dict:
        """Generate JSON-serializable dictionary"""
```

### Explanation and Recommendation Pairing

The pipeline correctly implements explanations and recommendations as **paired units**, following the actual HAR structure:

```python
@dataclass
class ExplanationRecommendation:
    """
    Explanation and Recommendation as a single cohesive text block.

    Example:
        "Ground rupture hazard assessment is the distance to the nearest
        known active fault. The recommended buffer zone, or Zone of Avoidance,
        against ground rupture hazard is at least 5 meters on both sides of
        the active fault or from its zone of deformation."
    """
    text: str

    @classmethod
    def from_parts(cls, explanation: Optional[str] = None,
                   recommendation: Optional[str] = None):
        """Combine explanation and recommendation intelligently"""
```

## Decision Workflow

### Earthquake Hazards

1. Check map availability (vicinity map or coordinates only)
2. Assess Active Fault distance
3. Assess Fissure proximity (if within 1km of fault)
4. Assess Liquefaction potential
5. Assess Earthquake-Induced Landslide susceptibility
6. Assess Tsunami (if coastal)
7. Add Ground Shaking statement
8. Add mitigation recommendations (Building Code compliance)
9. Add supersedes statement

### Volcano Hazards

1. Check map availability
2. Identify nearest Active Volcano
3. Check distance category (> 50km = distance-based safety)
4. Assess Permanent Danger Zone (PDZ) status
5. Assess Lava Flow
6. Assess Pyroclastic Density Current
7. Assess Lahar (volcano-specific: Pinatubo zones, Mayon prone levels)
8. Assess Ballistic Projectiles (if applicable)
9. Assess Base Surge (Taal only)
10. Assess Volcanic Tsunami (if applicable)
11. Assess Fissure (Taal area)
12. Check Potentially Active Volcano (PAV)
13. Add Ashfall statement (always included)
14. Add avoidance recommendation (if any hazard is prone)
15. Add supersedes statement

## Special Cases Handled

### Pinatubo Lahar Zones

5 distinct lahar zones with different explanations:
- Zone 1 (most hazardous) → Zone 5 (least hazardous)

### Mayon Lahar Classifications

3 prone levels:
- Highly Prone
- Moderately Prone
- Least Prone

### Taal Volcano

- Permanent Danger Zone (PDZ)
- Base Surge assessment
- Fissure assessment
- Volcanic Tsunami

### Potentially Active Volcanoes (PAV)

Special statement for volcanoes classified as PAV (e.g., Corregidor):
> "Corregidor Volcano is currently classified as potentially active volcano (PAV) with no historical eruption but with uncertain evidence of Holocene (last 10,000 years) activity."

## Testing

```bash
# Run unit tests (when implemented)
pytest tests/

# Run with coverage
pytest --cov=src tests/

# Test with specific assessment
python example.py
```

## Output Format

The generated HAR follows the official PHIVOLCS template structure:

```
EARTHQUAKE HAZARD ASSESSMENT

Based on the vicinity map and coordinates provided, the assessment is as follows:

EXPLANATION AND RECOMMENDATION

1. Ground Rupture: Safe; Approximately 7.1 kilometers west of the Valley Fault System.
   Ground rupture hazard assessment is the distance to the nearest known active fault.
   The recommended buffer zone, or Zone of Avoidance, against ground rupture hazard
   is at least 5 meters on both sides of the active fault or from its zone of deformation.

2. Ground Shaking and Liquefaction: All sites may be affected by strong ground shaking.
   High Potential. Ground shaking and liquefaction hazards can be mitigated by following
   the provisions of the National Building Code and the Structural Code of the Philippines.

3. Tsunami: Prone; Within the tsunami inundation zone. Tsunami threat to people's lives
   can be addressed by community preparedness and tsunami evacuation plan...

This assessment supersedes all previous reports issued for this site.

For more information on geohazards in the Philippines, please visit HazardHunterPH
(https://hazardhunter.georisk.gov.ph/) and GeoAnalyticsPH (https://geoanalytics.georisk.gov.ph/).
```

## Integration with OHAS

The pipeline is designed to integrate with the OHAS platform workflow:

```
┌──────────────────────────────────────────────────────────────┐
│                   HASADMIN PLATFORM                          │
│  1. Manual: Draw property boundary                          │
│  2. Click: "Assess" button                                  │
│     └─→ Spatial analysis and Summary Table population      │
│  3. Click: "Sync to GeoDB"                                  │
└──────────────────────────────────────────────────────────────┘
                         ↓
┌──────────────────────────────────────────────────────────────┐
│              HAR AUTOMATION PIPELINE (This Module)           │
│  - Parse Summary Table data                                  │
│  - Match to official explanations/recommendations            │
│  - Generate complete HAR text                                │
│  Time: <1 second                                            │
└──────────────────────────────────────────────────────────────┘
                         ↓
┌──────────────────────────────────────────────────────────────┐
│                  HUMAN REVIEW (5-10 min)                     │
│  - Verify HAR accuracy                                       │
│  - Approve and submit                                        │
└──────────────────────────────────────────────────────────────┘
```

## Schema Structure

The pipeline uses `docs/hazard_rules_schema_refined.json` which contains:

- **Earthquake Rules**: Active Fault, Liquefaction, EIL, Tsunami, Fissure
- **Volcano Rules**: PDZ, Lava Flow, PDC, Base Surge, Ballistic, Lahar, Volcanic Tsunami, Fissure, Ashfall
- **Decision Logic**: Step-by-step workflow for each hazard category
- **Conditions**: Status templates (Safe, High Potential, Prone, etc.)
- **Special Cases**: Volcano-specific rules (Pinatubo zones, Mayon classifications, Taal hazards)

### Schema Design Principle: Separation of Concerns

- **Schema (Data Storage)**: Explanations and recommendations stored as **separate fields** for flexibility and maintainability
- **Pipeline (Data Presentation)**: Combines them into **paired units** for HAR output format

See `docs/SCHEMA_STRUCTURE_RATIONALE.md` for detailed rationale.

## Future Enhancements

- [ ] HTML table parsing (from OHAS clipboard)
- [ ] PDF generation with proper formatting
- [ ] Web API (Flask/FastAPI) for HAR generation
- [ ] Direct OHAS database integration
- [ ] Multi-language support (Filipino translations)
- [ ] Batch processing for multiple assessments
- [ ] Visualization with hazard maps

## Related Documentation

- `docs/HAR_GENERATOR_PIPELINE_PLAN.md` - Complete implementation plan
- `docs/SCHEMA_STRUCTURE_RATIONALE.md` - Why schema is structured this way
- `docs/ASSESSMENT_18388_ANALYSIS.md` - Real assessment analysis example
- `docs/HAR_STRUCTURE_INSIGHTS.md` - HAR document structure findings
- `docs/REVISED_AUTOMATION_STRATEGY.md` - Overall automation approach

## Contributing

When making changes:
1. Follow the existing code structure
2. Update tests for new features
3. Ensure schema changes are backward compatible
4. Document special cases in code comments

## License

Internal PHIVOLCS tool - not for public distribution.

---

**Status:** Initial implementation complete (v0.1.0)
**Next Steps:** Testing with real OHAS data, validation, integration
