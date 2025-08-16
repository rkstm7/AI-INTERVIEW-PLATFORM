from flask import Blueprint, request, render_template, redirect, url_for, flash
from extensions import db  # assume db = SQLAlchemy() in extensions.py
from models.model import Contact  # Contact model defined via SQLAlchemy

contact_bp = Blueprint('contact', __name__, url_prefix='/user')

@contact_bp.route('/', methods=['GET', 'POST'])
def user_contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')  # optional
        message = request.form.get('message')

        if not name or not email or not message:
            flash("Please fill out all required fields.", "danger")
            return redirect(url_for('contact.user_contact'))

        new_contact = Contact(name=name, email=email, phone=phone, message=message)
        db.session.add(new_contact)
        db.session.commit()

        flash("Thank you for contacting us! We'll get back to you soon.", "success")
        return redirect(url_for('contact.user_contact'))

    return render_template('user/contact/user_contact.html')
