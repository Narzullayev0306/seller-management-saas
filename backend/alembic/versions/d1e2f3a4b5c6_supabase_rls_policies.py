"""supabase row-level security policies (defense in depth)

The application connects as the table owner / Supabase service role, which
bypasses RLS unless FORCE ROW LEVEL SECURITY is enabled, so these policies do
not change existing app behaviour. They lock down org-scoped tables for any
future direct database access via the Supabase anon/authenticated role
(user JWT -> auth.uid()).

Revision ID: d1e2f3a4b5c6
Revises: c1d2e3f4a5b6
Create Date: 2026-08-17 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'd1e2f3a4b5c6'
down_revision: Union[str, None] = 'c1d2e3f4a5b6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ORG_SCOPED_TABLES = [
    "products",
    "product_images",
    "brands",
    "reviews",
    "price_history",
    "back_in_stock_requests",
    "customers",
    "orders",
    "sellers",
    "sales",
    "inventory_movements",
    "suppliers",
    "roles",
    "audit_logs",
    "notifications",
]

USER_KEYED_TABLES = [
    "auth_tokens",
    "refresh_tokens",
]


def _auth_schema_exists() -> bool:
    bind = op.get_bind()
    exists = bind.execute(
        sa.text("SELECT to_regnamespace('auth') IS NOT NULL")
    ).scalar()
    return bool(exists)


def upgrade() -> None:
    # Supabase-only: policies rely on the auth schema (auth.uid()) that only
    # exists on Supabase. On plain Postgres deployments they are skipped.
    if not _auth_schema_exists():
        return
    op.execute(
        """
        CREATE OR REPLACE FUNCTION public.app_current_org_id() RETURNS uuid
        LANGUAGE sql STABLE SECURITY DEFINER AS
        $$ SELECT organization_id FROM public.users WHERE id = auth.uid() $$;
        """
    )

    # ---- organizations: the row itself is the caller's org ---------------
    op.execute("ALTER TABLE organizations ENABLE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY org_select ON organizations
        FOR SELECT TO authenticated
        USING (id = public.app_current_org_id())
        """
    )
    op.execute(
        """
        CREATE POLICY org_update ON organizations
        FOR UPDATE TO authenticated
        USING (id = public.app_current_org_id())
        WITH CHECK (id = public.app_current_org_id())
        """
    )

    # ---- users: org-scoped via the app helper -----------------------------
    op.execute("ALTER TABLE users ENABLE ROW LEVEL SECURITY")
    for action, suffix, clause in [
        ("SELECT", "select", "USING (organization_id = public.app_current_org_id())"),
        ("INSERT", "insert", "WITH CHECK (organization_id = public.app_current_org_id())"),
        (
            "UPDATE",
            "update",
            "USING (organization_id = public.app_current_org_id()) "
            "WITH CHECK (organization_id = public.app_current_org_id())",
        ),
        ("DELETE", "delete", "USING (organization_id = public.app_current_org_id())"),
    ]:
        op.execute(
            f"CREATE POLICY users_{suffix} ON users FOR {action} TO authenticated {clause}"
        )

    # ---- direct org-scoped tables ----------------------------------------
    for table in ORG_SCOPED_TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        for action, suffix, clause in [
            ("SELECT", "select", "USING (organization_id = public.app_current_org_id())"),
            ("INSERT", "insert", "WITH CHECK (organization_id = public.app_current_org_id())"),
            (
                "UPDATE",
                "update",
                "USING (organization_id = public.app_current_org_id()) "
                "WITH CHECK (organization_id = public.app_current_org_id())",
            ),
            ("DELETE", "delete", "USING (organization_id = public.app_current_org_id())"),
        ]:
            op.execute(
                f"CREATE POLICY {table}_{suffix} ON {table} "
                f"FOR {action} TO authenticated {clause}"
            )

    # ---- user-keyed tables ------------------------------------------------
    for table in USER_KEYED_TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(
            f"CREATE POLICY {table}_select ON {table} FOR SELECT TO authenticated "
            "USING (user_id = auth.uid())"
        )
        op.execute(
            f"CREATE POLICY {table}_insert ON {table} FOR INSERT TO authenticated "
            "WITH CHECK (user_id = auth.uid())"
        )
        op.execute(
            f"CREATE POLICY {table}_update ON {table} FOR UPDATE TO authenticated "
            "USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid())"
        )
        op.execute(
            f"CREATE POLICY {table}_delete ON {table} FOR DELETE TO authenticated "
            "USING (user_id = auth.uid())"
        )

    # ---- order_items: scoped through the parent order ---------------------
    op.execute("ALTER TABLE order_items ENABLE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY order_items_select ON order_items FOR SELECT TO authenticated
        USING (
            order_id IN (
                SELECT id FROM orders
                WHERE organization_id = public.app_current_org_id()
            )
        )
        """
    )
    op.execute(
        """
        CREATE POLICY order_items_insert ON order_items FOR INSERT TO authenticated
        WITH CHECK (
            order_id IN (
                SELECT id FROM orders
                WHERE organization_id = public.app_current_org_id()
            )
        )
        """
    )
    op.execute(
        """
        CREATE POLICY order_items_update ON order_items FOR UPDATE TO authenticated
        USING (
            order_id IN (
                SELECT id FROM orders
                WHERE organization_id = public.app_current_org_id()
            )
        )
        WITH CHECK (
            order_id IN (
                SELECT id FROM orders
                WHERE organization_id = public.app_current_org_id()
            )
        )
        """
    )
    op.execute(
        """
        CREATE POLICY order_items_delete ON order_items FOR DELETE TO authenticated
        USING (
            order_id IN (
                SELECT id FROM orders
                WHERE organization_id = public.app_current_org_id()
            )
        )
        """
    )

    # ---- user_roles: caller's own rows ------------------------------------
    op.execute("ALTER TABLE user_roles ENABLE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY user_roles_select ON user_roles FOR SELECT TO authenticated "
        "USING (user_id = auth.uid())"
    )
    op.execute(
        "CREATE POLICY user_roles_insert ON user_roles FOR INSERT TO authenticated "
        "WITH CHECK (user_id = auth.uid())"
    )
    op.execute(
        "CREATE POLICY user_roles_update ON user_roles FOR UPDATE TO authenticated "
        "USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid())"
    )
    op.execute(
        "CREATE POLICY user_roles_delete ON user_roles FOR DELETE TO authenticated "
        "USING (user_id = auth.uid())"
    )


def downgrade() -> None:
    tables = ORG_SCOPED_TABLES + USER_KEYED_TABLES + [
        "organizations",
        "users",
        "order_items",
        "user_roles",
    ]
    for table in tables:
        for suffix in ("select", "insert", "update", "delete"):
            op.execute(f"DROP POLICY IF EXISTS {table}_{suffix} ON {table}")
    for table in tables:
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")
    op.execute("DROP FUNCTION IF EXISTS public.app_current_org_id()")