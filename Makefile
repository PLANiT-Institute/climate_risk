.PHONY: up down build logs

# Start all services in the background
up:
	docker-compose up -d

# Build docker images
build:
	docker-compose build

# Stop all services
down:
	docker-compose down

# Tail logs for all services
logs:
	docker-compose logs -f
