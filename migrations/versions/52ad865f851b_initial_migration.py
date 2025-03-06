"""Initial migration

Revision ID: 52ad865f851b
Revises: 3a04e122fab7
Create Date: 2025-03-03 14:29:07.199407

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '52ad865f851b'
down_revision: Union[str, None] = '3a04e122fab7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('game_sessions', 'status',
               existing_type=sa.VARCHAR(length=20),
               type_=sa.String(length=50),
               nullable=True)
    op.drop_column('game_sessions', 'created_at')
    op.drop_column('game_sessions', 'updated_at')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('game_sessions', sa.Column('updated_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=True))
    op.add_column('game_sessions', sa.Column('created_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=True))
    op.alter_column('game_sessions', 'status',
               existing_type=sa.String(length=50),
               type_=sa.VARCHAR(length=20),
               nullable=False)
    # ### end Alembic commands ###
