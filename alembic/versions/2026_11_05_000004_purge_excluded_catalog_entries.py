"""Remove excluded Teva and Israeli catalog entries without erasing transaction history.

This is an intentionally irreversible catalog-data cleanup. Products referenced by
inventory, batches, or completed sale lines are retained as inactive records so
stock traceability and financial/audit history remain intact.
"""

from alembic import op


revision = "2026_11_05_000004"
down_revision = "2026_11_05_000003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Normalized source payloads are flat records from RxNorm, EMA, and Health
    # Canada. Delete excluded source records regardless of their review status.
    op.execute(
        """
        DELETE FROM drug_catalog_source_records
        WHERE
            COALESCE(normalized_payload ->> 'brand_name', '') ILIKE '%teva%'
            OR COALESCE(normalized_payload ->> 'product_name', '') ILIKE '%teva%'
            OR COALESCE(normalized_payload ->> 'manufacturer', '') ILIKE '%teva%'
            OR COALESCE(normalized_payload ->> 'manufacturer_name', '') ILIKE '%teva%'
            OR COALESCE(normalized_payload ->> 'holder', '') ILIKE '%teva%'
            OR COALESCE(normalized_payload ->> 'company_name', '') ILIKE '%teva%'
            OR COALESCE(normalized_payload ->> 'labeler', '') ILIKE '%teva%'
            OR COALESCE(normalized_payload ->> 'country', '') ILIKE '%israel%'
            OR COALESCE(normalized_payload ->> 'country', '') ~* '(^|[^a-z])(il|isr)([^a-z]|$)'
            OR COALESCE(normalized_payload ->> 'authorization_country', '') ILIKE '%israel%'
            OR COALESCE(normalized_payload ->> 'authorization_country', '') ~* '(^|[^a-z])(il|isr)([^a-z]|$)'
            OR COALESCE(normalized_payload ->> 'manufacturer_country', '') ILIKE '%israel%'
            OR COALESCE(normalized_payload ->> 'manufacturer_country', '') ~* '(^|[^a-z])(il|isr)([^a-z]|$)'
            OR COALESCE(normalized_payload ->> 'country_of_origin', '') ILIKE '%israel%'
            OR COALESCE(normalized_payload ->> 'country_of_origin', '') ~* '(^|[^a-z])(il|isr)([^a-z]|$)'
            OR COALESCE(normalized_payload ->> 'country_of_manufacture', '') ILIKE '%israel%'
            OR COALESCE(normalized_payload ->> 'country_of_manufacture', '') ~* '(^|[^a-z])(il|isr)([^a-z]|$)'
            OR COALESCE(normalized_payload ->> 'country_of_production', '') ILIKE '%israel%'
            OR COALESCE(normalized_payload ->> 'country_of_production', '') ~* '(^|[^a-z])(il|isr)([^a-z]|$)'
            OR COALESCE(normalized_payload ->> 'origin_country', '') ILIKE '%israel%'
            OR COALESCE(normalized_payload ->> 'origin_country', '') ~* '(^|[^a-z])(il|isr)([^a-z]|$)'
        """
    )

    excluded_product_predicate = """
        (
            p.name ILIKE '%teva%'
            OR COALESCE(p.manufacturer, '') ILIKE '%teva%'
            OR lower(trim(COALESCE(p.manufacturer_country, ''))) IN
                ('il', 'isr', 'israel', 'state of israel', 'израиль', 'ізраїль')
            OR COALESCE(p.manufacturer_country, '') ILIKE '%israel%'
            OR COALESCE(p.manufacturer_country, '') ~* '(^|[^a-z])(il|isr)([^a-z]|$)'
            OR EXISTS (
                SELECT 1
                FROM medicinal_products mp
                WHERE mp.id = p.medicinal_product_id
                  AND (
                    COALESCE(mp.brand_name, '') ILIKE '%teva%'
                    OR COALESCE(mp.manufacturer, '') ILIKE '%teva%'
                    OR lower(trim(COALESCE(mp.authorization_country, ''))) IN
                        ('il', 'isr', 'israel', 'state of israel', 'израиль', 'ізраїль')
                    OR COALESCE(mp.authorization_country, '') ILIKE '%israel%'
                    OR COALESCE(mp.authorization_country, '') ~* '(^|[^a-z])(il|isr)([^a-z]|$)'
                    OR lower(trim(COALESCE(mp.manufacturer_country, ''))) IN
                        ('il', 'isr', 'israel', 'state of israel', 'израиль', 'ізраїль')
                    OR COALESCE(mp.manufacturer_country, '') ILIKE '%israel%'
                    OR COALESCE(mp.manufacturer_country, '') ~* '(^|[^a-z])(il|isr)([^a-z]|$)'
                  )
            )
        )
    """

    # Hide every excluded SKU immediately. Keep referenced rows so inventory,
    # lot, and sale history is never cascaded away by a catalog cleanup.
    op.execute(
        f"""
        UPDATE products AS p
        SET is_active = FALSE
        WHERE {excluded_product_predicate}
        """
    )

    # Physically remove only unused, zero-stock SKUs with no inventory, lot,
    # or sale-line references. All dependent/history-bearing rows are retained.
    op.execute(
        f"""
        DELETE FROM products AS p
        WHERE {excluded_product_predicate}
          AND COALESCE(p.stock, 0) = 0
          AND NOT EXISTS (SELECT 1 FROM inventory i WHERE i.product_id = p.id)
          AND NOT EXISTS (SELECT 1 FROM product_batches b WHERE b.product_id = p.id)
          AND NOT EXISTS (SELECT 1 FROM sale_items si WHERE si.product_id = p.id)
          AND NOT EXISTS (SELECT 1 FROM prescriptions rx WHERE rx.product_id = p.id)
        """
    )

    # Remove excluded global catalog variants. Product.medicinal_product_id
    # and source-record match FKs use ON DELETE SET NULL.
    op.execute(
        """
        WITH deleted_products AS (
            DELETE FROM medicinal_products mp
            WHERE
                COALESCE(mp.brand_name, '') ILIKE '%teva%'
                OR COALESCE(mp.manufacturer, '') ILIKE '%teva%'
                OR lower(trim(COALESCE(mp.authorization_country, ''))) IN
                    ('il', 'isr', 'israel', 'state of israel', 'израиль', 'ізраїль')
                OR COALESCE(mp.authorization_country, '') ILIKE '%israel%'
                OR COALESCE(mp.authorization_country, '') ~* '(^|[^a-z])(il|isr)([^a-z]|$)'
                OR lower(trim(COALESCE(mp.manufacturer_country, ''))) IN
                    ('il', 'isr', 'israel', 'state of israel', 'израиль', 'ізраїль')
                OR COALESCE(mp.manufacturer_country, '') ILIKE '%israel%'
                OR COALESCE(mp.manufacturer_country, '') ~* '(^|[^a-z])(il|isr)([^a-z]|$)'
            RETURNING mp.drug_reference_id
        ),
        excluded_references AS (
            SELECT DISTINCT drug_reference_id
            FROM deleted_products
        )
        DELETE FROM drug_references dr
        USING excluded_references er
        WHERE dr.id = er.drug_reference_id
          AND NOT EXISTS (
              SELECT 1
              FROM medicinal_products remaining
              WHERE remaining.drug_reference_id = dr.id
          )
        """
    )


def downgrade() -> None:
    # Catalog rows intentionally removed by this data migration cannot be
    # reconstructed. Transactional and inventory history was retained.
    pass
