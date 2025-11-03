#!/bin/bash

# Database Migration Script
# Usage: ./migrate.sh [up|down|status] [migration_number]

set -e

# Configuration
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-esg_platform}"
DB_USER="${DB_USER:-esg_user}"
DB_PASSWORD="${DB_PASSWORD:-}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Function to execute SQL file
execute_sql() {
    local sql_file=$1
    print_info "Executing: $sql_file"
    
    if [ -n "$DB_PASSWORD" ]; then
        PGPASSWORD=$DB_PASSWORD psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "$sql_file"
    else
        psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "$sql_file"
    fi
    
    if [ $? -eq 0 ]; then
        print_info "✓ Successfully executed: $sql_file"
        return 0
    else
        print_error "✗ Failed to execute: $sql_file"
        return 1
    fi
}

# Function to check if migration table exists
check_migration_table() {
    local query="SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'schema_migrations');"
    
    if [ -n "$DB_PASSWORD" ]; then
        result=$(PGPASSWORD=$DB_PASSWORD psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "$query")
    else
        result=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "$query")
    fi
    
    echo "$result" | tr -d '[:space:]'
}

# Function to create migration tracking table
create_migration_table() {
    print_info "Creating schema_migrations table..."
    
    local sql="CREATE TABLE IF NOT EXISTS schema_migrations (
        id SERIAL PRIMARY KEY,
        migration_number INT NOT NULL UNIQUE,
        migration_name TEXT NOT NULL,
        applied_at TIMESTAMP DEFAULT NOW()
    );"
    
    if [ -n "$DB_PASSWORD" ]; then
        PGPASSWORD=$DB_PASSWORD psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "$sql"
    else
        psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "$sql"
    fi
}

# Function to record migration
record_migration() {
    local migration_number=$1
    local migration_name=$2
    
    local sql="INSERT INTO schema_migrations (migration_number, migration_name) VALUES ($migration_number, '$migration_name') ON CONFLICT (migration_number) DO NOTHING;"
    
    if [ -n "$DB_PASSWORD" ]; then
        PGPASSWORD=$DB_PASSWORD psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "$sql"
    else
        psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "$sql"
    fi
}

# Function to remove migration record
remove_migration() {
    local migration_number=$1
    
    local sql="DELETE FROM schema_migrations WHERE migration_number = $migration_number;"
    
    if [ -n "$DB_PASSWORD" ]; then
        PGPASSWORD=$DB_PASSWORD psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "$sql"
    else
        psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "$sql"
    fi
}

# Function to check if migration is applied
is_migration_applied() {
    local migration_number=$1
    
    local query="SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE migration_number = $migration_number);"
    
    if [ -n "$DB_PASSWORD" ]; then
        result=$(PGPASSWORD=$DB_PASSWORD psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "$query")
    else
        result=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "$query")
    fi
    
    echo "$result" | tr -d '[:space:]'
}

# Function to migrate up
migrate_up() {
    local target_migration=$1
    
    print_info "Running migrations..."
    
    # Ensure migration table exists
    if [ "$(check_migration_table)" != "t" ]; then
        create_migration_table
    fi
    
    # Find all migration files
    for migration_file in $(ls -1 [0-9][0-9][0-9]_*.sql 2>/dev/null | sort); do
        # Extract migration number and name
        migration_number=$(echo "$migration_file" | sed 's/^\([0-9]\{3\}\)_.*/\1/' | sed 's/^0*//')
        migration_name=$(echo "$migration_file" | sed 's/^[0-9]\{3\}_\(.*\)\.sql$/\1/')
        
        # Skip rollback files
        if [[ "$migration_name" == *"_rollback" ]]; then
            continue
        fi
        
        # If target specified, only run up to that migration
        if [ -n "$target_migration" ] && [ "$migration_number" -gt "$target_migration" ]; then
            break
        fi
        
        # Check if already applied
        if [ "$(is_migration_applied $migration_number)" = "t" ]; then
            print_info "⊙ Migration $migration_number ($migration_name) already applied, skipping..."
            continue
        fi
        
        # Execute migration
        print_info "→ Applying migration $migration_number: $migration_name"
        if execute_sql "$migration_file"; then
            record_migration "$migration_number" "$migration_name"
            print_info "✓ Migration $migration_number completed successfully"
        else
            print_error "✗ Migration $migration_number failed"
            exit 1
        fi
    done
    
    print_info "All migrations completed successfully!"
}

# Function to migrate down
migrate_down() {
    local target_migration=$1
    
    print_warning "Rolling back migrations..."
    print_warning "This will DELETE data! Make sure you have a backup."
    
    # Ensure migration table exists
    if [ "$(check_migration_table)" != "t" ]; then
        print_error "No migrations to rollback (schema_migrations table not found)"
        exit 1
    fi
    
    # If no target specified, rollback last migration
    if [ -z "$target_migration" ]; then
        # Get the last applied migration
        if [ -n "$DB_PASSWORD" ]; then
            target_migration=$(PGPASSWORD=$DB_PASSWORD psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT MAX(migration_number) FROM schema_migrations;")
        else
            target_migration=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT MAX(migration_number) FROM schema_migrations;")
        fi
        target_migration=$(echo "$target_migration" | tr -d '[:space:]')
    fi
    
    if [ -z "$target_migration" ] || [ "$target_migration" = "" ]; then
        print_info "No migrations to rollback"
        exit 0
    fi
    
    # Find rollback file
    rollback_file=$(printf "%03d" "$target_migration")_*_rollback.sql
    rollback_file=$(ls -1 $rollback_file 2>/dev/null | head -1)
    
    if [ -z "$rollback_file" ]; then
        print_error "Rollback file not found for migration $target_migration"
        exit 1
    fi
    
    migration_name=$(echo "$rollback_file" | sed 's/^[0-9]\{3\}_\(.*\)_rollback\.sql$/\1/')
    
    # Execute rollback
    print_warning "← Rolling back migration $target_migration: $migration_name"
    if execute_sql "$rollback_file"; then
        remove_migration "$target_migration"
        print_info "✓ Rollback $target_migration completed successfully"
    else
        print_error "✗ Rollback $target_migration failed"
        exit 1
    fi
}

# Function to show migration status
show_status() {
    print_info "Migration Status:"
    echo ""
    
    # Ensure migration table exists
    if [ "$(check_migration_table)" != "t" ]; then
        print_warning "No migrations applied yet (schema_migrations table not found)"
        echo ""
        print_info "Available migrations:"
        for migration_file in $(ls -1 [0-9][0-9][0-9]_*.sql 2>/dev/null | sort); do
            if [[ "$migration_file" != *"_rollback.sql" ]]; then
                migration_number=$(echo "$migration_file" | sed 's/^\([0-9]\{3\}\)_.*/\1/' | sed 's/^0*//')
                migration_name=$(echo "$migration_file" | sed 's/^[0-9]\{3\}_\(.*\)\.sql$/\1/')
                echo "  [ ] $migration_number - $migration_name"
            fi
        done
        exit 0
    fi
    
    # Show all migrations with status
    for migration_file in $(ls -1 [0-9][0-9][0-9]_*.sql 2>/dev/null | sort); do
        if [[ "$migration_file" != *"_rollback.sql" ]]; then
            migration_number=$(echo "$migration_file" | sed 's/^\([0-9]\{3\}\)_.*/\1/' | sed 's/^0*//')
            migration_name=$(echo "$migration_file" | sed 's/^[0-9]\{3\}_\(.*\)\.sql$/\1/')
            
            if [ "$(is_migration_applied $migration_number)" = "t" ]; then
                # Get applied timestamp
                if [ -n "$DB_PASSWORD" ]; then
                    applied_at=$(PGPASSWORD=$DB_PASSWORD psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT applied_at FROM schema_migrations WHERE migration_number = $migration_number;")
                else
                    applied_at=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT applied_at FROM schema_migrations WHERE migration_number = $migration_number;")
                fi
                echo -e "  ${GREEN}[✓]${NC} $migration_number - $migration_name (applied: $applied_at)"
            else
                echo -e "  ${YELLOW}[ ]${NC} $migration_number - $migration_name (pending)"
            fi
        fi
    done
}

# Main script
case "$1" in
    up)
        migrate_up "$2"
        ;;
    down)
        migrate_down "$2"
        ;;
    status)
        show_status
        ;;
    *)
        echo "Usage: $0 {up|down|status} [migration_number]"
        echo ""
        echo "Commands:"
        echo "  up [N]     - Apply all pending migrations (or up to migration N)"
        echo "  down [N]   - Rollback last migration (or rollback migration N)"
        echo "  status     - Show migration status"
        echo ""
        echo "Examples:"
        echo "  $0 up              # Apply all pending migrations"
        echo "  $0 up 3            # Apply migrations up to 003"
        echo "  $0 down            # Rollback last migration"
        echo "  $0 down 3          # Rollback migration 003"
        echo "  $0 status          # Show which migrations are applied"
        exit 1
        ;;
esac
