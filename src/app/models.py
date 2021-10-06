from sqlalchemy.sql.expression import null
from flask_sqlalchemy import SQLAlchemy

from werkzeug.security import generate_password_hash, check_password_hash


db = SQLAlchemy()

class Market(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    closed = db.Column(db.Boolean)
    fiscal_period = db.Column(db.String, nullable=False)
    metric = db.Column(db.String, nullable=False)
    ticker = db.Column(db.String, nullable=False)
    value_string = db.Column(db.String, nullable=False)
    value = db.Column(db.Numeric)
    beat_address = db.Column(db.String)
    beat_price = db.Column(db.Numeric)
    miss_address = db.Column(db.String)
    broker_address = db.Column(db.String)
    miss_price = db.Column(db.Numeric)
    issued = db.Column(db.Integer)
    highlight_market = db.Column(db.Boolean, nullable=False, default=False)
    resolved_value = db.Column(db.Numeric)

    def __repr__(self):
        return f'<metric.Market> {self.ticker} | {self.fiscal_period} | {self.metric}'


class RequestAccess(db.Model):

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    full_name = db.Column(db.String(500), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    reason = db.Column(db.String(2000))
    company = db.Column(db.String(2000))

    def __repr__(self):
        return f'<metric.RequestAccess> {self.full_name} | {self.email}'

class User(db.Model):

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.Text, nullable=False, unique=True)
    admin = db.Column(db.Boolean, default=False, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.Text, nullable=False)
    last_name = db.Column(db.Text, nullable=False)
    active = db.Column(db.Boolean, nullable=False)
    created_on = db.Column(db.DateTime, nullable=True)


    def set_password(self, password):
        """Create hashed password."""

        self.password = generate_password_hash(
            password,
            method='sha256'
        )

    def check_password(self, password):
        """Check hashed password."""

        return check_password_hash(self.password, password)

    def __repr__(self):
        return '<User {}>'.format(self.email)
