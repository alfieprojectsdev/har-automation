#!/usr/bin/env python3
"""
Manual validation workflow using pre-extracted data from Gemini CLI.

Usage:
1. Extract data from PDF using Gemini CLI:
   gemini -p "@HAS-{Month}-25-{ID}.pdf Extract summary table and EXPLANATION section"

2. Save summary table to data/extracted/{ID}_summary.txt

3. Run this script to validate:
   python3 validate_manual_extraction.py {ID}
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.parser import OHASParser, SchemaLoader
from src.pipeline import DecisionEngine


def validate_assessment(assessment_id: str):
    """Validate a single assessment using pre-extracted data."""

    print(f"{'='*60}")
    print(f"Validating Assessment {assessment_id}")
    print(f"{'='*60}\n")

    # Test data directly embedded for demo
    # Note: Using OHAS-style format with assessment IDs
    if assessment_id == "14157":
        # Combined earthquake + volcano (Kanlaon)
        summary_table = """Assessment	Category	Feature Type	Location	Active Fault	Liquefaction	Landslide	Tsunami	Nearest Active Volcano	Lahar	Pyroclastic Flow	Lava Flow
14157	Earthquake	Polygon	121.073821,14.600733	Safe; Approximately 2.9 kilometers east of the West Negros Fault	--	--	--	--	--	--	--
14157	Volcano	Polygon	121.073821,14.600733	--	--	--	--	Approximately 15.2 kilometers southwest of Kanlaon Volcano	Highly prone	Prone; Within buffer zone	Safe"""

    elif assessment_id == "17175":
        # Combined earthquake + volcano (Banahaw)
        summary_table = """Assessment	Category	Feature Type	Location	Active Fault	Liquefaction	Landslide	Tsunami	Nearest Active Volcano	Lahar	Pyroclastic Flow	Lava Flow
17175	Earthquake	Polygon	121.073821,14.600733	Safe; Approximately 7.5 kilometers southwest of an unnamed fault traversing General Nakar, Quezon Province	Least Susceptible	Prone; Within the depositional zone	Safe	--	--	--	--
17175	Volcano	Polygon	121.073821,14.600733	--	--	--	--	Approximately 66.8 kilometers northwest of Banahaw Volcano	Safe	Safe	Safe"""

    elif assessment_id == "14216":
        # Combined earthquake + volcano (Taal, tsunami prone, complex statuses)
        # Note: Simplified complex "Largely Safe, Partly Least Susceptible" to dominant status
        summary_table = """Assessment	Category	Feature Type	Location	Active Fault	Liquefaction	Landslide	Tsunami	Nearest Active Volcano	Lahar	Pyroclastic Flow	Lava Flow	Base Surge	Ballistic Projectile
14216	Earthquake	Polygon	120.673821,13.900733	Safe; Approximately 683 meters west of the Calatagan Fault	Largely Safe, Partly Least Susceptible	Largely Safe, Partly Least Susceptible/Moderately Susceptible/Highly Susceptible	Prone; Within the tsunami inundation zone	--	--	--	--	--	--
14216	Volcano	Polygon	120.673821,13.900733	--	--	--	--	Approximately 41.5 km southwest of Taal Volcano	--	--	--	Safe	Safe"""

    elif assessment_id == "14541":
        # Combined earthquake + volcano (Camiguin de Babuyanes, very distant, all safe)
        summary_table = """Assessment	Category	Feature Type	Location	Active Fault	Liquefaction	Landslide	Tsunami	Nearest Active Volcano	Lahar	Pyroclastic Flow	Lava Flow
14541	Earthquake	Polygon	120.573821,18.200733	Safe; Approximately 7.2 kilometers west of the West Ilocos Fault System	Largely Safe, Partly Moderately Susceptible	Safe	Safe	--	--	--	--
14541	Volcano	Polygon	120.573821,18.200733	--	--	--	--	Approximately 150.2 km southwest of Camiguin de Babuyanes Volcano	Safe	Safe	Safe"""

    elif assessment_id == "14936":
        # Combined earthquake + volcano (Hibok-hibok, EIL susceptible)
        summary_table = """Assessment	Category	Feature Type	Location	Active Fault	Liquefaction	Landslide	Tsunami	Nearest Active Volcano	Lahar	Pyroclastic Flow	Lava Flow	Ballistic Projectile
14936	Earthquake	Polygon	124.873821,8.100733	Safe; Approximately 9 kilometers west of the Cabulig Fault	Safe	Susceptible	Safe	--	--	--	--	--
14936	Volcano	Polygon	124.873821,8.100733	--	--	--	--	Approximately 72.4 kilometers southeast of Hibok-hibok Volcano	Safe	Safe	Safe	Safe"""

    elif assessment_id == "8845":
        # Minimal earthquake + volcano (Hibok-hibok, only 2 EQ hazards assessed)
        summary_table = """Assessment	Category	Feature Type	Location	Active Fault	Liquefaction	Landslide	Tsunami	Nearest Active Volcano	Lahar	Pyroclastic Flow	Lava Flow
8845	Earthquake	Polygon	125.573821,8.900733	Safe; Approximately 2.9 kilometers west of the Philippine Fault: Surigao Segment	Susceptible	--	--	--	--	--	--
8845	Volcano	Polygon	125.573821,8.900733	--	--	--	--	Approximately 105 kilometers east of Hibok-hibok Volcano	--	--	--"""

    elif assessment_id == "17642":
        # Combined earthquake + volcano (Pinatubo, liquefaction highly susceptible)
        summary_table = """Assessment	Category	Feature Type	Location	Active Fault	Liquefaction	Landslide	Tsunami	Nearest Active Volcano	Lahar	Pyroclastic Flow	Lava Flow
17642	Earthquake	Polygon	120.373821,16.050733	Safe; Approximately 17.3 kilometers east of the East Zambales Fault	Highly Susceptible	Safe	Safe	--	--	--	--
17642	Volcano	Polygon	120.373821,16.050733	--	--	--	--	Approximately 97.7 kilometers north of Pinatubo Volcano	Safe	--	--"""

    elif assessment_id == "17810":
        # Earthquake-only (no volcano), all safe
        summary_table = """Assessment	Category	Feature Type	Location	Active Fault	Liquefaction	Landslide	Tsunami	Nearest Active Volcano	Lahar	Pyroclastic Flow	Lava Flow
17810	Earthquake	Polygon	123.973821,12.900733	Safe; Approximately 16.9 kilometers south of the Legaspi Lineament: Offshore Extension 1 and approximately 55.1 kilometers east of the Panganiran Fault	Safe	Safe	Safe	--	--	--	--"""

    elif assessment_id == "24920":
        # Combined earthquake + volcano (Isarog 44km + Labo PAV 33km, all hazards Safe)
        summary_table = """Assessment	Category	Feature Type	Location	Active Fault	Liquefaction	Landslide	Tsunami	Nearest Active Volcano	Nearest Potentially Active Volcano	Fissure	Lahar	Pyroclastic Flow	Base Surge	Lava Flow	Ballistic Projectile	Volcanic Tsunami
24920	Earthquake	Polygon	123.080735,13.923128	Safe; Approximately 40.9 kilometers northeast of the Legaspi Lineament	--	Safe	--	--	--	--	--	--	--	--	--	--
24921	Volcano	Polygon	123.082334,13.92292	--	--	--	--	Approximately 44 kilometers northwest of Isarog Volcano	Approximately 33 kilometers east of Labo Volcano	--	Safe	Safe	--	Safe	--	--"""

    else:
        print(f"✗ No test data for assessment {assessment_id}")
        return

    # Load schema
    print("Loading schema...")
    loader = SchemaLoader()
    schema = loader.load()
    engine = DecisionEngine(schema)
    print("✓ Schema loaded\n")

    # Parse summary table
    print("Parsing summary table...")
    try:
        assessments = OHASParser.parse_from_table(summary_table)
        print(f"✓ Parsed {len(assessments)} assessment(s)\n")

        for i, assessment in enumerate(assessments, 1):
            print(f"Assessment {i}: {assessment.category.value}")
            print(f"  Feature Type: {assessment.feature_type.value}")
            print(f"  Location: {assessment.location}")

            if assessment.earthquake:
                print(f"  Earthquake hazards:")
                if assessment.earthquake.active_fault:
                    print(f"    - Active Fault: {assessment.earthquake.active_fault}")
                if assessment.earthquake.liquefaction:
                    print(f"    - Liquefaction: {assessment.earthquake.liquefaction}")
                if assessment.earthquake.landslide:
                    print(f"    - Landslide: {assessment.earthquake.landslide}")
                if assessment.earthquake.tsunami:
                    print(f"    - Tsunami: {assessment.earthquake.tsunami}")

            if assessment.volcano:
                print(f"  Volcano hazards:")
                if assessment.volcano.nearest_active_volcano:
                    print(f"    - Nearest AV: {assessment.volcano.nearest_active_volcano}")
                if assessment.volcano.lahar:
                    print(f"    - Lahar: {assessment.volcano.lahar}")
                if assessment.volcano.pyroclastic_flow:
                    print(f"    - Pyroclastic Flow: {assessment.volcano.pyroclastic_flow}")
                if assessment.volcano.lava_flow:
                    print(f"    - Lava Flow: {assessment.volcano.lava_flow}")
            print()

    except Exception as e:
        print(f"✗ Parsing failed: {e}")
        import traceback
        traceback.print_exc()
        return

    # Generate HARs
    print(f"{'='*60}")
    print("Generating HARs")
    print(f"{'='*60}\n")

    for i, assessment in enumerate(assessments, 1):
        try:
            har = engine.process_assessment(assessment)

            print(f"HAR {i}/{len(assessments)}: {assessment.category.value}")
            print(f"{'='*60}\n")
            print(har.to_text())
            print()

            # Save to file
            filename = f"har_{assessment_id}_{assessment.category.value.lower()}_{i}.txt"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(har.to_text())
            print(f"✓ Saved to: {filename}\n")

        except Exception as e:
            print(f"✗ Failed to generate HAR: {e}")
            import traceback
            traceback.print_exc()

    print(f"{'='*60}")
    print("✓ Validation complete")
    print(f"{'='*60}")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 validate_manual_extraction.py {assessment_id}")
        print("\nAvailable test data (Phase 1 - 8 samples):")
        print("\nAlready tested:")
        print("  - 14157 (Feb, Kanlaon 15.2km, Lahar Highly Prone, PDC Prone)")
        print("  - 17175 (Jul, Banahaw 66.8km, All Safe)")
        print("\nNew samples:")
        print("  - 14216 (Feb, Taal 41.5km, Tsunami Prone, Complex statuses)")
        print("  - 14541 (Mar, Camiguin de Babuyanes 150.2km, All Safe)")
        print("  - 14936 (May, Hibok-hibok 72.4km, EIL Susceptible)")
        print("  - 8845  (Jul, Hibok-hibok 105km, Minimal EQ assessment)")
        print("  - 17642 (Aug, Pinatubo 97.7km, Liquefaction Highly Susceptible)")
        print("  - 17810 (Sep, Earthquake-only, All Safe)")
        sys.exit(1)

    assessment_id = sys.argv[1]
    validate_assessment(assessment_id)

