-- Migration: Add product_recipes junction table and remove products.recipe_id
-- Run this against Neon BEFORE deploying the new code.

BEGIN;

-- 1. Create the junction table
CREATE TABLE IF NOT EXISTS product_recipes (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    recipe_id INTEGER NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,
    quantity_needed FLOAT DEFAULT 1.0,
    CONSTRAINT uq_product_recipe UNIQUE (product_id, recipe_id)
);

-- 2. Migrate existing product→recipe links
INSERT INTO product_recipes (product_id, recipe_id, quantity_needed)
SELECT id, recipe_id, 1.0
FROM products
WHERE recipe_id IS NOT NULL
ON CONFLICT DO NOTHING;

-- 3. Drop the old column
ALTER TABLE products DROP COLUMN IF EXISTS recipe_id;

COMMIT;
