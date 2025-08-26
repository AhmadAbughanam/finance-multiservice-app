.PHONY: build up down logs clean test help

# Default target
help:
	@echo "Finance Multi-Service App - Available Commands:"
	@echo ""
	@echo "  make build     - Build all Docker images"
	@echo "  make up        - Start all services"
	@echo "  make down      - Stop all services"
	@echo "  make restart   - Restart all services"
	@echo "  make logs      - Show logs from all services"
	@echo "  make clean     - Clean up containers and images"
	@echo "  make test      - Test API endpoints"
	@echo "  make db-reset  - Reset database (removes all data)"
	@echo "  make dev       - Start in development mode"
	@echo "  make prod      - Start in production mode"
	@echo ""

# Build all images
build:
	@echo "Building Docker images..."
	docker-compose build

# Start all services
up:
	@echo "Starting Finance Multi-Service App..."
	docker-compose up -d
	@echo "Services starting..."
	@echo "Dashboard: http://localhost:8501"
	@echo "API: http://localhost:5000"
	@echo "Database: localhost:5432"

# Start with logs visible
dev:
	@echo "Starting in development mode..."
	docker-compose up --build

# Start all services (build first)
start: build up

# Stop all services
down:
	@echo "Stopping all services..."
	docker-compose down

# Restart all services
restart: down up

# Show logs
logs:
	docker-compose logs -f

# Show logs for specific service
logs-backend:
	docker-compose logs -f backend

logs-worker:
	docker-compose logs -f worker

logs-dashboard:
	docker-compose logs -f dashboard

logs-db:
	docker-compose logs -f db

# Clean up everything
clean:
	@echo "Cleaning up containers, images, and volumes..."
	docker-compose down -v
	docker system prune -f
	docker volume prune -f

# Reset database (warning: removes all data)
db-reset:
	@echo "Resetting database (this will remove all data)..."
	@read -p "Are you sure? (y/N): " confirm && [ "$$confirm" = "y" ] || exit 1
	docker-compose down -v
	docker-compose up -d db
	@echo "Database reset complete"

# Test API endpoints
test:
	@echo "Testing API endpoints..."
	@echo "Testing health endpoint..."
	curl -f http://localhost:5000/health || echo "❌ Health check failed"
	@echo ""
	@echo "Testing stocks endpoint..."
	curl -f http://localhost:5000/stocks || echo "❌ Stocks endpoint failed"
	@echo ""
	@echo "Testing stock screening..."
	curl -f http://localhost:5000/screen/AAPL || echo "❌ Screening failed"

# Production deployment
prod:
	@echo "Starting in production mode..."
	docker-compose -f docker-compose.yml up -d --build

# Check service status
status:
	@echo "Service Status:"
	docker-compose ps

# Update all services
update: down
	docker-compose pull
	make up

# View resource usage
stats:
	docker stats

# Backup database
backup:
	@echo "Creating database backup..."
	docker-compose exec db pg_dump -U finance finance_db > backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "Backup created: backup_$(shell date +%Y%m%d_%H%M%S).sql"

# Restore database from backup
restore:
	@read -p "Enter backup file path: " backup_file; \
	docker-compose exec -T db psql -U finance -d finance_db < $$backup_file

# Install development dependencies
dev-setup:
	@echo "Setting up development environment..."
	@if command -v python3 >/dev/null 2>&1; then \
		echo "Installing backend dependencies..."; \
		cd backend && pip install -r requirements.txt; \
		echo "Installing worker dependencies..."; \
		cd ../worker && pip install -r requirements.txt; \
		echo "Installing dashboard dependencies..."; \
		cd ../dashboard && pip install -r requirements.txt; \
	else \
		echo "Python3 not found. Please install Python 3.11+"; \
	fi