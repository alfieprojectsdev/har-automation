"""
Example: HAR generation from clipboard (like HAM filename tools)

This demonstrates clipboard-based workflow:
1. Copy OHAS summary table from browser
2. Run this script
3. Get HAR text output

Usage:
    1. Go to OHAS/HASAdmin assessment page
    2. Copy the summary table (Ctrl+C or Cmd+C)
    3. Run: python3 example_clipboard.py
    4. View generated HAR(s)
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.parser import OHASParser, SchemaLoader
from src.pipeline import DecisionEngine


def main():
    """Main clipboard parsing workflow"""

    print("=" * 60)
    print("HAR Generator - Clipboard Mode")
    print("=" * 60)
    print()

    # 1. Load schema
    print("Loading hazard rules schema...")
    try:
        loader = SchemaLoader()
        schema = loader.load()
        print(f"✓ Schema loaded: {len(schema.earthquake_rules)} earthquake rules, "
              f"{len(schema.volcano_rules)} volcano rules")
    except Exception as e:
        print(f"✗ Failed to load schema: {e}")
        return 1

    # 2. Parse from clipboard
    print("\nReading assessment data from clipboard...")
    try:
        assessments = OHASParser.parse_from_clipboard()
        print(f"✓ Found {len(assessments)} assessment(s)")
        for assessment in assessments:
            print(f"  - Assessment {assessment.id} ({assessment.category.value})")
    except Exception as e:
        print(f"✗ Failed to parse clipboard: {e}")
        print("\nExpected format:")
        print("Copy OHAS summary table from browser, then run this script.")
        print("\nExample format:")
        print("| Assessment | Category   | Feature Type | Location              | Active Fault | ... |")
        print("| 24918      | Earthquake | Polygon      | 120.989669,14.537869  | Safe; ...    | ... |")
        return 1

    # 3. Generate HARs
    print("\nGenerating HAR(s)...")
    engine = DecisionEngine(schema)

    for i, assessment in enumerate(assessments, start=1):
        print(f"\n{'=' * 60}")
        print(f"HAR {i}/{len(assessments)}: Assessment {assessment.id}")
        print(f"{'=' * 60}")

        try:
            har = engine.process_assessment(assessment)
            print(har.to_text())
            print()

            # Save to file
            filename = f"har_{assessment.id}_{assessment.category.value.lower()}.txt"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(har.to_text())
            print(f"✓ Saved to: {filename}")

        except Exception as e:
            print(f"✗ Failed to generate HAR: {e}")
            import traceback
            traceback.print_exc()

    print(f"\n{'=' * 60}")
    print(f"✓ Generated {len(assessments)} HAR(s) successfully!")
    print(f"{'=' * 60}")

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
