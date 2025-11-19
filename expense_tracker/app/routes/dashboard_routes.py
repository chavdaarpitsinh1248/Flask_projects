from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from sqlalchemy import func
from app.models import Expense

dashboard_bp = Blueprint("dashboard", __name__, template_folder="../templates/dashboard")

# -----------------------------------------
#   Dashboard Main Page
# -----------------------------------------
@dashboard_bp.route("/")
@login_required
def dashboard_home():
    # Total spent
    total_spent = (
        Expense.query.with_entities(func.sum(Expense.amount))
        .filter_by(user_id=current_user.id)
        .scalar()
    ) or 0

    # Today's spend
    today = datetime.today().date()
    today_spent = (
        Expense.query.with_entities(func.sum(Expense.amount))
        .filter_by(user_id=current_user.id)
        .filter(Expense.date == today)
        .scalar()
    ) or 0

    # Monthly spend
    month = today.month
    year = today.year

    monthly_spent = (
        Expense.query.with_entities(func.sum(Expense.amount))
        .filter_by(user_id=current_user.id)
        .filter(func.extract("month", Expense.date) == month)
        .filter(func.extract("year", Expense.date) == year)
        .scalar()
    ) or 0

    return render_template(
        "dashboard/index.html",
        total_spent = total_spent,
        today_spent = today_spent,
        monthly_spent = monthly_spent,
    )



# -----------------------------------------
#   API: Category Breakdown (Pie Chart)
# -----------------------------------------
@dashboard_bp.route("api/category-data")
@login_required
def category_data():
    rows = (
        Expense.query.with_entities(Expense.category, func.sum(Expense.amount))
        .filter_by(user_id=current_user.id)
        .group_by(Expense.category)
        .all()
    )

    labels = [row[0].capitalize() for row in rows]
    values = [float(row[1]) for row in rows]

    return jsonify({"labels": labels, "values": values})



# -----------------------------------------
#   API: Weekly Spending (Line Chart)
# -----------------------------------------
@dashboard_bp.route("/api/weekly-data")
@login_required
def weekly_data():
    rows = (
        Expense.query.with_entities(
            Expense.date, func.sum(Expense.amount)
        )
        .filter_by(user_id=current_user.id)
        .group_by(Expense.date)
        .order_by(Expense.date.asc())
        .all()
    )

    labels = [r[0].strftime("%Y-%m-%d") for r in rows]
    values = [float(r[1]) for r in rows]

    return jsonify({"labels": labels, "values": values})