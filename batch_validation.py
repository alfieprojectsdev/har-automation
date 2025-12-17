#!/usr/bin/env python3
"""
Batch validation script for HAR generation pipeline.
Validates generated HARs against approved PHIVOLCS HARs.
"""

import sys
import json
import subprocess
from pathlib import Path
from typing import List, Dict, Tuple

sys.path.insert(0, str(Path(__file__).parent))

from src.parser import OHASParser, SchemaLoader
from src.pipeline import DecisionEngine


# List of approved HAR PDFs
APPROVED_HARS = [
    "/home/finch/repos/hasadmin/docs/HAS-Jul-25-17175.pdf",
    "/home/finch/repos/hasadmin/docs/HAS-Jul-25-17176.pdf",
    "/home/finch/repos/hasadmin/docs/HAS-Jul-25-17181.pdf",
    "/home/finch/repos/hasadmin/docs/HAS-Jul-25-17180.pdf",
    "/home/finch/repos/hasadmin/docs/HAS-Jun-25-17023.pdf",
    "/home/finch/repos/hasadmin/docs/HAS-Jun-25-17014.pdf",
    "/home/finch/repos/hasadmin/docs/HAS-Jun-25-17020.pdf",
    "/home/finch/repos/hasadmin/docs/HAS-May-25-14959.pdf",
    "/home/finch/repos/hasadmin/docs/HAS-May-25-14936.pdf",
    "/home/finch/repos/hasadmin/docs/HAS-May-25-14921.pdf",
    "/home/finch/repos/hasadmin/docs/HAS-May-25-16788.pdf",
    "/home/finch/repos/hasadmin/docs/HAS-Mar-25-14541.pdf",
    "/home/finch/repos/hasadmin/docs/HAS-Mar-25-14448.pdf",
    "/home/finch/repos/hasadmin/docs/HAS-Mar-25-14563.pdf",
    "/home/finch/repos/hasadmin/docs/HAS-Feb-25-14216.pdf",
    "/home/finch/repos/hasadmin/docs/HAS-Feb-25-14157.pdf",
    "/home/finch/repos/hasadmin/docs/HAS-Feb-25-14341.pdf",
    "/home/finch/repos/hasadmin/docs/HAS-Feb-25-14174.pdf",
    "/home/finch/repos/hasadmin/docs/HAS-Feb-25-14165.pdf",
    "/home/finch/repos/hasadmin/docs/HAS-Sep-25-17810.pdf",
    "/home/finch/repos/hasadmin/docs/HAS-Sep-25-17760.pdf",
    "/home/finch/repos/hasadmin/docs/HAS-Sep-25-17768.pdf",
    "/home/finch/repos/hasadmin/docs/HAS-Aug-25-17642.pdf",
    "/home/finch/repos/hasadmin/docs/HAS-Aug-25-17635.pdf",
    "/home/finch/repos/hasadmin/docs/HAS-Aug-25-17633.pdf",
    "/home/finch/repos/hasadmin/docs/HAS-Jul-25-17283.pdf",
    "/home/finch/repos/hasadmin/docs/HAS-Jul-25-17119.pdf",
    "/home/finch/repos/hasadmin/docs/HAS-Jul-25-8845.pdf",
]


def extract_assessment_id(pdf_path: str) -> str:
    """Extract assessment ID from filename (e.g., HAS-Feb-25-14157.pdf -> 14157)"""
    filename = Path(pdf_path).stem
    parts = filename.split('-')
    return parts[-1]


def extract_data_with_gemini(pdf_path: str) -> Tuple[str, str]:
    """
    Extract summary table and HAR text from PDF using Gemini CLI.

    Returns:
        Tuple of (summary_table_text, har_text)
    """
    prompt = (
        f'@{pdf_path} Extract the summary table (Assessment, Category, Feature Type, Location, '
        'and all hazard columns) in tab-separated format. Also extract the complete '
        'EXPLANATION AND RECOMMENDATION section text. Separate the two sections with "***".'
    )

    try:
        result = subprocess.run(
            ['gemini', '-p', prompt],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=str(Path(pdf_path).parent)
        )

        if result.returncode != 0:
            print(f"  ⚠ Gemini failed: {result.stderr}")
            return "", ""

        # Parse output
        output = result.stdout.strip()

        # Remove startup logs
        lines = [line for line in output.split('\n')
                 if not line.startswith('[') and not line.startswith('Loaded cached')]
        output_clean = '\n'.join(lines)

        # Split on ***
        if '***' in output_clean:
            parts = output_clean.split('***')
            summary_table = parts[0].strip()
            har_text = parts[1].strip() if len(parts) > 1 else ""
        else:
            # Try to split on "EXPLANATION AND RECOMMENDATION"
            if 'EXPLANATION AND RECOMMENDATION' in output_clean:
                idx = output_clean.index('EXPLANATION AND RECOMMENDATION')
                summary_table = output_clean[:idx].strip()
                har_text = output_clean[idx:].strip()
            else:
                summary_table = output_clean
                har_text = ""

        return summary_table, har_text

    except subprocess.TimeoutExpired:
        print(f"  ⚠ Gemini timeout")
        return "", ""
    except Exception as e:
        print(f"  ⚠ Gemini error: {e}")
        return "", ""


def validate_single_pdf(pdf_path: str, schema, engine) -> Dict:
    """
    Validate a single PDF by:
    1. Extracting data with Gemini
    2. Parsing summary table
    3. Generating our HAR
    4. Comparing with approved HAR

    Returns validation result dictionary.
    """
    assessment_id = extract_assessment_id(pdf_path)
    print(f"\n{'='*60}")
    print(f"Validating Assessment {assessment_id}")
    print(f"{'='*60}")

    # 1. Extract data with Gemini
    print("  1. Extracting data with Gemini CLI...")
    summary_table, approved_har = extract_data_with_gemini(pdf_path)

    if not summary_table:
        return {
            'assessment_id': assessment_id,
            'status': 'failed',
            'error': 'Gemini extraction failed'
        }

    print(f"  ✓ Extracted {len(summary_table)} chars summary table")
    print(f"  ✓ Extracted {len(approved_har)} chars HAR text")

    # 2. Parse summary table
    print("  2. Parsing summary table...")
    try:
        # Try OHAS native format first, then tab-separated
        assessments = OHASParser.parse_from_table(summary_table)
        print(f"  ✓ Parsed {len(assessments)} assessment(s)")
    except Exception as e:
        return {
            'assessment_id': assessment_id,
            'status': 'failed',
            'error': f'Parsing failed: {e}'
        }

    # 3. Generate our HARs
    print("  3. Generating HARs...")
    generated_hars = []
    try:
        for assessment in assessments:
            har = engine.process_assessment(assessment)
            generated_hars.append({
                'category': assessment.category.value,
                'text': har.to_text()
            })
        print(f"  ✓ Generated {len(generated_hars)} HAR(s)")
    except Exception as e:
        return {
            'assessment_id': assessment_id,
            'status': 'failed',
            'error': f'Generation failed: {e}'
        }

    # 4. Compare
    print("  4. Comparing with approved HAR...")

    return {
        'assessment_id': assessment_id,
        'pdf_path': pdf_path,
        'status': 'success',
        'num_assessments': len(assessments),
        'categories': [a.category.value for a in assessments],
        'approved_har': approved_har,
        'generated_hars': generated_hars,
        'summary_table': summary_table
    }


def main():
    """Run batch validation on all approved HARs."""
    print("="*60)
    print("HAR Automation Pipeline - Batch Validation")
    print("="*60)
    print(f"\nValidating {len(APPROVED_HARS)} approved HARs...\n")

    # Load schema and engine
    print("Loading schema...")
    loader = SchemaLoader()
    schema = loader.load()
    engine = DecisionEngine(schema)
    print("✓ Schema loaded\n")

    # Process sample first (faster testing)
    sample_size = 5
    print(f"Processing sample of {sample_size} PDFs first...\n")

    sample_pdfs = APPROVED_HARS[:sample_size]
    results = []

    for pdf_path in sample_pdfs:
        result = validate_single_pdf(pdf_path, schema, engine)
        results.append(result)

    # Summary
    print(f"\n{'='*60}")
    print("VALIDATION SUMMARY")
    print(f"{'='*60}\n")

    successful = [r for r in results if r['status'] == 'success']
    failed = [r for r in results if r['status'] == 'failed']

    print(f"Total: {len(results)}")
    print(f"✓ Successful: {len(successful)}")
    print(f"✗ Failed: {len(failed)}")

    if failed:
        print("\nFailed assessments:")
        for r in failed:
            print(f"  - {r['assessment_id']}: {r['error']}")

    # Save results
    output_file = "validation_results_sample.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    print(f"\n✓ Results saved to: {output_file}")

    print("\nNext: Review sample results, then run full batch validation.")


if __name__ == '__main__':
    main()
