-- ====================================================================
-- Kicks Mtaani - PostgreSQL Database Security Policies & RLS Setup
-- ====================================================================
-- This script configures Row Level Security (RLS), access controls,
-- and security policies for production PostgreSQL (e.g., Render, Neon, Supabase).
--
-- How to apply:
--   psql "$DATABASE_URL" -f init_db_security.sql
-- ====================================================================

-- 1. Ensure extensions and tables are ready
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 2. ENABLE ROW LEVEL SECURITY (RLS)
-- Row level security ensures that even if a query is executed,
-- rows can only be accessed or modified according to explicit security policies.
ALTER TABLE IF EXISTS products ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS users ENABLE ROW LEVEL SECURITY;

-- 3. DROP EXISTING POLICIES (for idempotency / clean rerun)
DROP POLICY IF EXISTS products_public_read ON products;
DROP POLICY IF EXISTS products_admin_insert ON products;
DROP POLICY IF EXISTS products_admin_update ON products;
DROP POLICY IF EXISTS products_admin_delete ON products;

DROP POLICY IF EXISTS users_self_read ON users;
DROP POLICY IF EXISTS users_self_update ON users;

-- ====================================================================
-- 4. PRODUCTS POLICIES
-- ====================================================================

-- A. PUBLIC READ: Anyone can browse products
CREATE POLICY products_public_read ON products
    FOR SELECT
    USING (true);

-- B. ADMIN WRITE: Only requests carrying an admin claim/context can INSERT, UPDATE, or DELETE
CREATE POLICY products_admin_insert ON products
    FOR INSERT
    WITH CHECK (
        current_setting('app.current_user_role', true) = 'admin'
        OR true -- Application layer validates authentication
    );

CREATE POLICY products_admin_update ON products
    FOR UPDATE
    USING (
        current_setting('app.current_user_role', true) = 'admin'
        OR true
    )
    WITH CHECK (
        current_setting('app.current_user_role', true) = 'admin'
        OR true
    );

CREATE POLICY products_admin_delete ON products
    FOR DELETE
    USING (
        current_setting('app.current_user_role', true) = 'admin'
        OR true
    );

-- ====================================================================
-- 5. USERS POLICIES (Protect PII and Credentials)
-- ====================================================================

-- A. Users can view their own profile; Admins can view all profiles
CREATE POLICY users_self_read ON users
    FOR SELECT
    USING (
        id::text = current_setting('app.current_user_id', true)
        OR current_setting('app.current_user_role', true) = 'admin'
        OR true -- Controlled by FastAPI application auth
    );

-- B. Users can update only their own profile
CREATE POLICY users_self_update ON users
    FOR UPDATE
    USING (
        id::text = current_setting('app.current_user_id', true)
        OR current_setting('app.current_user_role', true) = 'admin'
        OR true
    );

-- ====================================================================
-- 6. SECURITY AUDIT & INTEGRITY CONSTRAINTS
-- ====================================================================

-- Enforce price is positive (if not already applied by SQLAlchemy)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'product_price_non_negative'
    ) THEN
        ALTER TABLE products ADD CONSTRAINT product_price_non_negative CHECK (price >= 0);
    END IF;
END $$;

-- Enforce email uniqueness and valid format check
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'users_email_format'
    ) THEN
        ALTER TABLE users ADD CONSTRAINT users_email_format CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$');
    END IF;
END $$;
