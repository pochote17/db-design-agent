"""Test fixtures."""

import json

SAMPLE_CONTEXT = """
E-commerce marketplace where multiple sellers list products, manage inventory 
across warehouses, receive orders, process payments with transaction commissions, 
and need sales reports by seller, category, and period. Prices and commissions 
change over time and require history tracking.
"""

SAMPLE_SCHEMA_JSON = {
    "tables": [
        {
            "name": "sellers",
            "description": "Marketplace sellers",
            "columns": [
                {"name": "id", "type": "UUID", "nullable": False, "primary_key": True, "foreign_key": None, "description": "Seller ID", "default": "gen_random_uuid()"},
                {"name": "email", "type": "citext", "nullable": False, "primary_key": False, "foreign_key": None, "description": "Contact email", "default": None},
                {"name": "name", "type": "varchar(255)", "nullable": False, "primary_key": False, "foreign_key": None, "description": "Business name", "default": None},
                {"name": "commission_rate", "type": "numeric(5,4)", "nullable": False, "primary_key": False, "foreign_key": None, "description": "Current commission rate", "default": "0.10"},
                {"name": "created_at", "type": "timestamptz", "nullable": False, "primary_key": False, "foreign_key": None, "description": "Registration timestamp", "default": "now()"},
            ],
            "indexes": [
                {"name": "idx_sellers_email", "columns": ["email"], "unique": True, "where": None},
            ],
        },
        {
            "name": "products",
            "description": "Products listed by sellers",
            "columns": [
                {"name": "id", "type": "UUID", "nullable": False, "primary_key": True, "foreign_key": None, "description": "Product ID", "default": "gen_random_uuid()"},
                {"name": "seller_id", "type": "UUID", "nullable": False, "primary_key": False, "foreign_key": "sellers.id", "description": "Seller reference", "default": None},
                {"name": "name", "type": "varchar(255)", "nullable": False, "primary_key": False, "foreign_key": None, "description": "Product name", "default": None},
                {"name": "price", "type": "numeric(12,2)", "nullable": False, "primary_key": False, "foreign_key": None, "description": "Current price", "default": None},
                {"name": "category", "type": "varchar(100)", "nullable": False, "primary_key": False, "foreign_key": None, "description": "Product category", "default": None},
            ],
            "indexes": [
                {"name": "idx_products_seller", "columns": ["seller_id"], "unique": False, "where": None},
                {"name": "idx_products_category", "columns": ["category"], "unique": False, "where": None},
            ],
        },
    ],
    "relationships": [
        {"source_table": "products", "source_column": "seller_id", "target_table": "sellers", "target_column": "id", "cardinality": "N:1"},
    ],
}

SAMPLE_DDL = """CREATE TABLE sellers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email citext NOT NULL UNIQUE,
    name varchar(255) NOT NULL,
    commission_rate numeric(5,4) NOT NULL DEFAULT 0.10,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    seller_id UUID NOT NULL REFERENCES sellers(id) ON DELETE RESTRICT,
    name varchar(255) NOT NULL,
    price numeric(12,2) NOT NULL,
    category varchar(100) NOT NULL
);

CREATE INDEX idx_sellers_email ON sellers(email);
CREATE INDEX idx_products_seller ON products(seller_id);
CREATE INDEX idx_products_category ON products(category);

COMMENT ON TABLE sellers IS 'Marketplace sellers';
COMMENT ON TABLE products IS 'Products listed by sellers';
COMMENT ON COLUMN sellers.id IS 'Seller ID';
COMMENT ON COLUMN sellers.email IS 'Contact email';
COMMENT ON COLUMN sellers.name IS 'Business name';
COMMENT ON COLUMN sellers.commission_rate IS 'Current commission rate';
COMMENT ON COLUMN sellers.created_at IS 'Registration timestamp';
COMMENT ON COLUMN products.id IS 'Product ID';
COMMENT ON COLUMN products.seller_id IS 'Seller reference';
COMMENT ON COLUMN products.name IS 'Product name';
COMMENT ON COLUMN products.price IS 'Current price';
COMMENT ON COLUMN products.category IS 'Product category';
"""
