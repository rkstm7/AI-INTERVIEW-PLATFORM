from flask import Blueprint, request, render_template, redirect, url_for, flash
from datetime import datetime
from flask_login import login_required
from models.model import db, JobRole, LearningResource

manage_resources_bp = Blueprint("manage_resources", __name__, url_prefix="/admin")


# Manage resources (View + Add)
@manage_resources_bp.route("/resources", methods=["GET", "POST"])
@login_required
def resources():
    if request.method == "POST":
        job_role_id = request.form["job_role"]
        title = request.form["title"]
        description = request.form.get("description", "")
        url = request.form["url"]

        resource = LearningResource(
            job_role_id=job_role_id,
            title=title,
            description=description,
            url=url,
            created_at=datetime.now(),
        )
        db.session.add(resource)
        db.session.commit()

        flash("Resource added!", "success")
        return redirect(url_for("manage_resources.resources"))

    job_roles = JobRole.query.order_by(JobRole.name).all()

    # Query resources with job role name
    query = (
        db.session.query(LearningResource, JobRole.name.label("job_role_name"))
        .join(JobRole, LearningResource.job_role_id == JobRole.id)
        .order_by(LearningResource.created_at.desc())
        .all()
    )

    # Convert tuples to dicts for template
    resources = [
        {
            "id": res.id,
            "title": res.title,
            "description": res.description,
            "url": res.url,
            "created_at": res.created_at.strftime("%Y-%m-%d %H:%M"),
            "job_role_name": job_role_name,
        }
        for res, job_role_name in query
    ]

    return render_template(
        "admin/resources/manage_resources.html",
        resources=resources,
        job_roles=job_roles,
    )


# Edit resource
@manage_resources_bp.route("/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_resource(id):
    resource = LearningResource.query.get_or_404(id)

    if request.method == "POST":
        resource.job_role_id = request.form["job_role"]
        resource.title = request.form["title"]
        resource.description = request.form.get("description", "")
        resource.url = request.form["url"]

        db.session.commit()
        flash("Resource updated!", "success")
        return redirect(url_for("manage_resources.resources"))

    job_roles = JobRole.query.order_by(JobRole.name).all()

    return render_template(
        "admin/resources/edit_resource.html", resource=resource, job_roles=job_roles
    )


# Delete resource
@manage_resources_bp.route("/delete/<int:id>", methods=["POST"])
@login_required
def delete_resource(id):
    resource = LearningResource.query.get_or_404(id)
    db.session.delete(resource)
    db.session.commit()

    flash("Resource deleted.", "success")
    return redirect(url_for("manage_resources.resources"))
