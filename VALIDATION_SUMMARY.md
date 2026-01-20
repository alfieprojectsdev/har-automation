# Validation Script Summary

## Created Files

1. **validate_decision_engine.py** - Main validation script (565 lines)
2. **VALIDATION.md** - Complete documentation for the validation system

## Features Implemented

### Core Validation
- [x] Parse real OHAS assessment data (TSV format)
- [x] Generate HARs using decision engine
- [x] Validate HAR structure (sections, statements, intro, supersedes)
- [x] Validate HAR content (expected phrases present)
- [x] Calculate text similarity
- [x] Highlight differences between generated and expected

### Test Cases (5 total)
- [x] **24918**: Earthquake - Active Fault Safe, High Liquefaction (PASSING)
- [x] **24777**: Earthquake - Multiple Hazards (FAILING - structure count)
- [x] **24778**: Volcano - Biliran Distance Safe (FAILING - structure count)
- [x] **14786**: Volcano - Mayon Lahar (FAILING - missing lahar section)
- [x] **tsunami_test**: Earthquake - Tsunami Prone (PASSING)

### User Interface
- [x] Colored terminal output (ANSI colors)
- [x] Clear pass/fail indicators (✓/✗)
- [x] Progress indicators for each step
- [x] Detailed diff output for failures
- [x] Verbose mode with full HAR output
- [x] Color disable option for non-TTY

### Output Options
- [x] Console output with colors
- [x] JSON output file
- [x] Exit codes (0=pass, 1=fail)
- [x] Summary statistics

### Command-Line Interface
- [x] `--verbose` / `-v` - Show full HARs and details
- [x] `--test-id ID` - Run specific test (repeatable)
- [x] `--output FILE` / `-o` - Save JSON results
- [x] `--no-color` - Disable colored output
- [x] `--help` / `-h` - Show usage

## Test Results

Current status: **2 of 5 tests passing (40%)**

### Passing Tests
1. 24918 - Earthquake basic assessment
2. tsunami_test - Earthquake with tsunami

### Failing Tests (Expected)
1. **24777** - Structure count off by 1 (includes Tsunami section with "Safe" status)
2. **24778** - Common statement count off by 1 (includes HazardHunterPH link)
3. **14786** - Missing lahar section (distance-based safety overriding lahar assessment)

### Identified Issues
The failing tests revealed implementation issues in the decision engine:

1. **Tsunami "Safe" sections** - Currently included as section, may need to be omitted
2. **Additional recommendations** - HazardHunterPH link counted as common statement
3. **Distance-based volcano safety** - At 64km, should still assess lahar if status is "Highly Prone"

## Usage Examples

### Run all tests
```bash
python validate_decision_engine.py
```

### Run specific test with verbose output
```bash
python validate_decision_engine.py --test-id 24918 --verbose
```

### Save results to JSON
```bash
python validate_decision_engine.py --output results.json
```

### Run without colors (for CI/CD)
```bash
python validate_decision_engine.py --no-color
```

## Integration

### CI/CD Pipeline
```bash
# In your CI script
python validate_decision_engine.py --no-color --output validation.json
if [ $? -ne 0 ]; then
    echo "Validation failed!"
    exit 1
fi
```

### Pre-commit Hook
```bash
#!/bin/bash
# .git/hooks/pre-commit
python validate_decision_engine.py --test-id 24918 --test-id tsunami_test
```

## Next Steps

To achieve 100% test passing rate:

1. **Fix tsunami "Safe" handling** - Decide if "Safe" statuses should create sections
2. **Adjust structure expectations** - Update test cases to account for additional recommendations
3. **Fix distance-based volcano logic** - Allow lahar assessment even when > 50km if status is "Prone"
4. **Add more test cases** - Cover Pinatubo zones, Taal PDZ, etc.
5. **Extract real HAR examples** - Use batch_validation.py with Gemini to extract more cases

## File Locations

- Script: `/home/finch/repos/hasadmin/har-automation/validate_decision_engine.py`
- Documentation: `/home/finch/repos/hasadmin/har-automation/VALIDATION.md`
- Example output: `/home/finch/repos/hasadmin/har-automation/validation_results.json`
