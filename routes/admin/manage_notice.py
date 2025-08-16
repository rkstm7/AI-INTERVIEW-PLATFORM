from flask import Blueprint, request, redirect, url_for, flash, render_template
from flask_login import login_required, current_user
from datetime import datetime
from models.model import db, Notice

manage_notice_bp = Blueprint("manage_notice", __name__, url_prefix="/admin")


# Admin: Add / Edit / View Notices
@manage_notice_bp.route("/notice", methods=["GET", "POST"])
@login_required
def notice():
    if not current_user.is_admin():
        flash("Unauthorized access!", "danger")
        return redirect(url_for("notice_bp.notice"))

    if request.method == "POST":
        notice_id = request.form.get("notice_id")
        title = request.form.get("title")
        description = request.form.get("description")
        url = request.form.get("url")

        if not title or not description:
            flash("Title and Description are required.", "warning")
            return redirect(url_for("manage_notice.notice"))

        if notice_id:  # Update existing notice
            notice = Notice.query.get(notice_id)
            if notice:
                notice.title = title
                notice.description = description
                notice.url = url
                db.session.commit()
                flash("Notice updated successfully.", "success")
            else:
                flash("Notice not found.", "danger")
        else:  # Add new notice
            new_notice = Notice(
                title=title,
                description=description,
                url=url,
                created_at=datetime.utcnow(),
            )
            db.session.add(new_notice)
            db.session.commit()
            flash("Notice added successfully.", "success")

        return redirect(url_for("manage_notice.notice"))

    # GET all notices, newest first
    notices = Notice.query.order_by(Notice.id.desc()).all()
    return render_template("admin/notice/manage_notice.html", notices=notices)


# Admin: Delete a Notice
@manage_notice_bp.route("/delete_notice/<int:notice_id>", methods=["POST"])
@login_required
def delete_notice(notice_id):
    if not current_user.is_admin():
        flash("Unauthorized access!", "danger")
        return redirect(url_for("notice_bp.notice"))

    notice = Notice.query.get(notice_id)
    if notice:
        db.session.delete(notice)
        db.session.commit()
        flash("Notice deleted successfully.", "success")
    else:
        flash("Notice not found.", "danger")

    return redirect(url_for("manage_notice.notice"))
