# HAR Decision Engine Validation

This document describes the validation script for testing the HAR decision engine against real PHIVOLCS HAR outputs.

## Overview

The `validate_decision_engine.py` script validates that the decision engine generates correct HAR text by:

1. Parsing real OHAS assessment data
2. Generating HARs using the decision engine
3. Comparing generated output with expected content and structure
4. Highlighting differences and providing detailed feedback

## Test Cases

The validation suite includes 5 test cases covering:

- **24918**: Earthquake - Active Fault Safe, High Liquefaction
- **24777**: Earthquake - Multiple Hazards (AF, Liquefaction, Landslide, Tsunami)
- **24778**: Volcano - Biliran (Distance Safe scenario)
- **14786**: Volcano - Mayon Lahar (Highly Prone)
- **tsunami_test**: Earthquake - Tsunami Prone

Each test case validates:
- **Structure**: Correct number of sections, common statements, intro/supersedes
- **Content**: Presence of expected phrases and wording from official HARs
- **Format**: Proper HAR text formatting

## Usage

### Run All Tests

```bash
python validate_decision_engine.py
```

### Run Specific Test

```bash
python validate_decision_engine.py --test-id 24918
```

### Run with Verbose Output

Shows full generated HAR and detailed validation steps:

```bash
python validate_decision_engine.py --verbose
```

### Save Results to JSON

```bash
python validate_decision_engine.py --output validation_results.json
```

### Run Multiple Specific Tests

```bash
python validate_decision_engine.py --test-id 24918 --test-id 24778
```

### Disable Colored Output

For non-TTY environments or redirection to file:

```bash
python validate_decision_engine.py --no-color > results.txt
```

## Command-Line Options

| Option | Short | Description |
|--------|-------|-------------|
| `--verbose` | `-v` | Enable verbose output (show full HARs and detailed steps) |
| `--test-id TEST_ID` | | Run specific test by ID (can be specified multiple times) |
| `--output FILE` | `-o` | Save detailed results to JSON file |
| `--no-color` | | Disable colored output |
| `--help` | `-h` | Show help message |

## Output

### Console Output

The script provides color-coded console output:

- **Green (✓)**: Passed validations
- **Red (✗)**: Failed validations
- **Yellow**: Warnings and issues
- **Cyan**: Section headers and info

### JSON Output Format

When using `--output`, the script generates a JSON file with:

```json
{
  "summary": {
    "total": 5,
    "passed": 2,
    "failed": 3
  },
  "results": [
    {
      "id": "24918",
      "name": "Earthquake - Active Fault Safe, High Liquefaction",
      "category": "Earthquake",
      "passed": true,
      "issues": [],
      "generated_text": "..."  // Only included if failed or verbose
    }
  ]
}
```

## Exit Codes

- **0**: All tests passed
- **1**: One or more tests failed

This allows integration with CI/CD pipelines:

```bash
python validate_decision_engine.py || echo "Validation failed!"
```

## Validation Steps

For each test case, the script:

1. **Parses Input** - Converts OHAS table format to Assessment object
2. **Generates HAR** - Runs decision engine to create HAR output
3. **Validates Structure** - Checks sections count, intro, supersedes, etc.
4. **Validates Content** - Verifies expected phrases are present
5. **Shows Differences** - Highlights missing content if validation fails

## Example Output

```
======================================================================
 Test: Earthquake - Active Fault Safe, High Liquefaction (ID: 24918)  
======================================================================

Step 1: Parsing Input
✓ Parsed assessment 24918
  Category: Earthquake
  Location: 120.989669,14.537869

Step 2: Generating HAR
✓ HAR generated successfully

Step 3: Validating Structure
✓ Structure validation passed

Step 4: Validating Content
✓ Content validation passed

✓ TEST PASSED
```

## Adding New Test Cases

To add new test cases, edit the `TEST_CASES` list in `validate_decision_engine.py`:

```python
TEST_CASES = [
    {
        'id': 'unique_id',
        'name': 'Test Case Description',
        'category': 'Earthquake' or 'Volcano',
        'input': """Assessment\tCategory\t...\n...""",  # TSV format
        'expected_contains': [
            'phrase 1',
            'phrase 2',
        ],
        'expected_structure': {
            'intro': True,
            'sections': 2,
            'common_statements': 3,
            'supersedes': True,
        }
    },
]
```

## Integration with Development Workflow

1. **Before committing changes** to decision engine:
   ```bash
   python validate_decision_engine.py
   ```

2. **When adding new features** to decision engine:
   - Add corresponding test case to `TEST_CASES`
   - Run validation to ensure no regressions
   - Commit both feature and test together

3. **For debugging failed tests**:
   ```bash
   python validate_decision_engine.py --test-id FAILING_ID --verbose
   ```

## Known Issues

Some tests may fail due to:

1. **Additional recommendations statement** - Engine adds HazardHunterPH link, increasing common statement count
2. **Distance-based safety logic** - Needs refinement for volcano hazards at ~50-60km
3. **Lahar assessment** - Mayon lahar zones need special handling

These are tracked in the decision engine implementation and will be addressed in future updates.
