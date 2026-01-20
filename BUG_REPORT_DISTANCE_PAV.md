# BUG REPORT - Distance-Based Safety & PAV Statement
## HAR Automation - Critical Fixes Required

**Date**: 2025-12-21
**Severity**: HIGH
**Impact**: Generated HARs missing required statements

---

## BUG 1: Distance-Based Safety Logic Incorrect

### Issue
The `_check_distance_based_safety()` method has incorrect logic for determining when to show the distance-based safety statement.

**Current (WRONG) logic**:
```python
def _check_distance_based_safety(self, assessment: Assessment, distance_km: float) -> bool:
    # Check distance threshold
    if distance_km > 50.0:
        return True

    # Check if all proximity hazards are "Safe"  ← THIS IS WRONG
    proximity_hazards = []
    if assessment.volcano.pyroclastic_flow:
        proximity_hazards.append(assessment.volcano.pyroclastic_flow)
    if assessment.volcano.lava_flow:
        proximity_hazards.append(assessment.volcano.lava_flow)
    if assessment.volcano.ballistic_projectile:
        proximity_hazards.append(assessment.volcano.ballistic_projectile)

    # All must be "Safe" for distance-based safety statement
    if proximity_hazards and all('Safe' in h for h in proximity_hazards):
        return True  ← THIS CONDITION IS INCORRECT

    return False
```

### Evidence from Official HARs

| HAR | Distance | All Hazards Safe? | Distance-based safety present? | Result |
|-----|----------|-------------------|-------------------------------|--------|
| HAS-Jul-24-12496 | 80.3 km | Yes | ✅ YES | Correct |
| HAS-Jun-25-16968 | 69 km | Yes | ✅ YES | Correct |
| HAS-Apr-25-14786 | **64.4 km** | **No (Lahar Prone)** | **✅ YES** | **KEY EVIDENCE** |
| HAS-18223 (24920) | 44 km | Yes | ❌ NO | Correct |

**Key finding**: HAS-Apr-25-14786 has distance-based safety statement even though Lahar status is "Prone" (not all Safe). This proves the logic should ONLY check distance, not hazard statuses.

### Expected Behavior
Distance-based safety statement should appear when **distance > ~50-60 km from nearest active volcano**, regardless of hazard statuses.

**Statement text** (from official HARs):
> "Considering the distance of the site from the volcano, the site is safe from volcanic hazards such as pyroclastic density currents, lava flows, and ballistic projectiles that may originate from the volcano."

Note: This statement specifically mentions PDC, lava flows, and ballistic projectiles. It does NOT mention lahar, which is why it appears even when Lahar is "Prone".

### Fix Required

**Correct logic**:
```python
def _check_distance_based_safety(self, assessment: Assessment, distance_km: float) -> bool:
    """
    Distance-based safety statement appears when site is > ~50-60km from volcano.

    This is independent of hazard statuses - even if some hazards (like lahar)
    are Prone, the distance-based statement still appears for proximity hazards
    (PDC, lava flows, ballistic projectiles).
    """
    # Threshold is approximately 50-60km based on official HARs
    # Using 50km as conservative threshold
    if distance_km > 50.0:
        return True

    return False
```

### Impact
- **Before fix**: Missing distance-based safety statement for sites 50-70km from volcano
- **After fix**: Statement correctly appears for all sites > 50km

---

## BUG 2: PAV (Potentially Active Volcano) Statement Missing

### Issue
PAV statements are not being added to generated HARs, even when a PAV is present in the assessment data.

**Current implementation**:
- `_process_pav()` method exists (lines 1115-1143) but is NOT called in workflow
- Lines 229-231 have comment saying "Skip PAV if we already have a nearby active volcano"
- This is INCORRECT based on official HARs

### Evidence from Official HARs

**All 5 samples have Labo as PAV, and ALL include PAV statement**:

| HAR | Isarog (AV) Distance | Labo (PAV) Distance | PAV Statement Present? |
|-----|---------------------|---------------------|----------------------|
| HAS-Jul-24-12496 | 80.3 km | 15.8 km | ✅ YES |
| HAS-Jun-25-14462 | 70.9 km | 16.7 km | ✅ YES |
| HAS-Jun-25-16968 | 69 km | 10.4 km | ✅ YES |
| HAS-Jul-25-16994 | 68.4 km | 15.1 km | ✅ YES |
| HAS-Apr-25-14786 | 64.4 km | 25.8 km | ✅ YES |

**Statement text** (from official HARs):
> "Labo Volcano is currently classified by DOST-PHIVOLCS as a potentially active volcano, which is morphologically young-looking but with no historical or analytical records of eruption, therefore, its eruptive and hazard potential is yet to be determined."

### Expected Behavior
PAV statement should be added to `common_statements` list (NOT as a hazard section) when `assessment.volcano.nearest_pav` is present, **regardless of whether there's also a nearby active volcano**.

### Fix Required

**Location**: `decision_engine.py:229-231`

**Remove incorrect comment**:
```python
# 11. PAV (Potentially Active Volcano) - only if no nearby active volcano
# Skip PAV if we already have a nearby active volcano
# Real HARs prioritize nearest AV over distant PAV
```

**Add PAV processing**:
```python
# 11. PAV (Potentially Active Volcano) - always include if present
if assessment.volcano.nearest_pav and assessment.volcano.nearest_pav != "--":
    pav_statement = self._get_pav_statement(assessment.volcano.nearest_pav)
    common.append(pav_statement)
```

**Create new method** `_get_pav_statement()`:
```python
def _get_pav_statement(self, pav_text: str) -> ExplanationRecommendation:
    """
    Get PAV statement for common statements section.

    Args:
        pav_text: Text from assessment.volcano.nearest_pav
                  Format: "Approximately X kilometers [direction] of [Volcano Name] Volcano"

    Returns:
        ExplanationRecommendation for PAV
    """
    # Extract volcano name from text
    # Format: "Approximately 15.8 kilometers northeast of Labo Volcano"
    volcano_name = "Unknown"
    if "of " in pav_text and "Volcano" in pav_text:
        parts = pav_text.split("of ")[-1]  # Get part after "of "
        volcano_name = parts.split(" Volcano")[0].strip()

    # Standard PAV explanation
    explanation = (
        f"{volcano_name} Volcano is currently classified by DOST-PHIVOLCS as a "
        f"potentially active volcano, which is morphologically young-looking but with "
        f"no historical or analytical records of eruption, therefore, its eruptive and "
        f"hazard potential is yet to be determined."
    )

    return ExplanationRecommendation.from_parts(explanation=explanation)
```

### Impact
- **Before fix**: PAV statements completely missing from generated HARs
- **After fix**: PAV statements correctly included for all assessments with PAV data

---

## SUMMARY OF FIXES

### Files to Modify
1. `/home/finch/repos/hasadmin/har-automation/src/pipeline/decision_engine.py`

### Changes Required

1. **Fix distance-based safety logic** (lines 1050-1085)
   - Remove "all hazards Safe" condition
   - Keep only distance > 50km check

2. **Add PAV statement processing** (lines 229-231)
   - Remove incorrect comment
   - Add PAV statement to common_statements when present
   - Create `_get_pav_statement()` method

### Testing Required

After fixes, re-run validation on:
1. Sample 24920 (should still match preview - no PAV in preview)
2. HAS-Apr-25-14786 equivalent (64.4km, should show distance-based safety + PAV)
3. All 8 regression samples (ensure no regressions)

### Expected Results

**For sites > 50km from volcano**:
- ✅ Distance-based safety statement appears
- ✅ PAV statement appears (if PAV present)
- ✅ Ashfall statement appears
- ✅ Hazard sections only for non-Safe statuses

**For sites < 50km from volcano**:
- ❌ No distance-based safety statement
- ✅ PAV statement appears (if PAV present)
- ✅ Ashfall statement appears
- ✅ Hazard sections for all assessed hazards

---

## PRIORITY

**Severity**: HIGH
**Impact**: Missing required statements in generated HARs
**Priority**: FIX IMMEDIATELY before production deployment

Both bugs cause generated HARs to deviate from official PHIVOLCS format and may result in incomplete hazard information being provided to users.

---

**Report Date**: 2025-12-21
**Discovered by**: Comparison with official released HARs (5 samples)
**Status**: Fixes pending implementation
