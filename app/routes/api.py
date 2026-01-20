"""API routes for HAR generation"""

from flask import Blueprint, request, jsonify, current_app
import sys
from pathlib import Path

# Add decision engine to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.parser import OHASParser, SchemaLoader
from src.pipeline import DecisionEngine

api_bp = Blueprint('api', __name__)

# Security: Maximum input size to prevent DoS attacks
MAX_INPUT_SIZE = 10 * 1024  # 10 KB as per deployment plan

# Load schema once at startup
schema_loader = SchemaLoader()
schema = schema_loader.load()
engine = DecisionEngine(schema)


@api_bp.route('/generate', methods=['POST'])
def generate_har():
    """Generate HAR from summary table."""
    try:
        data = request.get_json()
        summary_table = data.get('summary_table', '').strip()

        if not summary_table:
            return jsonify({'error': 'No summary table provided'}), 400

        if len(summary_table) > MAX_INPUT_SIZE:
            return jsonify({
                'error': f'Input too large. Maximum {MAX_INPUT_SIZE} bytes allowed.'
            }), 400

        # Parse assessments
        assessments = OHASParser.parse_from_table(summary_table)

        # Generate HARs
        results = []
        for assessment in assessments:
            har = engine.process_assessment(assessment)
            results.append({
                'assessment_id': assessment.id,
                'category': assessment.category.value,
                'har_text': har.to_text()
            })

        return jsonify({'success': True, 'hars': results})

    except Exception as e:
        # Log full error server-side for debugging
        current_app.logger.error(f"HAR generation failed: {str(e)}", exc_info=True)

        # Return generic error to user
        return jsonify({
            'error': 'Failed to generate HAR. Please check input format.'
        }), 500
