"""add EndpointLogDB and CheaterDB table

Revision ID: 3996356a8091
Revises: 
Create Date: 2023-12-15 23:40:58.763929

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3996356a8091'
down_revision = None
branch_labels = None
depends_on = None


def upgrade(op=None):
    op.create_table(
        "endpointLog",
        sa.Column("id", sa.Integer, nullable=False, autoincrement=True),
        sa.Column("userid", sa.Integer, nullable=False),
        sa.Column("endpoint", sa.String(length=128), nullable=False),
        sa.ForeignKeyConstraint(["userid"], ["users.id"], ondelete="CASCADE", onupdate="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "cheater",
        sa.Column("id", sa.Integer, nullable=False, autoincrement=True),
        sa.Column("userid", sa.Integer, nullable=False),
        sa.Column("challengesid", sa.Integer, nullable=False),
        sa.ForeignKeyConstraint(["userid"], ["users.id"], ondelete="CASCADE", onupdate="CASCADE"),
        sa.ForeignKeyConstraint(["challengesid"], ["challenges.id"], ondelete="CASCADE", onupdate="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "fw_challenge",
        sa.Column("id", sa.Integer, nullable=False),
        sa.Column("endpoints", sa.JSON, nullable=False, default=[]),
        sa.ForeignKeyConstraint(["id"], ["challenges.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "fw_dynamic_challenge",
        sa.Column("id", sa.Integer, nullable=False),
        sa.Column("endpoints", sa.JSON, nullable=False, default=[]),
        sa.ForeignKeyConstraint(["id"], ["dynamic_challenge.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade(op=None) -> None:
    op.drop_table("endpointLog")
    op.drop_table("cheater")
    op.drop_table("fw_challenge")
    op.drop_table("fw_dynamic_challenge")

