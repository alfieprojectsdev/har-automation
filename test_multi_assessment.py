"""
Test OHAS format with multiple assessments (2 rows)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.parser import TableParser, SchemaLoader
from src.pipeline import DecisionEngine

# Real example from user - 2 assessments
ohas_text = """Hazard Assessment
Displaying 1-2 of 2 results.
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

24777    Earthquake    Polygon    125.083337,11.772125    Safe; Approximately 458 meters west of the Central Samar Fault: Paranas Segment    Safe    Least to Highly Susceptible; Within the depositional zone    Safe    --    --    --    --    --    --    --    --    --
24778    Volcano    Polygon    125.072479,11.788131    --    --    --    --    Approximately 67.7 kilometers east of Biliran Volcano    Approximately 85.4 km northeast of Cancajanag Volcano    --    Safe    Safe    --    Safe    --    --
"""

print("Testing OHAS format with 2 assessments...")
print("=" * 60)

try:
    # Parse
    assessments = TableParser.parse_from_text(ohas_text)

    print(f"✓ Successfully parsed {len(assessments)} assessment(s)\n")

    # Display parsed data
    for i, assessment in enumerate(assessments, 1):
        print(f"Assessment {i}/{len(assessments)}:")
        print(f"  ID: {assessment.id}")
        print(f"  Category: {assessment.category.value}")
        print(f"  Feature Type: {assessment.feature_type.value}")
        print(f"  Location: {assessment.location}")

        if assessment.earthquake:
            print(f"  Earthquake Hazards:")
            if assessment.earthquake.active_fault:
                print(f"    Active Fault: {assessment.earthquake.active_fault}")
            if assessment.earthquake.liquefaction:
                print(f"    Liquefaction: {assessment.earthquake.liquefaction}")
            if assessment.earthquake.landslide:
                print(f"    Landslide: {assessment.earthquake.landslide}")
            if assessment.earthquake.tsunami:
                print(f"    Tsunami: {assessment.earthquake.tsunami}")

        if assessment.volcano:
            print(f"  Volcano Hazards:")
            if assessment.volcano.nearest_active_volcano:
                print(f"    Nearest AV: {assessment.volcano.nearest_active_volcano}")
            if assessment.volcano.nearest_pav:
                print(f"    Nearest PAV: {assessment.volcano.nearest_pav}")
            if assessment.volcano.lahar:
                print(f"    Lahar: {assessment.volcano.lahar}")
            if assessment.volcano.pyroclastic_flow:
                print(f"    Pyroclastic Flow: {assessment.volcano.pyroclastic_flow}")
            if assessment.volcano.lava_flow:
                print(f"    Lava Flow: {assessment.volcano.lava_flow}")

        print()

    print("=" * 60)
    print("✓ Parsing test passed!\n")

    # Now generate HARs
    print("Generating HARs...")
    print("=" * 60)

    loader = SchemaLoader()
    schema = loader.load()
    engine = DecisionEngine(schema)

    for i, assessment in enumerate(assessments, 1):
        print(f"\n{'=' * 60}")
        print(f"HAR {i}/{len(assessments)}: Assessment {assessment.id} ({assessment.category.value})")
        print(f"{'=' * 60}\n")

        try:
            har = engine.process_assessment(assessment)
            print(har.to_text())

            # Save to file
            filename = f"har_{assessment.id}_{assessment.category.value.lower()}.txt"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(har.to_text())
            print(f"\n✓ Saved to: {filename}")

        except Exception as e:
            print(f"✗ Failed to generate HAR: {e}")
            import traceback
            traceback.print_exc()

    print(f"\n{'=' * 60}")
    print(f"✓ Generated {len(assessments)} HAR(s) successfully!")
    print(f"{'=' * 60}")

except Exception as e:
    print(f"✗ Test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
