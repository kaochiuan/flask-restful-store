"""empty message

Revision ID: 69233168a099
Revises: 178695a29dca
Create Date: 2018-12-21 23:23:42.120840

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '69233168a099'
down_revision = '178695a29dca'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('menu', sa.Column('coffee_option', sa.Enum('coffee_one', 'coffee_two'), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('menu', 'coffee_option')
    # ### end Alembic commands ###
