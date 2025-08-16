# routes/user/legal_pages.py
from flask import Blueprint, render_template

legal_bp = Blueprint('legal', __name__, url_prefix='/user')

@legal_bp.route('/privacy_policy')
def privacy_policy():
    # You can replace this with render_template('user/legal/privacy_policy.html')
    return "Privacy Policy page (to be implemented)"

@legal_bp.route('/terms_of_service')
def terms_of_service():
    # You can replace this with render_template('user/legal/terms_of_service.html')
    return "Terms of Service page (to be implemented)"
