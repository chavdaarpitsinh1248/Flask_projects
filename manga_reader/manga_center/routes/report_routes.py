
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from .. import db
from ..models import Report

report_bp = Blueprint("report", __name__)

@report_bp.route("/create/<string:target_type>/<int:target_id>", methods=["GET", "POST"])
@login_required
def create_report(target_type, target_id):
    """
    Allows any logged-in user to submit a report for a specific entity:
    - target_type can be 'manga', 'chapter', 'comment', or 'studio'
    - target_id is the ID of the target
    """
    if request.method == "POST":
        reason = request.form.get("reason", "").strip()
        details = request.form.get("details", "").strip()

        if not reason:
            flash("Please select a reason for your report.", "warning")
            return redirect(request.url)

        new_report = Report(
            user_id=current_user.id,
            target_type=target_type,
            target_id=target_id,
            reason=reason,
            details=details,
            status="pending"
        )

        db.session.add(new_report)
        db.session.commit()
        flash("Your report has been submitted successfully.", "success")
        return redirect(url_for("index"))

    return render_template("report/create_report.html", target_type=target_type, target_id=target_id)
