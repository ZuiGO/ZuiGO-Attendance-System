-- Enable core PostgreSQL extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "postgis";

-- Enable Row-Level Security setting configuration
-- Grant permission to access application custom settings
ALTER DATABASE zuigo_attendance SET "app.current_tenant_id" TO '';
