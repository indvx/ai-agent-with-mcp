"""add user as default role

Revision ID: 8f5f8bbef5b5
Revises: 35b565596bc1
Create Date: 2026-06-06 14:14:53.132453

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8f5f8bbef5b5'
down_revision: Union[str, Sequence[str], None] = '35b565596bc1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("""
        UPDATE roles
        SET is_default = 1
        WHERE name = 'user'
    """)
    pass
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("""
        UPDATE roles
        SET is_default = 0
        WHERE name = 'user'
    """)
    pass
    # ### end Alembic commands ###
