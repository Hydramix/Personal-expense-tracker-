from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Expense(db.Model):
    __tablename__ = 'expenses'
    id          = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(200), nullable=False)
    amount      = db.Column(db.Float, nullable=False)
    category    = db.Column(db.String(50), nullable=False)
    date        = db.Column(db.Date, nullable=False)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Expense {self.description} ₹{self.amount}>'

class Budget(db.Model):
    __tablename__ = 'budgets'
    id     = db.Column(db.Integer, primary_key=True)
    month  = db.Column(db.String(7), nullable=False, unique=True)  # 'YYYY-MM'
    amount = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f'<Budget {self.month} ₹{self.amount}>'
