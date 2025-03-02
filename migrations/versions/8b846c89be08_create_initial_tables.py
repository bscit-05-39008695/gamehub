"""Create initial tables

Revision ID: 8b846c89be08
Revises: 
Create Date: 2025-03-02 11:41:13.739558

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from datetime import datetime


# revision identifiers, used by Alembic.
revision: str = '8b846c89be08'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('username', sa.String(50), unique=True, nullable=False),
        sa.Column('email', sa.String(100), unique=True, nullable=False),
        sa.Column('password', sa.String(255), nullable=False),
        sa.Column('balance', sa.Float(), default=0.0),
        sa.Column('created_at', sa.DateTime(), default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime(), default=datetime.utcnow),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create games table
    op.create_table(
        'games',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(50), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('min_bet', sa.Float(), default=0.0),
        sa.Column('max_bet', sa.Float()),
        sa.Column('created_at', sa.DateTime(), default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime(), default=datetime.utcnow),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create multiplayer table
    op.create_table(
        'multiplayer',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('max_players', sa.Integer(), nullable=False),
        sa.Column('current_players', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('created_at', sa.DateTime(), default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime(), default=datetime.utcnow),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create transactions table
    op.create_table(
        'transactions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('type', sa.String(20), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('created_at', sa.DateTime(), default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime(), default=datetime.utcnow),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create game_sessions table
    op.create_table(
        'game_sessions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('game_id', sa.Integer(), nullable=False),
        sa.Column('multiplayer_id', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('created_at', sa.DateTime(), default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime(), default=datetime.utcnow),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['game_id'], ['games.id']),
        sa.ForeignKeyConstraint(['multiplayer_id'], ['multiplayer.id']),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create spin_and_win table
    op.create_table(
        'spin_and_win',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('bet_amount', sa.Float(), nullable=False),
        sa.Column('win_amount', sa.Float(), nullable=False),
        sa.Column('result', sa.String(20), nullable=False),
        sa.Column('created_at', sa.DateTime(), default=datetime.utcnow),
        sa.ForeignKeyConstraint(['session_id'], ['game_sessions.id']),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create russian_roulette table
    op.create_table(
        'russian_roulette',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('multiplayer_id', sa.Integer(), nullable=False),
        sa.Column('bullet_position', sa.Integer(), nullable=False),
        sa.Column('current_position', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('created_at', sa.DateTime(), default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime(), default=datetime.utcnow),
        sa.ForeignKeyConstraint(['multiplayer_id'], ['multiplayer.id']),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create bet_history table
    op.create_table(
        'bet_history',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('game_id', sa.Integer(), nullable=False),
        sa.Column('bet_amount', sa.Float(), nullable=False),
        sa.Column('win_amount', sa.Float(), default=0.0),
        sa.Column('net_result', sa.Float(), default=0.0),
        sa.Column('bet_type', sa.String(20), nullable=True),
        sa.Column('status', sa.String(20), default='completed'),
        sa.Column('created_at', sa.DateTime(), default=datetime.utcnow),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['game_id'], ['games.id']),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    # Drop tables in reverse order to avoid foreign key constraint issues
    op.drop_table('bet_history')
    op.drop_table('russian_roulette')
    op.drop_table('spin_and_win')
    op.drop_table('game_sessions')
    op.drop_table('transactions')
    op.drop_table('multiplayer')
    op.drop_table('games')
    op.drop_table('users')