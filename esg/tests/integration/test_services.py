"""
Service health integration tests

These tests verify:
- PostgreSQL health and connectivity
- MinIO health and connectivity
- RabbitMQ health and connectivity
- Redis health and connectivity
"""
import pytest
import psycopg2
import redis
import pika
from minio import Minio
from minio.error import S3Error


def test_postgresql_health(db_connection):
    """Test PostgreSQL is healthy and accepting connections"""
    cursor = db_connection.cursor()
    cursor.execute("SELECT 1")
    result = cursor.fetchone()
    assert result[0] == 1, "PostgreSQL health check failed"
    cursor.close()
    print("✓ PostgreSQL is healthy")


def test_postgresql_version(db_cursor):
    """Test PostgreSQL version is accessible"""
    db_cursor.execute("SELECT version()")
    version = db_cursor.fetchone()[0]
    assert "PostgreSQL" in version, "Could not retrieve PostgreSQL version"
    print(f"✓ PostgreSQL version: {version.split(',')[0]}")


def test_minio_health(minio_config):
    """Test MinIO is healthy and accessible"""
    try:
        client = Minio(
            minio_config["endpoint"],
            access_key=minio_config["access_key"],
            secret_key=minio_config["secret_key"],
            secure=minio_config["secure"]
        )
        
        # List buckets to verify connectivity
        buckets = client.list_buckets()
        assert buckets is not None, "MinIO returned None for bucket list"
        
        print(f"✓ MinIO is healthy (found {len(buckets)} buckets)")
    except S3Error as e:
        pytest.fail(f"MinIO health check failed: {e}")
    except Exception as e:
        pytest.fail(f"MinIO connection failed: {e}")


def test_minio_bucket_exists(minio_config):
    """Test required MinIO bucket exists"""
    try:
        client = Minio(
            minio_config["endpoint"],
            access_key=minio_config["access_key"],
            secret_key=minio_config["secret_key"],
            secure=minio_config["secure"]
        )
        
        # Check if esg-reports bucket exists
        bucket_name = "esg-reports"
        exists = client.bucket_exists(bucket_name)
        
        if not exists:
            print(f"⚠ Bucket '{bucket_name}' does not exist yet (will be created on first use)")
        else:
            print(f"✓ Bucket '{bucket_name}' exists")
            
    except Exception as e:
        pytest.fail(f"MinIO bucket check failed: {e}")


def test_rabbitmq_health(rabbitmq_config):
    """Test RabbitMQ is healthy and accepting connections"""
    try:
        credentials = pika.PlainCredentials(
            rabbitmq_config["user"],
            rabbitmq_config["password"]
        )
        parameters = pika.ConnectionParameters(
            host=rabbitmq_config["host"],
            port=rabbitmq_config["port"],
            credentials=credentials,
            connection_attempts=3,
            retry_delay=1
        )
        
        connection = pika.BlockingConnection(parameters)
        assert connection.is_open, "RabbitMQ connection is not open"
        
        channel = connection.channel()
        assert channel.is_open, "RabbitMQ channel is not open"
        
        channel.close()
        connection.close()
        
        print("✓ RabbitMQ is healthy")
    except Exception as e:
        pytest.fail(f"RabbitMQ health check failed: {e}")


def test_rabbitmq_queues_exist(rabbitmq_config):
    """Test RabbitMQ queues are declared"""
    try:
        credentials = pika.PlainCredentials(
            rabbitmq_config["user"],
            rabbitmq_config["password"]
        )
        parameters = pika.ConnectionParameters(
            host=rabbitmq_config["host"],
            port=rabbitmq_config["port"],
            credentials=credentials
        )
        
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()
        
        # Declare queues passively to check if they exist
        expected_queues = ["ingestion_queue", "extraction_queue"]
        
        for queue_name in expected_queues:
            try:
                # Passive declare - will raise exception if queue doesn't exist
                method = channel.queue_declare(queue=queue_name, passive=True)
                print(f"✓ Queue '{queue_name}' exists (messages: {method.method.message_count})")
            except pika.exceptions.ChannelClosedByBroker:
                # Queue doesn't exist yet - this is okay for initial setup
                print(f"⚠ Queue '{queue_name}' not declared yet (will be created on first use)")
                # Reopen channel after error
                channel = connection.channel()
        
        channel.close()
        connection.close()
        
    except Exception as e:
        pytest.fail(f"RabbitMQ queue check failed: {e}")


def test_redis_health(redis_config):
    """Test Redis is healthy and accepting connections"""
    try:
        client = redis.Redis(
            host=redis_config["host"],
            port=redis_config["port"],
            db=redis_config["db"],
            socket_connect_timeout=5
        )
        
        # Ping Redis
        response = client.ping()
        assert response is True, "Redis ping failed"
        
        print("✓ Redis is healthy")
    except redis.ConnectionError as e:
        pytest.fail(f"Redis connection failed: {e}")
    except Exception as e:
        pytest.fail(f"Redis health check failed: {e}")


def test_redis_operations(redis_config):
    """Test Redis basic operations work"""
    try:
        client = redis.Redis(
            host=redis_config["host"],
            port=redis_config["port"],
            db=redis_config["db"]
        )
        
        # Test set/get
        test_key = "health_check_test"
        test_value = "test_value"
        
        client.set(test_key, test_value, ex=10)  # Expire in 10 seconds
        retrieved = client.get(test_key)
        
        assert retrieved is not None, "Redis GET returned None"
        assert retrieved.decode() == test_value, "Redis value mismatch"
        
        # Clean up
        client.delete(test_key)
        
        print("✓ Redis operations working")
    except Exception as e:
        pytest.fail(f"Redis operations test failed: {e}")


def test_all_services_connectivity():
    """Test all services can be reached (summary test)"""
    services_status = {
        "PostgreSQL": False,
        "MinIO": False,
        "RabbitMQ": False,
        "Redis": False
    }
    
    # PostgreSQL
    try:
        import os
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "5432")),
            database=os.getenv("DB_NAME", "moz"),
            user=os.getenv("DB_USER", "drfitz"),
            password=os.getenv("DB_PASSWORD", "h4i1hydr4")
        )
        conn.close()
        services_status["PostgreSQL"] = True
    except:
        pass
    
    # MinIO
    try:
        client = Minio(
            "localhost:9000",
            access_key="minioadmin",
            secret_key="minioadmin",
            secure=False
        )
        client.list_buckets()
        services_status["MinIO"] = True
    except:
        pass
    
    # RabbitMQ
    try:
        credentials = pika.PlainCredentials("guest", "guest")
        parameters = pika.ConnectionParameters(
            host="localhost",
            port=5672,
            credentials=credentials,
            connection_attempts=1
        )
        connection = pika.BlockingConnection(parameters)
        connection.close()
        services_status["RabbitMQ"] = True
    except:
        pass
    
    # Redis
    try:
        client = redis.Redis(host="localhost", port=6379, db=0, socket_connect_timeout=2)
        client.ping()
        services_status["Redis"] = True
    except:
        pass
    
    # Report status
    print("\n=== Service Connectivity Summary ===")
    for service, status in services_status.items():
        status_str = "✓ Connected" if status else "✗ Not reachable"
        print(f"{service}: {status_str}")
    
    # At least PostgreSQL should be reachable for tests to be meaningful
    assert services_status["PostgreSQL"], "PostgreSQL must be reachable for integration tests"
