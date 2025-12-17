"""
Test OHAS native format parsing

This tests the exact format you get when copying from OHAS browser.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.parser import TableParser

# Exact format from user's example
ohas_text = """Hazard Assessment
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
"""

print("Testing OHAS native format parsing...")
print("=" * 60)

try:
    assessments = TableParser.parse_from_text(ohas_text)

    print(f"✓ Successfully parsed {len(assessments)} assessment(s)\n")

    for assessment in assessments:
        print(f"Assessment ID: {assessment.id}")
        print(f"Category: {assessment.category.value}")
        print(f"Feature Type: {assessment.feature_type.value}")
        print(f"Location: {assessment.location}")

        if assessment.earthquake:
            print(f"\nEarthquake Hazards:")
            print(f"  Active Fault: {assessment.earthquake.active_fault}")
            print(f"  Liquefaction: {assessment.earthquake.liquefaction}")
            print(f"  Landslide: {assessment.earthquake.landslide}")
            print(f"  Tsunami: {assessment.earthquake.tsunami}")

        if assessment.volcano:
            print(f"\nVolcano Hazards:")
            print(f"  Nearest AV: {assessment.volcano.nearest_active_volcano}")
            print(f"  Nearest PAV: {assessment.volcano.nearest_pav}")

    print("\n" + "=" * 60)
    print("✓ Test passed! OHAS format parsing works correctly.")

except Exception as e:
    print(f"✗ Test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
