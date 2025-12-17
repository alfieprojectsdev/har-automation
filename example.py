"""
Example usage of HAR Automation Pipeline

This script demonstrates how to:
1. Load the hazard rules schema
2. Parse assessment data
3. Generate HAR output
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.parser import OHASParser, SchemaLoader
from src.pipeline import DecisionEngine


def example_earthquake_assessment():
    """Example: Generate HAR for earthquake assessment"""

    print("=" * 60)
    print("EXAMPLE 1: Earthquake Assessment (Assessment 24918)")
    print("=" * 60)

    # 1. Load schema
    print("\n1. Loading hazard rules schema...")
    loader = SchemaLoader()
    schema = loader.load()
    print(f"   ✓ Schema loaded: {len(schema.earthquake_rules)} earthquake rules, "
          f"{len(schema.volcano_rules)} volcano rules")

    # 2. Parse assessment data
    print("\n2. Parsing assessment data...")
    assessment_data = {
        "id": 24918,
        "category": "Earthquake",
        "feature_type": "Polygon",
        "location": "120.989669,14.537869",
        "vicinity_map_provided": True,
        "earthquake": {
            "active_fault": "Safe; Approximately 7.1 kilometers west of the Valley Fault System: West Valley Fault",
            "liquefaction": "High Potential",
            "landslide": "--",
            "tsunami": "Prone; Within the tsunami inundation zone",
            "fissure": "--"
        }
    }

    assessment = OHASParser.parse_from_dict(assessment_data)
    print(f"   ✓ Assessment {assessment.id} parsed")
    print(f"   - Category: {assessment.category.value}")
    print(f"   - Feature: {assessment.feature_type.value}")
    print(f"   - Location: {assessment.location}")

    # 3. Generate HAR
    print("\n3. Generating HAR...")
    engine = DecisionEngine(schema)
    har = engine.process_assessment(assessment)
    print(f"   ✓ HAR generated with {len(har.sections)} sections")

    # 4. Output HAR text
    print("\n4. HAR Output:")
    print("-" * 60)
    print(har.to_text())
    print("-" * 60)

    return har


def example_volcano_assessment():
    """Example: Generate HAR for volcano assessment"""

    print("\n\n" + "=" * 60)
    print("EXAMPLE 2: Volcano Assessment (Assessment 24919)")
    print("=" * 60)

    # 1. Load schema
    print("\n1. Loading hazard rules schema...")
    loader = SchemaLoader()
    schema = loader.load()
    print(f"   ✓ Schema loaded")

    # 2. Parse assessment data
    print("\n2. Parsing assessment data...")
    assessment_data = {
        "id": 24919,
        "category": "Volcano",
        "feature_type": "Polygon",
        "location": "120.989669,14.537869",
        "vicinity_map_provided": True,
        "volcano": {
            "nearest_active_volcano": "Approximately 58.3 km north of Taal Volcano",
            "nearest_pav": "Corregidor Volcano is currently classified as potentially active volcano (PAV) with no historical eruption but with uncertain evidence of Holocene (last 10,000 years) activity.",
            "fissure": "--",
            "lahar": "Safe",
            "pyroclastic_flow": "Safe",
            "base_surge": "Safe",
            "lava_flow": "Safe",
            "ballistic_projectile": "Safe",
            "volcanic_tsunami": "Safe"
        }
    }

    assessment = OHASParser.parse_from_dict(assessment_data)
    print(f"   ✓ Assessment {assessment.id} parsed")
    print(f"   - Category: {assessment.category.value}")
    print(f"   - Feature: {assessment.feature_type.value}")

    # 3. Generate HAR
    print("\n3. Generating HAR...")
    engine = DecisionEngine(schema)
    har = engine.process_assessment(assessment)
    print(f"   ✓ HAR generated with {len(har.sections)} sections")

    # 4. Output HAR text
    print("\n4. HAR Output:")
    print("-" * 60)
    print(har.to_text())
    print("-" * 60)

    return har


def example_json_export():
    """Example: Export HAR as JSON"""

    print("\n\n" + "=" * 60)
    print("EXAMPLE 3: Export HAR as JSON")
    print("=" * 60)

    # Generate HAR (reuse earthquake example)
    loader = SchemaLoader()
    schema = loader.load()

    assessment_data = {
        "id": 24918,
        "category": "Earthquake",
        "feature_type": "Polygon",
        "location": "120.989669,14.537869",
        "earthquake": {
            "active_fault": "Safe; Approximately 7.1 kilometers west of the Valley Fault System",
            "liquefaction": "High Potential",
            "tsunami": "Prone; Within the tsunami inundation zone"
        }
    }

    assessment = OHASParser.parse_from_dict(assessment_data)
    engine = DecisionEngine(schema)
    har = engine.process_assessment(assessment)

    # Export as JSON
    import json
    har_dict = har.to_dict()
    print(json.dumps(har_dict, indent=2))


if __name__ == "__main__":
    # Run all examples
    try:
        example_earthquake_assessment()
        example_volcano_assessment()
        # example_json_export()

        print("\n" + "=" * 60)
        print("✓ All examples completed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
