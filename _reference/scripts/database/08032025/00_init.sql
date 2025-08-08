-- Initial database setup
-- This file just ensures the database exists and has proper extensions
-- Alembic will create all the tables

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- That's it! Let Alembic handle the rest