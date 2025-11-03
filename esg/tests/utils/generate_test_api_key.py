#!/usr/bin/env -S uv run --script
# /// script
# dependencies = [
#   "psycopg2-binary",
# ]
# ///
"""Generate a test API key for integration testing."""

import os
import secrets
import hashlib
from datetime import datetime, timedelta

import psycopg2
from psycopg2.extras import RealDictCursor


def generate_api_key() -> tuple[str, str, str]:
    """
    Generate a new API key.
    
    Returns:
        tuple: (full_key, key_hash, key_prefix)
    """
    # Generate 32 random bytes (256 bits)
    key_bytes = secrets.token_bytes(32)
    full_key = key_bytes.hex()
    
    # Hash the key for storage
    key_hash = hashlib.sha256(full_key.encode()).hexdigest()
    
    # Get prefix (first 8 chars) for identification
    key_prefix = full_key[:8]
    
    return full_key, key_hash, key_prefix


def create_test_user_and_api_key():
    """Create a test user and API key in the database."""
    
    # Database connection
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        database=os.getenv("DB_NAME", "moz"),
        user=os.getenv("DB_USER", "drfitz"),
        password=os.getenv("DB_PASSWORD", "h4i1hydr4")
    )
    
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Check if test user already exists
        cur.execute("SELECT id FROM users WHERE username = 'test_user'")
        user = cur.fetchone()
        
        if not user:
            # Create test user (password hash is for "test_password")
            password_hash = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqNqYqNqYq"
            cur.execute("""
                INSERT INTO users (username, email, hashed_password, is_active, is_admin)
                VALUES ('test_user', 'test@example.com', %s, 1, 1)
                RETURNING id
            """, (password_hash,))
            user = cur.fetchone()
            conn.commit()
            print(f"✓ Created test user with id={user['id']}")
        else:
            print(f"✓ Test user already exists with id={user['id']}")
        
        user_id = user['id']
        
        # Check if test API key already exists
        cur.execute("SELECT id, key_prefix FROM api_keys WHERE user_id = %s AND key_name = 'test_api_key'", (user_id,))
        existing_key = cur.fetchone()
        
        if existing_key:
            print(f"✓ Test API key already exists with prefix={existing_key['key_prefix']}")
            print("\nTo use this key, you need to retrieve it from the database or regenerate it.")
            print("Regenerating a new test API key...")
            
            # Delete old key
            cur.execute("DELETE FROM api_keys WHERE id = %s", (existing_key['id'],))
            conn.commit()
        
        # Generate new API key
        full_key, key_hash, key_prefix = generate_api_key()
        
        # Set expiration to 1 year from now
        expires_at = datetime.utcnow() + timedelta(days=365)
        
        # Insert API key
        cur.execute("""
            INSERT INTO api_keys (
                user_id, key_name, key_hash, key_prefix, 
                scopes, is_active, expires_at
            )
            VALUES (%s, %s, %s, %s, %s, 1, %s)
            RETURNING id
        """, (
            user_id,
            'test_api_key',
            key_hash,
            key_prefix,
            '["read", "write"]',
            expires_at
        ))
        
        api_key_record = cur.fetchone()
        conn.commit()
        
        print(f"\n{'='*70}")
        print("✓ Successfully created test API key!")
        print(f"{'='*70}")
        print(f"\nAPI Key ID: {api_key_record['id']}")
        print(f"Key Prefix: {key_prefix}")
        print(f"Expires: {expires_at.strftime('%Y-%m-%d')}")
        print(f"\n{'='*70}")
        print("FULL API KEY (save this - it won't be shown again):")
        print(f"{'='*70}")
        print(f"\n{full_key}\n")
        print(f"{'='*70}")
        print("\nTo use this key in tests, set the environment variable:")
        print(f"export TEST_API_KEY={full_key}")
        print("\nOr add to your test configuration:")
        print(f"TEST_API_KEY={full_key}")
        print(f"{'='*70}\n")
        
        # Save to file for easy access
        key_file = os.path.join(os.path.dirname(__file__), '../.test_api_key')
        with open(key_file, 'w') as f:
            f.write(full_key)
        print(f"✓ API key saved to: {key_file}")
        print("  (This file is gitignored)\n")
        
        cur.close()
        return full_key
        
    except Exception as e:
        print(f"✗ Error creating test API key: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    create_test_user_and_api_key()
