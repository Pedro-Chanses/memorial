"""Видалення таблиць, пов'язаних з клубом

Revision ID: remove_club_tables
Revises: 
Create Date: 2025-04-12 11:03:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'remove_club_tables'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Видаляємо таблиці, пов'язані з клубом
    op.drop_table('event_participant')
    op.drop_table('achievement')
    op.drop_table('event')
    op.drop_table('branch')
    
    # Видаляємо зайві поля з таблиці user
    op.drop_column('user', 'is_coach')
    op.drop_column('user', 'belt_rank')
    op.drop_column('user', 'branch_id')
    
    # Видаляємо зайві поля з таблиці image
    op.drop_column('image', 'event_id')
    op.drop_column('image', 'branch_id')


def downgrade():
    # Відновлення таблиць не підтримується
    pass
