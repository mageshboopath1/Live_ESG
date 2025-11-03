#!/bin/bash

# ============================================================================
# ESG Intelligence Platform - Start Script
# ============================================================================
# This script provides convenient commands to manage the Docker Compose stack
# ============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Function to print colored messages
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if .env exists
check_env() {
    if [ ! -f "$SCRIPT_DIR/.env" ]; then
        print_error ".env file not found!"
        print_info "Creating .env from .env.example..."
        if [ -f "$SCRIPT_DIR/../.env.example" ]; then
            cp "$SCRIPT_DIR/../.env.example" "$SCRIPT_DIR/.env"
            print_warn "Please edit $SCRIPT_DIR/.env with your configuration"
            exit 1
        else
            print_error ".env.example not found. Please create .env manually."
            exit 1
        fi
    fi
}

# Function to check Docker
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        print_error "Docker daemon is not running. Please start Docker."
        exit 1
    fi
}

# Function to start services
start_services() {
    local mode=$1
    check_env
    check_docker
    
    if [ "$mode" = "dev" ]; then
        print_info "Starting services in DEVELOPMENT mode..."
        docker-compose -f "$SCRIPT_DIR/docker-compose.yml" -f "$SCRIPT_DIR/docker-compose.dev.yml" up -d
    else
        print_info "Starting services in PRODUCTION mode..."
        docker-compose -f "$SCRIPT_DIR/docker-compose.yml" up -d
    fi
    
    print_info "Waiting for services to be healthy..."
    sleep 5
    
    print_info "Service status:"
    docker-compose -f "$SCRIPT_DIR/docker-compose.yml" ps
    
    print_info ""
    print_info "Services are starting up. Access points:"
    print_info "  Frontend:          http://localhost:3000"
    print_info "  API Gateway:       http://localhost:8000"
    print_info "  API Docs:          http://localhost:8000/docs"
    print_info "  PgAdmin:           http://localhost:8080"
    print_info "  MinIO Console:     http://localhost:9001"
    print_info "  RabbitMQ Mgmt:     http://localhost:15672"
}

# Function to stop services
stop_services() {
    print_info "Stopping services..."
    docker-compose -f "$SCRIPT_DIR/docker-compose.yml" down
    print_info "Services stopped."
}

# Function to restart services
restart_services() {
    local service=$1
    if [ -z "$service" ]; then
        print_info "Restarting all services..."
        docker-compose -f "$SCRIPT_DIR/docker-compose.yml" restart
    else
        print_info "Restarting $service..."
        docker-compose -f "$SCRIPT_DIR/docker-compose.yml" restart "$service"
    fi
}

# Function to view logs
view_logs() {
    local service=$1
    if [ -z "$service" ]; then
        docker-compose -f "$SCRIPT_DIR/docker-compose.yml" logs -f
    else
        docker-compose -f "$SCRIPT_DIR/docker-compose.yml" logs -f "$service"
    fi
}

# Function to show status
show_status() {
    print_info "Service status:"
    docker-compose -f "$SCRIPT_DIR/docker-compose.yml" ps
    
    print_info ""
    print_info "Resource usage:"
    docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"
}

# Function to clean up
cleanup() {
    print_warn "This will remove all containers and volumes. Data will be lost!"
    read -p "Are you sure? (yes/no): " confirm
    if [ "$confirm" = "yes" ]; then
        print_info "Cleaning up..."
        docker-compose -f "$SCRIPT_DIR/docker-compose.yml" down -v
        print_info "Cleanup complete."
    else
        print_info "Cleanup cancelled."
    fi
}

# Function to rebuild service
rebuild_service() {
    local service=$1
    if [ -z "$service" ]; then
        print_error "Please specify a service to rebuild"
        exit 1
    fi
    
    print_info "Rebuilding $service..."
    docker-compose -f "$SCRIPT_DIR/docker-compose.yml" build "$service"
    docker-compose -f "$SCRIPT_DIR/docker-compose.yml" up -d "$service"
    print_info "Rebuild complete."
}

# Main script
case "$1" in
    start)
        start_services "prod"
        ;;
    dev)
        start_services "dev"
        ;;
    stop)
        stop_services
        ;;
    restart)
        restart_services "$2"
        ;;
    logs)
        view_logs "$2"
        ;;
    status)
        show_status
        ;;
    rebuild)
        rebuild_service "$2"
        ;;
    clean)
        cleanup
        ;;
    *)
        echo "ESG Intelligence Platform - Docker Compose Manager"
        echo ""
        echo "Usage: $0 {start|dev|stop|restart|logs|status|rebuild|clean} [service]"
        echo ""
        echo "Commands:"
        echo "  start              Start all services in production mode"
        echo "  dev                Start all services in development mode (hot-reload)"
        echo "  stop               Stop all services"
        echo "  restart [service]  Restart all services or specific service"
        echo "  logs [service]     View logs for all services or specific service"
        echo "  status             Show service status and resource usage"
        echo "  rebuild <service>  Rebuild and restart a specific service"
        echo "  clean              Remove all containers and volumes (destructive)"
        echo ""
        echo "Examples:"
        echo "  $0 start                    # Start in production mode"
        echo "  $0 dev                      # Start in development mode"
        echo "  $0 logs api-gateway         # View API gateway logs"
        echo "  $0 restart extraction       # Restart extraction service"
        echo "  $0 rebuild frontend         # Rebuild frontend service"
        echo ""
        exit 1
        ;;
esac
