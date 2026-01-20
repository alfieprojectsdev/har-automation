from flask import Blueprint, render_template

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Main HAR generator page."""
    return render_template('index.html')

@main_bp.route('/health')
def health():
    """Health check endpoint."""
    return {'status': 'ok', 'version': '1.0'}
