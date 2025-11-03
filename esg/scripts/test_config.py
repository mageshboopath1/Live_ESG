#!/usr/bin/env python3
"""
Test script to validate pipeline configuration.
Run this to check if your configuration is correct before running the pipeline.
"""

import sys
import os
from pathlib import Path

# Load .env file if it exists
env_file = Path(__file__).parent / '.env'
if env_file.exists():
    print(f"Loading environment from: {env_file}")
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value

from pipeline_config import get_config


def main():
    """Test and validate pipeline configuration."""
    print("=" * 70)
    print("Pipeline Configuration Test")
    print("=" * 70)
    
    # Load configuration
    print("\n📋 Loading configuration...")
    try:
        config = get_config()
        print("✓ Configuration loaded successfully")
    except Exception as e:
        print(f"✗ Failed to load configuration: {e}")
        return 1
    
    # Validate configuration
    print("\n🔍 Validating configuration...")
    errors = config.validate()
    
    if errors:
        print(f"✗ Found {len(errors)} validation error(s):\n")
        for i, error in enumerate(errors, 1):
            print(f"  {i}. {error}")
        print("\n❌ Configuration validation failed!")
        print("\nPlease fix the errors above and try again.")
        print("See PIPELINE_CONFIG_README.md for configuration details.")
        return 1
    else:
        print("✓ All validation checks passed")
    
    # Print configuration summary
    print("\n" + "=" * 70)
    config.print_summary()
    
    # Test database connection
    print("\n🔌 Testing database connection...")
    try:
        import psycopg2
        conn = psycopg2.connect(**config.database.connection_dict)
        conn.close()
        print("✓ Database connection successful")
    except Exception as e:
        print(f"⚠️  Database connection failed: {e}")
        print("   (This is OK if database is not running yet)")
    
    # Test MinIO connection
    print("\n🔌 Testing MinIO connection...")
    try:
        import boto3
        from botocore.exceptions import ClientError
        
        s3 = boto3.client(
            's3',
            endpoint_url=config.minio.endpoint,
            aws_access_key_id=config.minio.access_key,
            aws_secret_access_key=config.minio.secret_key,
            use_ssl=config.minio.secure
        )
        
        # Try to list buckets
        s3.list_buckets()
        print("✓ MinIO connection successful")
    except Exception as e:
        print(f"⚠️  MinIO connection failed: {e}")
        print("   (This is OK if MinIO is not running yet)")
    
    # Test RabbitMQ connection
    print("\n🔌 Testing RabbitMQ connection...")
    try:
        import pika
        
        credentials = pika.PlainCredentials(
            config.rabbitmq.user,
            config.rabbitmq.password
        )
        
        parameters = pika.ConnectionParameters(
            host=config.rabbitmq.host,
            port=config.rabbitmq.port,
            credentials=credentials,
            heartbeat=config.rabbitmq.heartbeat,
            blocked_connection_timeout=config.rabbitmq.blocked_connection_timeout
        )
        
        connection = pika.BlockingConnection(parameters)
        connection.close()
        print("✓ RabbitMQ connection successful")
    except Exception as e:
        print(f"⚠️  RabbitMQ connection failed: {e}")
        print("   (This is OK if RabbitMQ is not running yet)")
    
    # Final result
    print("\n" + "=" * 70)
    print("✅ Configuration test completed successfully!")
    print("=" * 70)
    print("\nYour configuration is valid and ready to use.")
    print("\nNext steps:")
    print("  1. Start infrastructure: cd infra && docker-compose up -d")
    print("  2. Run pipeline: python scripts/pipeline_orchestrator.py")
    print("  3. See PIPELINE_CONFIG_README.md for more options")
    print()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
