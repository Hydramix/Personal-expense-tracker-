from flask import Flask, render_template, request, redirect, url_for, flash
from models import db, Expense, Budget
from analytics import get_analytics
from datetime import datetime, date
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///finance.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'finance_secret_key'
app.config['STATIC_FOLDER'] = 'static'

db.init_app(app)

CATEGORIES = ['Food', 'Transport', 'Bills', 'Shopping', 'Health',
              'Entertainment', 'Travel', 'Education', 'Other']



@app.route("/", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # For now, we just redirect to the index. 
        # Later, you can add 'username' and 'password' validation here.
        return redirect(url_for('index'))
    
    return render_template("login.html")




@app.route('/home')
def index():
    month_filter = request.args.get('month', datetime.now().strftime('%Y-%m'))
    cat_filter   = request.args.get('category', 'All')

    query = Expense.query
    if month_filter:
        year, mon = month_filter.split('-')
        query = query.filter(
            db.extract('year',  Expense.date) == int(year),
            db.extract('month', Expense.date) == int(mon)
        )
    if cat_filter != 'All':
        query = query.filter(Expense.category == cat_filter)

    expenses = query.order_by(Expense.date.desc()).all()
    budget   = Budget.query.filter_by(month=month_filter).first()

    total_spent  = sum(e.amount for e in
                       Expense.query.filter(
                           db.extract('year',  Expense.date) == int(month_filter.split('-')[0]),
                           db.extract('month', Expense.date) == int(month_filter.split('-')[1])
                       ).all())
    budget_amount = budget.amount if budget else 0
    remaining     = budget_amount - total_spent

    return render_template('index2.html',
        expenses=expenses,
        categories=CATEGORIES,
        month_filter=month_filter,
        cat_filter=cat_filter,
        total_spent=total_spent,
        budget_amount=budget_amount,
        remaining=remaining,
        budget_pct=min(100, int((total_spent / budget_amount * 100) if budget_amount > 0 else 0))
    )

'''
@app.route('/add', methods=['POST'])
def add():
    try:
        exp = Expense(
            description = request.form['description'],
            amount      = float(request.form['amount']),
            category    = request.form['category'],
            date        = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
        )
        db.session.add(exp)
        db.session.commit()
        flash('Expense added successfully!', 'success')
    except Exception as e:
        flash(f'Error adding expense: {e}', 'error')
    return redirect(url_for('index'))

'''
@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    exp = Expense.query.get_or_404(id)
    if request.method == 'POST':
        exp.description = request.form['description']
        exp.amount      = float(request.form['amount'])
        exp.category    = request.form['category']
        exp.date        = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
        db.session.commit()
        flash('Expense updated!', 'success')
        return redirect(url_for('index'))
    return render_template('edit.html', expense=exp, categories=CATEGORIES)

'''
@app.route('/delete/<int:id>', methods=['POST'])
def delete(id):
    exp = Expense.query.get_or_404(id)
    db.session.delete(exp)
    db.session.commit()
    flash('Expense deleted.', 'success')
    return redirect(url_for('index'))
'''




@app.route('/add', methods=['POST'])
def add():
    # Capture the month view from the hidden input
    view_month = request.form.get('view_month')
    try:
        # Create the expense object
        new_expense = Expense(
            description = request.form['description'],
            amount      = float(request.form['amount']),
            category    = request.form['category'],
            date        = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
        )
        db.session.add(new_expense)
        db.session.commit()
        flash('Expense added successfully!', 'success')
    except Exception as e:
        db.session.rollback() # Rollback if there is a database error
        flash(f'Error adding expense: {e}', 'error')
    
    # Redirect back to the month you were looking at 
    return redirect(url_for('index', month=view_month))

@app.route('/delete/<int:id>', methods=['POST'])
def delete(id):
    # 1. Find the expense first
    target_expense = Expense.query.get_or_404(id)
    
    # 2. Capture its month so we stay on the same page after deleting
    view_month = target_expense.date.strftime('%Y-%m')
    
    try:
        db.session.delete(target_expense)
        db.session.commit()
        flash('Expense deleted.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting: {e}', 'error')
        
    return redirect(url_for('index', month=view_month))

@app.route('/set-budget', methods=['POST'])
def set_budget():
    month  = request.form['month']
    amount = float(request.form['amount'])
    budget = Budget.query.filter_by(month=month).first()
    if budget:
        budget.amount = amount
    else:
        db.session.add(Budget(month=month, amount=amount))
    db.session.commit()
    flash('Budget saved!', 'success')
    return redirect(url_for('index', month=month))

@app.route('/dashboard')
def dashboard():
    month_filter = request.args.get('month', datetime.now().strftime('%Y-%m'))
    analytics    = get_analytics(month_filter)
    budget       = Budget.query.filter_by(month=month_filter).first()
    analytics['budget'] = budget.amount if budget else 0
    analytics['month_filter'] = month_filter
    return render_template('dashboard.html', **analytics)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Seed sample data if DB is empty
        if Expense.query.count() == 0:
            from datetime import timedelta
            import random
            samples = [
                ('Grocery Store',       1240, 'Food'),
                ('Electricity Bill',     850, 'Bills'),
                ('Uber Ride',            320, 'Transport'),
                ('Netflix',              649, 'Entertainment'),
                ('Pharmacy',             430, 'Health'),
                ('Amazon Order',        1890, 'Shopping'),
                ('Restaurant Dinner',    760, 'Food'),
                ('Internet Bill',        999, 'Bills'),
                ('Petrol',               600, 'Transport'),
                ('Movie Tickets',        500, 'Entertainment'),
                ('Gym Membership',       800, 'Health'),
                ('Books',                450, 'Education'),
                ('Flight Tickets',      3500, 'Travel'),
                ('Vegetables',           380, 'Food'),
                ('Mobile Recharge',      299, 'Bills'),
            ]
            today = date.today()
            for i, (desc, amt, cat) in enumerate(samples):
                d = today.replace(day=1) + timedelta(days=i)
                if d > today:
                    d = today
                db.session.add(Expense(description=desc, amount=amt, category=cat, date=d))
            db.session.add(Budget(month=today.strftime('%Y-%m'), amount=15000))
            db.session.commit()
    app.run(debug=True)
