import sqlite3

import backend.catalog.product_profiles as profiles


def create_legacy_schema(connection):
    connection.executescript(
        """
        PRAGMA foreign_keys = ON;

        CREATE TABLE documents (
            id TEXT PRIMARY KEY
        );

        CREATE TABLE product_profiles (
            product_id TEXT PRIMARY KEY,
            product_type TEXT,
            primary_entity TEXT,
            entities_json TEXT NOT NULL DEFAULT '[]',
            materials_json TEXT NOT NULL DEFAULT '[]',
            usages_json TEXT NOT NULL DEFAULT '[]',
            traditions_json TEXT NOT NULL DEFAULT '[]',
            synonyms_json TEXT NOT NULL DEFAULT '[]',
            keywords_json TEXT NOT NULL DEFAULT '[]',
            source_hash TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (product_id)
                REFERENCES documents(id)
                ON DELETE CASCADE
        );

        INSERT INTO documents (id) VALUES ('product-1');

        INSERT INTO product_profiles (
            product_id,
            product_type,
            primary_entity,
            created_at,
            updated_at
        )
        VALUES (
            'product-1',
            'statue',
            'Белая Тара',
            '2026-01-01',
            '2026-01-01'
        );
        """
    )


def test_migration_removes_foreign_key_and_preserves_rows():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    create_legacy_schema(connection)

    profiles._migrate_product_profiles_without_foreign_key(connection)

    assert connection.execute(
        "PRAGMA foreign_key_list(product_profiles)"
    ).fetchall() == []

    row = connection.execute(
        "SELECT * FROM product_profiles"
    ).fetchone()

    assert row["product_id"] == "product-1"
    assert row["product_type"] == "statue"
    assert row["primary_entity"] == "Белая Тара"


def test_profile_without_document_can_be_inserted():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    create_legacy_schema(connection)

    profiles._migrate_product_profiles_without_foreign_key(connection)

    connection.execute(
        """
        INSERT INTO product_profiles (
            product_id,
            created_at,
            updated_at
        )
        VALUES (
            'product-without-document',
            '2026-01-01',
            '2026-01-01'
        )
        """
    )

    row = connection.execute(
        """
        SELECT product_id
        FROM product_profiles
        WHERE product_id = 'product-without-document'
        """
    ).fetchone()

    assert row["product_id"] == "product-without-document"
