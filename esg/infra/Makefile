# ============================================================================
# ESG Intelligence Platform - Makefile
# ============================================================================
# Convenient commands for managing the Docker Compose stack
# ============================================================================

.PHONY: help start dev stop restart logs status clean rebuild ps health

# Default target
.DEFAULT_GOAL := help

# Docker Compose files
COMPOSE_FILE := docker-compose.yml
COMPOSE_DEV_FILE := docker-compose.dev.yml
COMPOSE_AIRFLOW_FILE := docker-compose.airflow.yml
COMPOSE_CMD := docker-compose -f $(COMPOSE_FILE)
COMPOSE_DEV_CMD := docker-compose -f $(COMPOSE_FILE) -f $(COMPOSE_DEV_FILE)
COMPOSE_AIRFLOW_CMD := docker-compose -f $(COMPOSE_FILE) -f $(COMPOSE_AIRFLOW_FILE)

help: ## Show this help message
	@echo "ESG Intelligence Platform - Docker Compose Commands"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-15s %s\n", $$1, $$2}'

start: ## Start all services in production mode (queue-based)
	@echo "Starting services in production mode..."
	$(COMPOSE_CMD) up -d
	@echo "Services started. Run 'make status' to check health."

start-airflow: ## Start all services with Airflow orchestration
	@echo "Starting services with Airflow orchestration..."
	$(COMPOSE_AIRFLOW_CMD) up -d
	@echo "Services started with Airflow."
	@echo "Airflow UI: http://localhost:8081 (admin/admin)"
	@echo "Run 'make logs-airflow' to view Airflow logs."

dev: ## Start all services in development mode with hot-reload
	@echo "Starting services in development mode..."
	$(COMPOSE_DEV_CMD) up -d
	@echo "Services started in dev mode. Run 'make logs' to view output."

stop: ## Stop all services
	@echo "Stopping services..."
	$(COMPOSE_CMD) down
	@echo "Services stopped."

stop-airflow: ## Stop Airflow services
	@echo "Stopping Airflow services..."
	$(COMPOSE_AIRFLOW_CMD) down
	@echo "Airflow services stopped."

restart: ## Restart all services
	@echo "Restarting services..."
	$(COMPOSE_CMD) restart
	@echo "Services restarted."

logs: ## View logs for all services (follow mode)
	$(COMPOSE_CMD) logs -f

logs-%: ## View logs for specific service (e.g., make logs-api-gateway)
	$(COMPOSE_CMD) logs -f $*

status: ## Show service status
	@echo "Service Status:"
	@$(COMPOSE_CMD) ps
	@echo ""
	@echo "Resource Usage:"
	@docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"

ps: ## Show running containers
	$(COMPOSE_CMD) ps

health: ## Check health of all services
	@echo "Checking service health..."
	@$(COMPOSE_CMD) ps --format json | jq -r '.[] | "\(.Name): \(.Health)"'

build: ## Build all services
	@echo "Building all services..."
	$(COMPOSE_CMD) build

build-%: ## Build specific service (e.g., make build-frontend)
	@echo "Building $*..."
	$(COMPOSE_CMD) build $*

rebuild-%: ## Rebuild and restart specific service (e.g., make rebuild-extraction)
	@echo "Rebuilding $*..."
	$(COMPOSE_CMD) build $*
	$(COMPOSE_CMD) up -d $*
	@echo "$* rebuilt and restarted."

restart-%: ## Restart specific service (e.g., make restart-api-gateway)
	@echo "Restarting $*..."
	$(COMPOSE_CMD) restart $*
	@echo "$* restarted."

shell-%: ## Open shell in specific service (e.g., make shell-extraction)
	$(COMPOSE_CMD) exec $* /bin/bash

clean: ## Remove all containers (keeps volumes)
	@echo "Removing containers..."
	$(COMPOSE_CMD) down
	@echo "Containers removed."

clean-all: ## Remove all containers and volumes (destructive!)
	@echo "WARNING: This will delete all data!"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		$(COMPOSE_CMD) down -v; \
		echo "Containers and volumes removed."; \
	else \
		echo "Cancelled."; \
	fi

pull: ## Pull latest images
	$(COMPOSE_CMD) pull

config: ## Validate and view the compose configuration
	$(COMPOSE_CMD) config

config-dev: ## Validate and view the dev compose configuration
	$(COMPOSE_DEV_CMD) config

# Database commands
db-shell: ## Open PostgreSQL shell
	$(COMPOSE_CMD) exec postgres psql -U drfitz -d moz

db-backup: ## Backup database to file
	@echo "Backing up database..."
	@mkdir -p backups
	$(COMPOSE_CMD) exec -T postgres pg_dump -U drfitz moz > backups/backup_$$(date +%Y%m%d_%H%M%S).sql
	@echo "Database backed up to backups/"

db-restore: ## Restore database from latest backup
	@echo "Restoring database from latest backup..."
	@LATEST=$$(ls -t backups/*.sql | head -1); \
	if [ -z "$$LATEST" ]; then \
		echo "No backup files found in backups/"; \
		exit 1; \
	fi; \
	echo "Restoring from $$LATEST"; \
	$(COMPOSE_CMD) exec -T postgres psql -U drfitz -d moz < $$LATEST
	@echo "Database restored."

# Service-specific shortcuts
api: ## View API Gateway logs
	$(COMPOSE_CMD) logs -f api-gateway

frontend: ## View Frontend logs
	$(COMPOSE_CMD) logs -f frontend

extraction: ## View Extraction service logs
	$(COMPOSE_CMD) logs -f extraction

embeddings: ## View Embeddings service logs
	$(COMPOSE_CMD) logs -f embeddings

# Airflow-specific commands
logs-airflow: ## View all Airflow logs
	$(COMPOSE_AIRFLOW_CMD) logs -f airflow-scheduler airflow-webserver

logs-airflow-scheduler: ## View Airflow scheduler logs
	$(COMPOSE_AIRFLOW_CMD) logs -f airflow-scheduler

logs-airflow-webserver: ## View Airflow webserver logs
	$(COMPOSE_AIRFLOW_CMD) logs -f airflow-webserver

airflow-trigger: ## Trigger ESG pipeline DAG
	@echo "Triggering ESG pipeline..."
	docker exec esg-airflow-scheduler airflow dags trigger esg_pipeline
	@echo "Pipeline triggered. Check status at http://localhost:8081"

airflow-trigger-companies: ## Trigger pipeline for specific companies (usage: make airflow-trigger-companies COMPANIES="RELIANCE,TCS")
	@echo "Triggering ESG pipeline for companies: $(COMPANIES)"
	docker exec esg-airflow-scheduler airflow dags trigger esg_pipeline \
		--conf '{"companies": ["$(shell echo $(COMPANIES) | sed 's/,/","/g')"]}'
	@echo "Pipeline triggered. Check status at http://localhost:8081"

airflow-list-dags: ## List all Airflow DAGs
	docker exec esg-airflow-scheduler airflow dags list

airflow-list-runs: ## List recent DAG runs
	docker exec esg-airflow-scheduler airflow dags list-runs -d esg_pipeline --limit 10

# Access web interfaces
open-frontend: ## Open frontend in browser
	@echo "Opening frontend..."
	@xdg-open http://localhost:3000 2>/dev/null || open http://localhost:3000 2>/dev/null || echo "Please open http://localhost:3000"

open-api: ## Open API docs in browser
	@echo "Opening API docs..."
	@xdg-open http://localhost:8000/docs 2>/dev/null || open http://localhost:8000/docs 2>/dev/null || echo "Please open http://localhost:8000/docs"

open-pgadmin: ## Open PgAdmin in browser
	@echo "Opening PgAdmin..."
	@xdg-open http://localhost:8080 2>/dev/null || open http://localhost:8080 2>/dev/null || echo "Please open http://localhost:8080"

open-minio: ## Open MinIO console in browser
	@echo "Opening MinIO console..."
	@xdg-open http://localhost:9001 2>/dev/null || open http://localhost:9001 2>/dev/null || echo "Please open http://localhost:9001"

open-rabbitmq: ## Open RabbitMQ management in browser
	@echo "Opening RabbitMQ management..."
	@xdg-open http://localhost:15672 2>/dev/null || open http://localhost:15672 2>/dev/null || echo "Please open http://localhost:15672"

open-airflow: ## Open Airflow UI in browser
	@echo "Opening Airflow UI..."
	@xdg-open http://localhost:8081 2>/dev/null || open http://localhost:8081 2>/dev/null || echo "Please open http://localhost:8081"

# Testing commands
test: ## Run comprehensive Docker Compose setup tests
	@echo "Running comprehensive Docker Compose tests..."
	@./test-docker-setup.sh

test-quick: ## Run quick health check
	@echo "Running quick health check..."
	@./quick-health-check.sh

test-services: ## Test service-to-service communication
	@echo "Testing service communication..."
	@echo "API Gateway health:"
	@curl -f http://localhost:8000/health 2>/dev/null && echo "✓ API Gateway OK" || echo "✗ API Gateway failed"
	@echo "MinIO health:"
	@curl -f http://localhost:9000/minio/health/live 2>/dev/null && echo "✓ MinIO OK" || echo "✗ MinIO failed"
	@echo "RabbitMQ health:"
	@curl -f http://localhost:15672 2>/dev/null && echo "✓ RabbitMQ OK" || echo "✗ RabbitMQ failed"

test-persistence: ## Test volume persistence
	@echo "Testing volume persistence..."
	@echo "Creating test data..."
	@$(COMPOSE_CMD) exec -T postgres psql -U esg_user -d esg_platform -c "CREATE TABLE IF NOT EXISTS test_persistence (id SERIAL, data TEXT);" > /dev/null
	@$(COMPOSE_CMD) exec -T postgres psql -U esg_user -d esg_platform -c "INSERT INTO test_persistence (data) VALUES ('test_$(shell date +%s)');" > /dev/null
	@echo "Stopping services..."
	@$(COMPOSE_CMD) stop > /dev/null
	@sleep 5
	@echo "Starting services..."
	@$(COMPOSE_CMD) start > /dev/null
	@sleep 10
	@echo "Verifying data..."
	@COUNT=$$($(COMPOSE_CMD) exec -T postgres psql -U esg_user -d esg_platform -t -c "SELECT COUNT(*) FROM test_persistence;" | tr -d ' '); \
	if [ "$$COUNT" -gt 0 ]; then \
		echo "✓ Data persisted ($$COUNT rows)"; \
	else \
		echo "✗ Data did not persist"; \
	fi
	@$(COMPOSE_CMD) exec -T postgres psql -U esg_user -d esg_platform -c "DROP TABLE IF EXISTS test_persistence;" > /dev/null

test-env: ## Verify environment variables
	@echo "Checking environment variables..."
	@echo "API Gateway DB_HOST: $$($(COMPOSE_CMD) exec -T api-gateway printenv DB_HOST 2>/dev/null || echo 'NOT SET')"
	@echo "Extraction RABBITMQ_HOST: $$($(COMPOSE_CMD) exec -T extraction printenv RABBITMQ_HOST 2>/dev/null || echo 'NOT SET')"
	@echo "Embeddings MINIO_ENDPOINT: $$($(COMPOSE_CMD) exec -T embeddings printenv MINIO_ENDPOINT 2>/dev/null || echo 'NOT SET')"
