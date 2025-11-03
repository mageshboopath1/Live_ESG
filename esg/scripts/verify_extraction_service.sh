#!/bin/bash
# Verification script for extraction service configuration
# This script checks the extraction service startup, queue connection, and configuration

echo "=========================================="
echo "Extraction Service Configuration Verification"
echo "=========================================="
echo ""

# Check if extraction service is running
echo "1. Checking extraction service status..."
SERVICE_STATUS=$(docker ps --filter "name=esg-extraction" --format "{{.Status}}")
if [ -z "$SERVICE_STATUS" ]; then
    echo "   ❌ Extraction service is NOT running"
    exit 1
else
    echo "   ✓ Extraction service is running: $SERVICE_STATUS"
fi
echo ""

# Check RabbitMQ status
echo "2. Checking RabbitMQ status..."
RABBITMQ_STATUS=$(docker ps --filter "name=rabbitmq" --format "{{.Status}}")
if [ -z "$RABBITMQ_STATUS" ]; then
    echo "   ❌ RabbitMQ is NOT running"
    exit 1
else
    echo "   ✓ RabbitMQ is running: $RABBITMQ_STATUS"
fi
echo ""

# Check database status
echo "3. Checking PostgreSQL status..."
POSTGRES_STATUS=$(docker ps --filter "name=postgres" --format "{{.Status}}")
if [ -z "$POSTGRES_STATUS" ]; then
    echo "   ❌ PostgreSQL is NOT running"
    exit 1
else
    echo "   ✓ PostgreSQL is running: $POSTGRES_STATUS"
fi
echo ""

# Check extraction service startup logs
echo "4. Checking extraction service startup configuration..."
echo "   Configuration from logs:"
docker logs esg-extraction 2>&1 | grep -E "Database:|RabbitMQ:|Queue:|Log Level:" | tail -4
echo ""

# Check queue declaration in logs
echo "5. Checking queue declaration..."
QUEUE_DECLARED=$(docker logs esg-extraction 2>&1 | grep "Declaring queue: extraction-tasks" | tail -1)
if [ -z "$QUEUE_DECLARED" ]; then
    echo "   ⚠ Queue declaration not found in logs"
else
    echo "   ✓ Queue declared: extraction-tasks"
fi

DLQ_DECLARED=$(docker logs esg-extraction 2>&1 | grep "Declaring dead letter queue:" | tail -1)
if [ -z "$DLQ_DECLARED" ]; then
    echo "   ⚠ Dead letter queue declaration not found in logs"
else
    echo "   ✓ Dead letter queue declared: extraction-tasks.dlq"
fi
echo ""

# Check if service is ready
echo "6. Checking if service is ready..."
SERVICE_READY=$(docker logs esg-extraction 2>&1 | grep "Extraction service ready" | tail -1)
if [ -z "$SERVICE_READY" ]; then
    echo "   ⚠ Service ready message not found in logs"
else
    echo "   ✓ Service is ready and waiting for tasks"
fi
echo ""

# Check RabbitMQ queue status
echo "7. Checking RabbitMQ queue status..."
echo "   Queue information:"
docker exec esg-rabbitmq rabbitmqctl list_queues name messages consumers 2>/dev/null | grep -E "extraction-tasks"
echo ""

# Check for any recent errors
echo "8. Checking for recent errors..."
ERROR_COUNT=$(docker logs --tail 100 esg-extraction 2>&1 | grep -c "\[ERROR\]")
if [ "$ERROR_COUNT" -gt 0 ]; then
    echo "   ⚠ Found $ERROR_COUNT error messages in last 100 log lines"
    echo "   Recent errors:"
    docker logs --tail 100 esg-extraction 2>&1 | grep "\[ERROR\]" | tail -5
else
    echo "   ✓ No errors found in recent logs"
fi
echo ""

# Check database connection
echo "9. Checking database connection..."
DB_ERROR=$(docker logs --tail 50 esg-extraction 2>&1 | grep "Database connection error" | tail -1)
if [ -n "$DB_ERROR" ]; then
    echo "   ⚠ Database connection issues detected:"
    echo "   $DB_ERROR"
else
    echo "   ✓ No database connection errors in recent logs"
fi
echo ""

echo "=========================================="
echo "Verification Complete"
echo "=========================================="
