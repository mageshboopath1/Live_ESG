-- Authentication and API Key Management Tables
-- This migration adds user authentication and API key management support

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    is_active INTEGER DEFAULT 1 CHECK (is_active IN (0, 1)),
    is_admin INTEGER DEFAULT 0 CHECK (is_admin IN (0, 1)),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for users table
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);

-- Create api_keys table
CREATE TABLE IF NOT EXISTS api_keys (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    key_name VARCHAR(100) NOT NULL,
    key_hash VARCHAR(255) NOT NULL UNIQUE,
    key_prefix VARCHAR(20) NOT NULL,
    scopes JSONB DEFAULT '[]'::jsonb,
    is_active INTEGER DEFAULT 1 CHECK (is_active IN (0, 1)),
    last_used_at TIMESTAMP,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for api_keys table
CREATE INDEX IF NOT EXISTS idx_api_keys_user_id ON api_keys(user_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_key_hash ON api_keys(key_hash);
CREATE INDEX IF NOT EXISTS idx_api_keys_is_active ON api_keys(is_active);
CREATE INDEX IF NOT EXISTS idx_api_keys_expires_at ON api_keys(expires_at);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers for updated_at
DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_api_keys_updated_at ON api_keys;
CREATE TRIGGER update_api_keys_updated_at
    BEFORE UPDATE ON api_keys
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Insert a default admin user for testing (password: admin123)
-- Password hash is SHA-256 of "admin123"
INSERT INTO users (username, email, hashed_password, is_active, is_admin)
VALUES (
    'admin',
    'admin@esg-platform.local',
    '240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9',
    1,
    1
)
ON CONFLICT (username) DO NOTHING;

-- Insert a default regular user for testing (password: user123)
-- Password hash is SHA-256 of "user123"
INSERT INTO users (username, email, hashed_password, is_active, is_admin)
VALUES (
    'testuser',
    'user@esg-platform.local',
    '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92',
    1,
    0
)
ON CONFLICT (username) DO NOTHING;

-- Add comments for documentation
COMMENT ON TABLE users IS 'User accounts for authentication';
COMMENT ON TABLE api_keys IS 'API keys for programmatic access';
COMMENT ON COLUMN users.is_active IS '1 = active, 0 = inactive';
COMMENT ON COLUMN users.is_admin IS '1 = admin, 0 = regular user';
COMMENT ON COLUMN api_keys.is_active IS '1 = active, 0 = revoked';
COMMENT ON COLUMN api_keys.scopes IS 'JSON array of permission scopes';
COMMENT ON COLUMN api_keys.key_prefix IS 'First 8 characters of API key for identification';
