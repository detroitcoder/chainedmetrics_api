"""Add a symbol column for each market and expected Reporting Date

Revision ID: 8de1ab3414af
Revises: 4c2be755eff7
Create Date: 2021-10-18 16:33:28.578703

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8de1ab3414af'
down_revision = '4c2be755eff7'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('market', sa.Column('metric_symbol', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('market', 'metric_symbol')
    # ### end Alembic commands ###
