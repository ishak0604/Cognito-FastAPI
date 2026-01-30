-- Database initialization script
-- This script runs when PostgreSQL container starts for the first time

-- Create extensions if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create application user (if different from default)
-- DO $$ 
-- BEGIN
--     IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'app_user') THEN
--         CREATE ROLE app_user WITH LOGIN PASSWORD 'secure_password';
--         GRANT CONNECT ON DATABASE fastapi_db TO app_user;
--         GRANT USAGE ON SCHEMA public TO app_user;
--         GRANT CREATE ON SCHEMA public TO app_user;
--     END IF;
-- END
-- $$;

-- Set timezone
SET timezone = 'UTC';

-- Log initialization
SELECT 'Database initialized successfully' AS status;