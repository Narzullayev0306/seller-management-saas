"""categories table + products.category_id with backfill

Revision ID: f9d0e1f2a3b4
Revises: f8c9d0e1f2a3
Create Date: 2026-08-19 13:00:00.000000

"""
import re
import unicodedata
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'f9d0e1f2a3b4'
down_revision: Union[str, None] = 'f8c9d0e1f2a3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _slugify(name: str) -> str:
    value = unicodedata.normalize("NFKD", name)
    value = value.encode("ascii", "ignore").decode("ascii").lower()
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    return value or "category"


def upgrade() -> None:
    op.create_table('categories',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('organization_id', sa.Uuid(), nullable=False),
    sa.Column('parent_id', sa.Uuid(), nullable=True),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('slug', sa.String(length=120), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('sort_order', sa.Integer(), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['parent_id'], ['categories.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_categories')),
    sa.UniqueConstraint('organization_id', 'slug', name='uq_categories_org_slug')
    )
    op.create_index(op.f('ix_categories_organization_id'), 'categories', ['organization_id'], unique=False)
    op.create_index('ix_categories_org_parent', 'categories', ['organization_id', 'parent_id'], unique=False)

    op.add_column('products', sa.Column('category_id', sa.Uuid(), nullable=True))
    op.create_index(op.f('ix_products_category_id'), 'products', ['category_id'], unique=False)
    op.create_foreign_key(
        op.f('fk_products_category_id_categories'), 'products', 'categories',
        ['category_id'], ['id'], ondelete='SET NULL'
    )

    conn = op.get_bind()
    categories_table = sa.table(
        'categories',
        sa.column('id', sa.Uuid()),
        sa.column('organization_id', sa.Uuid()),
        sa.column('name', sa.String()),
        sa.column('slug', sa.String()),
        sa.column('sort_order', sa.Integer()),
        sa.column('is_active', sa.Boolean()),
    )
    products_table = sa.table(
        'products',
        sa.column('id', sa.Uuid()),
        sa.column('organization_id', sa.Uuid()),
        sa.column('category', sa.String()),
        sa.column('category_id', sa.Uuid()),
    )

    rows = conn.execute(
        sa.select(products_table.c.organization_id, products_table.c.category)
        .where(products_table.c.category != None)  # noqa: E711
        .distinct()
    ).all()
    org_slugs: dict[tuple, int] = {}
    for org_id, name in rows:
        base = _slugify(name)
        n = org_slugs.get((org_id, base), 0) + 1
        org_slugs[(org_id, base)] = n
        slug = base if n == 1 else f"{base}-{n}"
        result = conn.execute(
            categories_table.insert().values(
                id=sa.func.gen_random_uuid(),
                organization_id=org_id,
                name=name,
                slug=slug,
                sort_order=0,
                is_active=True,
            ).returning(categories_table.c.id)
        )
        category_id = result.scalar_one()
        conn.execute(
            products_table.update()
            .where(
                products_table.c.organization_id == org_id,
                products_table.c.category == name,
                products_table.c.category_id == None,  # noqa: E711
            )
            .values(category_id=category_id)
        )


def downgrade() -> None:
    op.drop_constraint(op.f('fk_products_category_id_categories'), 'products', type_='foreignkey')
    op.drop_index(op.f('ix_products_category_id'), table_name='products')
    op.drop_column('products', 'category_id')
    op.drop_index('ix_categories_org_parent', table_name='categories')
    op.drop_index(op.f('ix_categories_organization_id'), table_name='categories')
    op.drop_table('categories')