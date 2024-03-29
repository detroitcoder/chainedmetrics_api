"""Add Column for broker

Revision ID: 599c122f2c73
Revises: 48ce5780e562
Create Date: 2021-09-06 19:29:21.376398

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '599c122f2c73'
down_revision = '48ce5780e562'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('market', sa.Column('broker_address', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('market', 'broker_address')
    # ### end Alembic commands ###
