"""empty message

Revision ID: aa80dddc2858
Revises: d04c9127ee7b
Create Date: 2022-07-09 21:52:45.411867

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'aa80dddc2858'
down_revision = 'd04c9127ee7b'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('avatar_s', sa.String(length=64), nullable=True))
    op.add_column('users', sa.Column('avatar_m', sa.String(length=64), nullable=True))
    op.add_column('users', sa.Column('avatar_l', sa.String(length=64), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'avatar_l')
    op.drop_column('users', 'avatar_m')
    op.drop_column('users', 'avatar_s')
    # ### end Alembic commands ###
