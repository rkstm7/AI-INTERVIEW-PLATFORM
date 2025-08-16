from flask import Blueprint, render_template

public_dashboard_bp = Blueprint('public_dashboard', __name__, url_prefix='/')

@public_dashboard_bp.route('/')
def dashboard():
    return render_template('public/dashboard/index.html')
