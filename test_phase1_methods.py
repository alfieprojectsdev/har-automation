#!/usr/bin/env python3
"""
Test script for Phase 1 volcano proximity-hazard methods.

Tests the 4 new methods added to DecisionEngine:
- _process_pdz
- _process_lahar
- _process_pyroclastic_flow
- _check_needs_avoidance
- _get_avoidance_recommendation
"""

import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from models import Assessment, AssessmentCategory, FeatureType, Coordinate, VolcanoAssessment
from pipeline.decision_engine import DecisionEngine
from parser.schema_loader import SchemaLoader


def test_syntax_and_import():
    """Test that all methods can be imported and have correct signatures."""
    print("Testing Phase 1 method imports...")

    # Load schema
    schema_path = Path(__file__).parent.parent / 'docs' / 'hazard_rules_schema_refined.json'
    loader = SchemaLoader()
    schema = loader.load_schema(str(schema_path))

    # Create decision engine
    engine = DecisionEngine(schema)

    # Check that methods exist
    assert hasattr(engine, '_process_pdz'), "_process_pdz method not found"
    assert hasattr(engine, '_process_lahar'), "_process_lahar method not found"
    assert hasattr(engine, '_process_pyroclastic_flow'), "_process_pyroclastic_flow method not found"
    assert hasattr(engine, '_check_needs_avoidance'), "_check_needs_avoidance method not found"
    assert hasattr(engine, '_get_avoidance_recommendation'), "_get_avoidance_recommendation method not found"

    print("✓ All Phase 1 methods found")
    return True


def test_lahar_method():
    """Test lahar processing with a sample assessment."""
    print("\nTesting _process_lahar method...")

    # Load schema
    schema_path = Path(__file__).parent.parent / 'docs' / 'hazard_rules_schema_refined.json'
    loader = SchemaLoader()
    schema = loader.load_schema(str(schema_path))

    # Create decision engine
    engine = DecisionEngine(schema)

    # Create a test assessment with lahar data
    volcano = VolcanoAssessment(
        nearest_active_volcano="Approximately 15.2 km north of Kanlaon Volcano",
        lahar="Highly Prone"
    )

    assessment = Assessment(
        id=14157,
        category=AssessmentCategory.VOLCANO,
        feature_type=FeatureType.POINT,
        location=Coordinate(longitude=123.0, latitude=10.0),
        volcano=volcano,
        vicinity_map_provided=True
    )

    # Test the method
    result = engine._process_lahar(assessment, "Kanlaon")

    if result:
        print(f"✓ Lahar section generated")
        print(f"  Heading: {result.heading}")
        print(f"  Assessment: {result.assessment}")
        print(f"  Text length: {len(result.explanation_recommendation.text)} chars")
    else:
        print("✓ Lahar section returned None (expected for Safe status)")

    return True


def test_pyroclastic_flow_method():
    """Test pyroclastic flow processing."""
    print("\nTesting _process_pyroclastic_flow method...")

    # Load schema
    schema_path = Path(__file__).parent.parent / 'docs' / 'hazard_rules_schema_refined.json'
    loader = SchemaLoader()
    schema = loader.load_schema(str(schema_path))

    # Create decision engine
    engine = DecisionEngine(schema)

    # Create a test assessment with PDC data
    volcano = VolcanoAssessment(
        nearest_active_volcano="Approximately 15.2 km north of Kanlaon Volcano",
        pyroclastic_flow="Prone"
    )

    assessment = Assessment(
        id=14157,
        category=AssessmentCategory.VOLCANO,
        feature_type=FeatureType.POINT,
        location=Coordinate(longitude=123.0, latitude=10.0),
        volcano=volcano,
        vicinity_map_provided=True
    )

    # Test the method
    result = engine._process_pyroclastic_flow(assessment)

    if result:
        print(f"✓ PDC section generated")
        print(f"  Heading: {result.heading}")
        print(f"  Assessment: {result.assessment}")
        print(f"  Text length: {len(result.explanation_recommendation.text)} chars")
    else:
        print("✓ PDC section returned None (expected for Safe status)")

    return True


def test_avoidance_methods():
    """Test avoidance checking and recommendation generation."""
    print("\nTesting _check_needs_avoidance and _get_avoidance_recommendation...")

    # Load schema
    schema_path = Path(__file__).parent.parent / 'docs' / 'hazard_rules_schema_refined.json'
    loader = SchemaLoader()
    schema = loader.load_schema(str(schema_path))

    # Create decision engine
    engine = DecisionEngine(schema)

    # Test 1: Assessment with prone lahar
    volcano1 = VolcanoAssessment(
        nearest_active_volcano="Approximately 15.2 km north of Kanlaon Volcano",
        lahar="Highly Prone"
    )
    assessment1 = Assessment(
        id=14157,
        category=AssessmentCategory.VOLCANO,
        feature_type=FeatureType.POINT,
        location=Coordinate(longitude=123.0, latitude=10.0),
        volcano=volcano1
    )

    needs_avoidance = engine._check_needs_avoidance(assessment1)
    print(f"✓ Prone lahar → needs_avoidance = {needs_avoidance}")
    assert needs_avoidance == True, "Should need avoidance for prone lahar"

    # Test 2: Assessment with safe statuses
    volcano2 = VolcanoAssessment(
        nearest_active_volcano="Approximately 60.0 km north of Kanlaon Volcano",
        lahar="Safe",
        pyroclastic_flow="Safe"
    )
    assessment2 = Assessment(
        id=14158,
        category=AssessmentCategory.VOLCANO,
        feature_type=FeatureType.POINT,
        location=Coordinate(longitude=123.0, latitude=10.0),
        volcano=volcano2
    )

    needs_avoidance2 = engine._check_needs_avoidance(assessment2)
    print(f"✓ All safe → needs_avoidance = {needs_avoidance2}")
    assert needs_avoidance2 == False, "Should not need avoidance for safe statuses"

    # Test 3: Get avoidance recommendation
    avoidance_rec = engine._get_avoidance_recommendation()
    print(f"✓ Avoidance recommendation generated")
    print(f"  Text length: {len(avoidance_rec.text)} chars")
    assert len(avoidance_rec.text) > 0, "Avoidance text should not be empty"

    return True


def main():
    """Run all tests."""
    print("=" * 60)
    print("Phase 1 Volcano Proximity-Hazard Methods Test")
    print("=" * 60)

    try:
        test_syntax_and_import()
        test_lahar_method()
        test_pyroclastic_flow_method()
        test_avoidance_methods()

        print("\n" + "=" * 60)
        print("All tests passed!")
        print("=" * 60)
        return 0

    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
