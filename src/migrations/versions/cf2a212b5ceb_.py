"""empty message

Revision ID: cf2a212b5ceb
Revises: 65d911b95a1f
Create Date: 2022-03-03 18:18:45.852564

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'cf2a212b5ceb'
down_revision = '65d911b95a1f'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('market', sa.Column('tick_size', sa.Numeric(), nullable=True))
    op.add_column('market', sa.Column('unit_abbr', sa.String(), nullable=True))
    op.add_column('market', sa.Column('unit_desc', sa.String(), nullable=True))
    op.add_column('market', sa.Column('company_name', sa.String(), nullable=True))
    op.add_column('market', sa.Column('about', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('market', 'about')
    op.drop_column('market', 'company_name')
    op.drop_column('market', 'unit_desc')
    op.drop_column('market', 'unit_abbr')
    op.drop_column('market', 'tick_size')
    # ### end Alembic commands ###
