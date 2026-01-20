"""
Test to verify the _process_pdz() method fix.

This test demonstrates that the method now:
1. Extracts distance from volcano
2. Compares distance vs PDZ radius
3. Generates appropriate "inside" or "outside" PDZ statements
4. Returns a HARSection (not None)
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from models import (
    Assessment,
    AssessmentCategory,
    HazardRulesSchema,
    VolcanoRule,
    VolcanoAssessment,
)
from pipeline.decision_engine import DecisionEngine


def create_test_assessment(distance_km: float, volcano_name: str) -> Assessment:
    """Create a test assessment with specified distance to volcano."""
    nearest_volcano_text = f"Approximately {distance_km} km north of {volcano_name} Volcano"

    return Assessment(
        request_id=12345,
        location="Test Location",
        category=AssessmentCategory.VOLCANO,
        volcano=VolcanoAssessment(
            nearest_active_volcano=nearest_volcano_text,
            nearest_potentially_active_volcano="N/A"
        )
    )


def create_test_schema() -> HazardRulesSchema:
    """Create a minimal schema with PDZ rule."""
    return HazardRulesSchema(
        version="1.0",
        earthquake_rules={},
        volcano_rules={
            "pdz_danger_zone": VolcanoRule(
                hazard_type="PDZ",
                explanation="The Permanent Danger Zone (PDZ) of {volcano_name} Volcano extends {radius} km from the crater.",
                recommendation="Human settlement is not recommended within the PDZ.",
                special_cases={
                    "Mayon": {
                        "radius_km": 6.0,
                        "explanation": "Mayon Volcano has a 6-km PDZ."
                    },
                    "Taal": {
                        "radius_km": 4.0,
                        "explanation": "Taal Volcano Island is the PDZ."
                    },
                    "Kanlaon": {
                        "radius_km": 4.0,
                        "explanation": "Kanlaon Volcano has a 4-km PDZ."
                    }
                }
            )
        },
        decision_logic={},
        fuzzy_logic_parameters={}
    )


def test_pdz_inside():
    """Test PDZ assessment when site is INSIDE the PDZ."""
    print("\n=== Test 1: Site INSIDE PDZ (3 km from Mayon, PDZ = 6 km) ===")

    schema = create_test_schema()
    engine = DecisionEngine(schema)
    assessment = create_test_assessment(3.0, "Mayon")

    result = engine._process_pdz(assessment, "Mayon")

    if result is None:
        print("❌ FAILED: Method returned None instead of HARSection")
        return False

    print(f"✓ Heading: {result.heading}")
    print(f"✓ Assessment: {result.assessment}")
    print(f"✓ Explanation: {result.explanation_recommendation.explanation}")
    print(f"✓ Recommendation: {result.explanation_recommendation.recommendation}")

    assert "Within PDZ" in result.assessment
    assert "6-kilometer radius" in result.assessment
    print("✓ PASSED: Site correctly identified as inside PDZ")
    return True


def test_pdz_outside():
    """Test PDZ assessment when site is OUTSIDE the PDZ."""
    print("\n=== Test 2: Site OUTSIDE PDZ (10 km from Mayon, PDZ = 6 km) ===")

    schema = create_test_schema()
    engine = DecisionEngine(schema)
    assessment = create_test_assessment(10.0, "Mayon")

    result = engine._process_pdz(assessment, "Mayon")

    if result is None:
        print("❌ FAILED: Method returned None instead of HARSection")
        return False

    print(f"✓ Heading: {result.heading}")
    print(f"✓ Assessment: {result.assessment}")
    print(f"✓ Explanation: {result.explanation_recommendation.explanation}")

    assert "Outside PDZ" in result.assessment
    assert "6-kilometer radius" in result.assessment
    assert "outside the" in result.explanation_recommendation.explanation.lower()
    print("✓ PASSED: Site correctly identified as outside PDZ")
    return True


def test_pdz_kanlaon():
    """Test PDZ assessment for different volcano (Kanlaon)."""
    print("\n=== Test 3: Site inside Kanlaon PDZ (2 km, PDZ = 4 km) ===")

    schema = create_test_schema()
    engine = DecisionEngine(schema)
    assessment = create_test_assessment(2.0, "Kanlaon")

    result = engine._process_pdz(assessment, "Kanlaon")

    if result is None:
        print("❌ FAILED: Method returned None instead of HARSection")
        return False

    print(f"✓ Heading: {result.heading}")
    print(f"✓ Assessment: {result.assessment}")

    assert "Within PDZ" in result.assessment
    assert "4-kilometer radius" in result.assessment
    print("✓ PASSED: Kanlaon PDZ correctly processed")
    return True


if __name__ == "__main__":
    print("Testing _process_pdz() method fix...")
    print("=" * 70)

    tests = [
        test_pdz_inside,
        test_pdz_outside,
        test_pdz_kanlaon
    ]

    passed = 0
    failed = 0

    for test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ FAILED with exception: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("\n" + "=" * 70)
    print(f"Results: {passed} passed, {failed} failed out of {len(tests)} tests")

    if failed == 0:
        print("✓ All tests passed! The _process_pdz() method is working correctly.")
        sys.exit(0)
    else:
        print("✗ Some tests failed. Please review the output above.")
        sys.exit(1)
