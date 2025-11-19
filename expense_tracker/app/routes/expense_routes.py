from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from app.forms import ExpenseForm
from app.models import Expense
from app.extensions import db


expense_bp = Blueprint("expenses", __name__, template_folder="../templates/expenses")

# --------------------------------------------
#   List all expense (with filtering)
# --------------------------------------------
@expense_bp.route("/")
@login_required
def list_expenses():
    category_filter = request.args.get("category")
    start_date = request.args.get("start")
    end_date = request.args.get("end")

    query = Expense.query.filter_by(user_id=current_user.id)

    if category_filter:
        query = query.filter(Expense.category == category_filter)

    if start_date:
        query = query.filter(Expense.date >= start_date)

    if end_date:
        query = query.filter(Expense.date <= end_date)

    expenses = query.order_by(Expense.date.desc()).all()

    return render_template("expenses/list_expenses.html", expenses=expenses)

# --------------------------------------------
#   Add Expense
# --------------------------------------------
@expense_bp.route("/add", methods=["GET","POST"])
@login_required
def add_expense():
    form = ExpenseForm()

    if form.validate_on_submit():
        expense = Expense(
            amount=form.amount.data,
            category=form.category.data,
            date=form.date.data,
            note=form.note.data,
            user_id=current_user.id,
        )
        db.session.add(expense)
        db.session.commit()

        flash("Expense added!", "success")
        return redirect(url_for("expense.list_expenses"))

    return render_template("expenses/add_expense.html", form=form)


# --------------------------------------------
#   Edit Expense
# --------------------------------------------
@expense_bp.route("/<int:expense_id>/edit", methods=["GET", "POST"])
@login_required
def edit_expense(expense_id):
    expense = Expense.query.get_or_404(expense_id)

    if expense.user_id != current_user.id:
        return "Unauthorized", 403

    form = ExpenseForm(obj=expense)

    if form.validate_on_submit():
        expense.amount = form.amount.data
        expense.category = form.category.data
        expense.date = form.date.data
        expense.note = form.note.data

        db.session.commit()

        flash("Expense updated!", "success")
        return redirect(url_for("expense.list_expenses"))

    return render_template("expenses/edit_expense.html", form=form, expense=expense)



# --------------------------------------------
#   Delete Expense
# --------------------------------------------
@expense_bp.route("/<int:expense_id>/delete", methods=["POST"])
@login_required
def delete_expense(expense_id):
    expense = Expense.query.get_or_404(expense_id)

    if expense.user_id != current_user.id:
        return "Unauthorized", 403

    db.session.delete(expense)
    db.session.commit()

    flask("Expense deleted!", "success")
    return redirect(url_for("expense.list_expenses"))