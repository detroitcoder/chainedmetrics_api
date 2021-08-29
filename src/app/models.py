from sqlalchemy.sql.expression import null
from flask_sqlalchemy import SQLAlchemy
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
    miss_price = db.Column(db.Numeric)
    issued = db.Column(db.Integer)
    highlight_market = db.Column(db.Boolean, nullable=False, default=False)

    def __repr__(self):
        return f'<metric.Market> {self.ticker} | {self.fiscal_period} | {self.metric}>'

