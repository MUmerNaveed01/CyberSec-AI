-- PostgreSQL initialization script
-- Runs once when the container is first created

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Set sensible timezone
SET timezone = 'UTC';

-- Grant schema privileges
GRANT ALL PRIVILEGES ON DATABASE cybersecdb TO cybersec;
