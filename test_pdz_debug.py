#!/usr/bin/env python3
"""Debug script for PDZ processing"""

from src.pipeline.decision_engine import DecisionEngine
from src.models import Assessment, AssessmentCategory, VolcanoAssessment, FeatureType, Coordinate
from src.parser.schema_loader import SchemaLoader

# Load schema
loader = SchemaLoader()
schema = loader.load()

# Create decision engine
engine = DecisionEngine(schema)

# Test: Mayon at 5.5km
assessment = Assessment(
    id=1,
    category=AssessmentCategory.VOLCANO,
    feature_type=FeatureType.POINT,
    location=Coordinate(120.0, 14.0),
    volcano=VolcanoAssessment(
        nearest_active_volcano='Approximately 5.5 km north of Mayon Volcano',
        nearest_pav=None,
        fissure='--',
        lahar='--',
        pyroclastic_flow='--',
        base_surge='--',
        lava_flow='--',
        ballistic_projectile='--',
        volcanic_tsunami='--'
    )
)

# Manual debugging
print("=== Debug _process_pdz ===")
print(f"1. Getting PDZ rule...")
rule = schema.volcano_rules.get('pdz_danger_zone')
print(f"   Rule found: {rule is not None}")

if rule:
    print(f"\n2. Checking special cases...")
    special_cases = rule.special_cases or {}
    print(f"   Special cases: {list(special_cases.keys())}")

    volcano_lower = 'mayon'.lower()
    print(f"   Looking for: '{volcano_lower}'")

    radius_km = None
    for volcano_key in special_cases:
        print(f"   Checking '{volcano_key.lower()}' against '{volcano_lower}'")
        if volcano_key.lower() in volcano_lower or volcano_lower in volcano_key.lower():
            print(f"   ✓ MATCH found!")
            volcano_config = special_cases[volcano_key]
            if isinstance(volcano_config, dict):
                radius_km = volcano_config.get('radius_km')
                print(f"   radius_km = {radius_km}")
            break

    if radius_km is None:
        print(f"\n   ✗ No radius found! Method will return None")
    else:
        print(f"\n3. Getting distance to volcano...")
        volcano_info = engine._parse_nearest_volcano(assessment)
        distance_km = volcano_info.get('distance', 0.0)
        print(f"   Distance: {distance_km} km")
        print(f"   Radius: {radius_km} km")
        print(f"   Inside PDZ: {distance_km < radius_km}")

        print(f"\n4. Method should return HARSection (not None)")

print("\n=== Running actual method ===")
result = engine._process_pdz(assessment, 'Mayon')
print(f"Result: {'HARSection' if result else 'None'}")

if result:
    print(f"  Heading: {result.heading}")
    print(f"  Assessment: {result.assessment}")
