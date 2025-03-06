"""Initial migration

Revision ID: b7964ac258e4
Revises: 8640c61297c6
Create Date: 2025-03-03 13:06:24.489779

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b7964ac258e4'
down_revision: Union[str, None] = '8640c61297c6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('multiplayer', 'game_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('multiplayer', 'game_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    # ### end Alembic commands ###
