"""Add status to alerts.

Revision ID: 20260915_add_alert_status
Revises: 
Create Date: 2026-09-15
"""

from alembic import op
import sqlalchemy as sa


revision = "20260915_add_alert_status"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "alerts",
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default=sa.text("'new'"),
        ),
    )
    op.alter_column("alerts", "status", server_default=None)
    op.create_index("idx_alert_status", "alerts", ["status"])


def downgrade() -> None:
    op.drop_index("idx_alert_status", table_name="alerts")
    op.drop_column("alerts", "status")