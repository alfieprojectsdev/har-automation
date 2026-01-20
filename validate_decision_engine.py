#!/usr/bin/env python3
"""
Validate Decision Engine Against Real HAR Outputs
Tests the decision engine with real OHAS data and compares
output with actual PHIVOLCS HAR documents.

Usage:
    python validate_decision_engine.py
    python validate_decision_engine.py --verbose
    python validate_decision_engine.py --test-id 24918
"""

import sys
from pathlib import Path
from typing import List, Dict, Tuple
from difflib import unified_diff, SequenceMatcher
import argparse

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.parser import OHASParser, SchemaLoader
from src.pipeline import DecisionEngine

# ANSI color codes for terminal output
class Colors:
    """ANSI color codes for colored terminal output"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

    @staticmethod
    def disable():
        """Disable colors for non-TTY output"""
        Colors.HEADER = ''
        Colors.OKBLUE = ''
        Colors.OKCYAN = ''
        Colors.OKGREEN = ''
        Colors.WARNING = ''
        Colors.FAIL = ''
        Colors.ENDC = ''
        Colors.BOLD = ''
        Colors.UNDERLINE = ''


# Real HAR test cases extracted from actual PHIVOLCS HARs
TEST_CASES = [
    {
        'id': '24918',
        'name': 'Test Case 1: Basic Earthquake (HAS-24918)',
        'category': 'Earthquake',
        'input': """Assessment\tCategory\tFeature Type\tLocation\tActive Fault\tLiquefaction
24918\tEarthquake\tPolygon\t120.989669,14.537869\tSafe; Approximately 7.1 km west of Valley Fault System\tHigh Potential""",
        'expected_contains': [
            'Ground rupture hazard assessment is the distance',
            '5 meters on both sides',
            'High Potential',
            'National Building Code',
            'EARTHQUAKE HAZARD ASSESSMENT',
            'All hazard assessments are based on',
        ],
        'expected_structure': {
            'intro': True,
            'sections': 2,  # Ground Rupture + Ground Shaking and Liquefaction
            'supersedes': True,
        }
    },
    {
        'id': '18223',
        'name': 'Test Case 2: EIL Susceptible (HAS-18223)',
        'category': 'Earthquake',
        'input': """Assessment\tCategory\tFeature Type\tLocation\tActive Fault\tLandslide
18223\tEarthquake\tPolygon\t122.8856,14.1053\tSafe; Approximately 40.9 km northeast of Legaspi Lineament\tSusceptible""",
        'expected_contains': [
            'Ground rupture hazard assessment',
            'Earthquake-Induced Landslide',
            'Susceptible',
            'Avoidance is recommended for sites with earthquake-induced landslide hazard',
            'engineering interventions',
            'EARTHQUAKE HAZARD ASSESSMENT',
        ],
        'expected_structure': {
            'intro': True,
            'sections': 3,  # Ground Rupture + Ground Shaking/Liquefaction + EIL
            'supersedes': True,
        },
        'vicinity_map_provided': True
    },
    {
        'id': '17810',
        'name': 'Test Case 3: Volcano All Safe (HAS-17810)',
        'category': 'Volcano',
        'input': """Assessment\tCategory\tFeature Type\tLocation\tNearest Active Volcano\tLahar\tPyroclastic Flow\tLava Flow
17810\tVolcano\tPolygon\t123.8545,12.7512\tApproximately 24 kilometers north of Bulusan Volcano\tSafe\tSafe\tSafe""",
        'expected_contains': [
            'Bulusan Volcano is the nearest identified active volcano',
            'Considering the distance of the site',
            'pyroclastic density currents',
            'lava flows',
            'ballistic projectiles',
            'ashfall',
            'VOLCANO HAZARD ASSESSMENT',
        ],
        'expected_structure': {
            'intro': True,
            'sections': 0,  # No hazard sections, all safe
            'common_statements': 2,  # Nearest volcano + Distance-based safety + Ashfall (no PAV)
            'supersedes': True,
        },
        'vicinity_map_provided': True
    },
    {
        'id': '14157',
        'name': 'Test Case 4: Volcano Mixed Hazards (HAS-14157)',
        'category': 'Volcano',
        'input': """Assessment\tCategory\tFeature Type\tLocation\tNearest Active Volcano\tLahar\tPyroclastic Flow\tLava Flow
14157\tVolcano\tPolygon\t123.1234,10.3456\tApproximately 15.2 kilometers southwest of Kanlaon Volcano\tHighly prone\tProne; Within buffer zone\tSafe""",
        'expected_contains': [
            'Kanlaon Volcano is the nearest identified active volcano',
            'Highly prone',
            'Lahar',
            'Prone',
            'buffer zone',
            'Pyroclastic',
            'Avoidance is recommended',
            'ashfall',
            'VOLCANO HAZARD ASSESSMENT',
        ],
        'expected_structure': {
            'intro': True,
            'sections': 2,  # Lahar + Pyroclastic Flow (Lava Flow is Safe)
            'common_statements': 3,  # Nearest volcano + Ashfall + Avoidance (no distance-based safety at 15km)
            'supersedes': True,
        },
        'vicinity_map_provided': True
    },
]


def print_header(text: str, color: str = Colors.HEADER) -> None:
    """Print a formatted header"""
    print(f"\n{color}{Colors.BOLD}{'='*70}{Colors.ENDC}")
    print(f"{color}{Colors.BOLD}{text:^70}{Colors.ENDC}")
    print(f"{color}{Colors.BOLD}{'='*70}{Colors.ENDC}\n")


def print_section(title: str, content: str = None) -> None:
    """Print a formatted section"""
    print(f"{Colors.OKCYAN}{Colors.BOLD}{title}{Colors.ENDC}")
    if content:
        print(content)
    print()


def calculate_similarity(text1: str, text2: str) -> float:
    """
    Calculate similarity ratio between two texts.

    Args:
        text1: First text
        text2: Second text

    Returns:
        Similarity ratio (0.0 to 1.0)
    """
    return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()


def compare_text_content(generated: str, expected_phrases: List[str], test_name: str, verbose: bool = False) -> Tuple[bool, List[str]]:
    """
    Compare generated text with expected content.

    Args:
        generated: Generated HAR text
        expected_phrases: List of phrases that should be present
        test_name: Name of test case
        verbose: Whether to print verbose output

    Returns:
        Tuple of (success, missing_phrases)
    """
    missing = []

    for phrase in expected_phrases:
        if phrase.lower() not in generated.lower():
            missing.append(phrase)

    if verbose or missing:
        print_section(f"Content Validation: {test_name}")

        for phrase in expected_phrases:
            if phrase.lower() in generated.lower():
                print(f"  {Colors.OKGREEN}✓{Colors.ENDC} Found: {phrase[:60]}...")
            else:
                print(f"  {Colors.FAIL}✗{Colors.ENDC} Missing: {phrase[:60]}...")

    return len(missing) == 0, missing


def validate_structure(har_output, expected_structure: Dict, test_name: str, verbose: bool = False) -> Tuple[bool, List[str]]:
    """
    Validate HAR output structure.

    Args:
        har_output: HAROutput object
        expected_structure: Expected structure dict
        test_name: Name of test case
        verbose: Whether to print verbose output

    Returns:
        Tuple of (success, issues)
    """
    issues = []

    # Check intro
    if expected_structure.get('intro', False):
        if not har_output.intro or len(har_output.intro) < 10:
            issues.append("Missing or invalid intro statement")

    # Check number of sections
    if 'sections' in expected_structure:
        expected_count = expected_structure['sections']
        actual_count = len(har_output.sections)
        if actual_count != expected_count:
            issues.append(f"Expected {expected_count} sections, got {actual_count}")

    # Check common statements
    if 'common_statements' in expected_structure:
        expected_count = expected_structure['common_statements']
        actual_count = len(har_output.common_statements)
        if actual_count != expected_count:
            issues.append(f"Expected {expected_count} common statements, got {actual_count}")

    # Check supersedes
    if expected_structure.get('supersedes', False):
        if not har_output.supersedes or len(har_output.supersedes) < 10:
            issues.append("Missing or invalid supersedes statement")

    if verbose or issues:
        print_section(f"Structure Validation: {test_name}")

        print(f"  Intro: {Colors.OKGREEN if har_output.intro else Colors.FAIL}{'Present' if har_output.intro else 'Missing'}{Colors.ENDC}")
        print(f"  Sections: {len(har_output.sections)}")
        print(f"  Common statements: {len(har_output.common_statements)}")
        print(f"  Supersedes: {Colors.OKGREEN if har_output.supersedes else Colors.FAIL}{'Present' if har_output.supersedes else 'Missing'}{Colors.ENDC}")

        if issues:
            print(f"\n  {Colors.WARNING}Issues:{Colors.ENDC}")
            for issue in issues:
                print(f"    {Colors.FAIL}✗{Colors.ENDC} {issue}")

    return len(issues) == 0, issues


def highlight_differences(generated: str, expected_phrases: List[str]) -> None:
    """
    Show detailed differences between generated and expected text.

    Args:
        generated: Generated HAR text
        expected_phrases: Expected phrases
    """
    print_section("Detailed Differences")

    print(f"{Colors.BOLD}Generated HAR (first 500 chars):{Colors.ENDC}")
    print(generated[:500] + "...\n")

    print(f"{Colors.BOLD}Missing Expected Phrases:{Colors.ENDC}")
    for phrase in expected_phrases:
        if phrase.lower() not in generated.lower():
            print(f"  {Colors.FAIL}✗{Colors.ENDC} {phrase}")


def run_single_test(test_case: Dict, engine: DecisionEngine, verbose: bool = False) -> Dict:
    """
    Run a single test case.

    Args:
        test_case: Test case dictionary
        engine: DecisionEngine instance
        verbose: Whether to print verbose output

    Returns:
        Result dictionary
    """
    test_id = test_case['id']
    test_name = test_case['name']

    print_header(f"Test: {test_name} (ID: {test_id})", Colors.OKCYAN)

    result = {
        'id': test_id,
        'name': test_name,
        'category': test_case['category'],
        'passed': True,
        'issues': []
    }

    try:
        # 1. Parse input
        print_section("Step 1: Parsing Input")
        assessments = OHASParser.parse_from_table(test_case['input'])

        if not assessments:
            result['passed'] = False
            result['issues'].append("Failed to parse input")
            print(f"{Colors.FAIL}✗ No assessments parsed{Colors.ENDC}")
            return result

        assessment = assessments[0]

        # Set vicinity_map_provided if specified in test case
        if 'vicinity_map_provided' in test_case:
            assessment.vicinity_map_provided = test_case['vicinity_map_provided']

        print(f"{Colors.OKGREEN}✓ Parsed assessment {assessment.id}{Colors.ENDC}")
        print(f"  Category: {assessment.category.value}")
        print(f"  Location: {assessment.location}")
        if assessment.vicinity_map_provided:
            print(f"  Vicinity map: Provided")

        # 2. Generate HAR
        print_section("Step 2: Generating HAR")
        har_output = engine.process_assessment(assessment)
        print(f"{Colors.OKGREEN}✓ HAR generated successfully{Colors.ENDC}")

        # 3. Validate structure
        print_section("Step 3: Validating Structure")
        structure_valid, structure_issues = validate_structure(
            har_output,
            test_case.get('expected_structure', {}),
            test_name,
            verbose=verbose
        )

        if not structure_valid:
            result['passed'] = False
            result['issues'].extend(structure_issues)
        else:
            print(f"{Colors.OKGREEN}✓ Structure validation passed{Colors.ENDC}")

        # 4. Validate content
        print_section("Step 4: Validating Content")
        generated_text = har_output.to_text()

        content_valid, missing_phrases = compare_text_content(
            generated_text,
            test_case.get('expected_contains', []),
            test_name,
            verbose=verbose
        )

        if not content_valid:
            result['passed'] = False
            result['issues'].append(f"Missing {len(missing_phrases)} expected phrase(s)")
            result['missing_phrases'] = missing_phrases
        else:
            print(f"{Colors.OKGREEN}✓ Content validation passed{Colors.ENDC}")

        # 5. Show differences if failed or verbose
        if not result['passed'] or verbose:
            highlight_differences(generated_text, missing_phrases if not content_valid else [])

        # 6. Show full generated HAR in verbose mode
        if verbose:
            print_section("Full Generated HAR")
            print(f"{Colors.BOLD}{'─'*70}{Colors.ENDC}")
            print(generated_text)
            print(f"{Colors.BOLD}{'─'*70}{Colors.ENDC}")

        # Store generated text for inspection
        result['generated_text'] = generated_text

        # Final status
        if result['passed']:
            print(f"\n{Colors.OKGREEN}{Colors.BOLD}✓ TEST PASSED{Colors.ENDC}\n")
        else:
            print(f"\n{Colors.FAIL}{Colors.BOLD}✗ TEST FAILED{Colors.ENDC}")
            print(f"{Colors.WARNING}Issues:{Colors.ENDC}")
            for issue in result['issues']:
                print(f"  - {issue}")
            print()

    except Exception as e:
        result['passed'] = False
        result['issues'].append(f"Exception: {str(e)}")
        print(f"{Colors.FAIL}✗ Exception occurred: {str(e)}{Colors.ENDC}")

        if verbose:
            import traceback
            traceback.print_exc()

    return result


def run_validation(test_ids: List[str] = None, verbose: bool = False, output_file: str = None) -> int:
    """
    Run all validation tests.

    Args:
        test_ids: Optional list of specific test IDs to run
        verbose: Whether to print verbose output
        output_file: Optional file path to save detailed results (JSON)

    Returns:
        Exit code (0 if all pass, 1 if any fail)
    """
    print_header("HAR Decision Engine Validation Suite", Colors.HEADER)

    # Load schema and create engine
    print("Loading schema...")
    loader = SchemaLoader()
    schema = loader.load()
    engine = DecisionEngine(schema)
    print(f"{Colors.OKGREEN}✓ Schema loaded successfully{Colors.ENDC}\n")

    # Filter test cases if specific IDs requested
    test_cases = TEST_CASES
    if test_ids:
        test_cases = [tc for tc in TEST_CASES if tc['id'] in test_ids]
        if not test_cases:
            print(f"{Colors.FAIL}✗ No test cases found with IDs: {test_ids}{Colors.ENDC}")
            return 1

    print(f"Running {len(test_cases)} test case(s)...\n")

    # Run tests
    results = []
    for test_case in test_cases:
        result = run_single_test(test_case, engine, verbose=verbose)
        results.append(result)

    # Print summary
    print_header("Validation Summary", Colors.HEADER)

    passed = [r for r in results if r['passed']]
    failed = [r for r in results if not r['passed']]

    print(f"Total Tests: {len(results)}")
    print(f"{Colors.OKGREEN}Passed: {len(passed)}{Colors.ENDC}")
    print(f"{Colors.FAIL}Failed: {len(failed)}{Colors.ENDC}")

    if failed:
        print(f"\n{Colors.FAIL}{Colors.BOLD}Failed Tests:{Colors.ENDC}")
        for r in failed:
            print(f"\n  {Colors.FAIL}✗{Colors.ENDC} {r['name']} (ID: {r['id']})")
            for issue in r['issues']:
                print(f"    - {issue}")

    # Save detailed results to file if requested
    if output_file:
        import json
        output_path = Path(output_file)

        # Prepare results for JSON serialization
        json_results = []
        for r in results:
            json_result = {
                'id': r['id'],
                'name': r['name'],
                'category': r['category'],
                'passed': r['passed'],
                'issues': r['issues'],
            }

            # Only include generated text if failed or verbose
            if not r['passed'] or verbose:
                json_result['generated_text'] = r.get('generated_text', '')

            if 'missing_phrases' in r:
                json_result['missing_phrases'] = r['missing_phrases']

            json_results.append(json_result)

        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump({
                'summary': {
                    'total': len(results),
                    'passed': len(passed),
                    'failed': len(failed)
                },
                'results': json_results
            }, f, indent=2)

        print(f"\n{Colors.OKGREEN}✓ Detailed results saved to: {output_file}{Colors.ENDC}")

    # Return exit code
    if failed:
        print(f"\n{Colors.FAIL}{Colors.BOLD}VALIDATION FAILED{Colors.ENDC}\n")
        return 1
    else:
        print(f"\n{Colors.OKGREEN}{Colors.BOLD}ALL TESTS PASSED{Colors.ENDC}\n")
        return 0


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Validate HAR decision engine against real PHIVOLCS HARs',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python validate_decision_engine.py                # Run all tests
  python validate_decision_engine.py --verbose      # Run with verbose output
  python validate_decision_engine.py --test-id 24918  # Run specific test
  python validate_decision_engine.py --no-color     # Disable colored output
        """
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )

    parser.add_argument(
        '--test-id',
        action='append',
        dest='test_ids',
        help='Run specific test by ID (can be specified multiple times)'
    )

    parser.add_argument(
        '--no-color',
        action='store_true',
        help='Disable colored output'
    )

    parser.add_argument(
        '--output', '-o',
        dest='output_file',
        help='Save detailed results to JSON file'
    )

    args = parser.parse_args()

    # Disable colors if requested or not a TTY
    if args.no_color or not sys.stdout.isatty():
        Colors.disable()

    # Run validation
    exit_code = run_validation(
        test_ids=args.test_ids,
        verbose=args.verbose,
        output_file=args.output_file
    )

    sys.exit(exit_code)


if __name__ == '__main__':
    main()
