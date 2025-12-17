#!/usr/bin/env python3
"""
Simple HAR generator - paste summary table directly.
No clipboard dependency required.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.parser import OHASParser, SchemaLoader
from src.pipeline import DecisionEngine


def main():
    print("="*60)
    print("HAR Generator - Direct Input Mode")
    print("="*60)
    print("\nPaste your summary table, then press Ctrl+D (Linux/Mac) or Ctrl+Z (Windows):\n")

    # Read from stdin
    try:
        summary_table = sys.stdin.read().strip()
    except KeyboardInterrupt:
        print("\n\nCancelled.")
        return

    if not summary_table:
        print("✗ No input received")
        return

    print(f"\n✓ Received {len(summary_table)} characters\n")

    # Load schema
    print("Loading schema...")
    loader = SchemaLoader()
    schema = loader.load()
    engine = DecisionEngine(schema)
    print("✓ Schema loaded\n")

    # Parse
    print("Parsing summary table...")
    try:
        assessments = OHASParser.parse_from_table(summary_table)
        print(f"✓ Parsed {len(assessments)} assessment(s)\n")
    except Exception as e:
        print(f"✗ Parsing failed: {e}")
        import traceback
        traceback.print_exc()
        return

    # Generate HARs
    print("="*60)
    print("Generating HARs")
    print("="*60)

    for i, assessment in enumerate(assessments, 1):
        print(f"\nHAR {i}/{len(assessments)}: Assessment {assessment.id} ({assessment.category.value})")
        print("="*60)

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

    print(f"\n{'='*60}")
    print(f"✓ Generated {len(assessments)} HAR(s)")
    print("="*60)


if __name__ == '__main__':
    main()
