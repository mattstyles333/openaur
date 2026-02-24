# openaur - Personal AI Assistant
# Arch Linux + FastAPI + OpenRouter + OpenMemory

.PHONY: build run stop clean test crawl

# Build the Docker image
build:
	docker-compose build --no-cache

# Run the container
run:
	docker-compose up -d

# Run with logs
run-logs:
	docker-compose up

# Stop the container
stop:
	docker-compose down

# Clean up
clean:
	docker-compose down -v
	docker rmi openaura-openaura || true
	rm -rf data/*.db

# Test the API
test:
	curl -s http://localhost:8000/health | jq .

# Crawl a CLI tool and register it
crawl:
	@echo "Usage: make crawl BINARY=<binary-name>"
	@if [ -z "$(BINARY)" ]; then \
		echo "Error: BINARY not set. Example: make crawl BINARY=git"; \
		exit 1; \
	fi
	curl -s -X POST http://localhost:8000/actions/ \
		-H "Content-Type: application/json" \
		-d '{"binary": "$(BINARY)", "safety": 2}' | jq .

# List registered actions
actions:
	curl -s http://localhost:8000/actions/ | jq .

# Search for packages
search:
	@echo "Usage: make search QUERY=<package-name>"
	@if [ -z "$(QUERY)" ]; then \
		echo "Error: QUERY not set. Example: make search QUERY=docker"; \
		exit 1; \
	fi
	curl -s "http://localhost:8000/packages/search?q=$(QUERY)" | jq .

# Install a package
install:
	@echo "Usage: make install PACKAGE=<package-name>"
	@if [ -z "$(PACKAGE)" ]; then \
		echo "Error: PACKAGE not set. Example: make install PACKAGE=htop"; \
		exit 1; \
	fi
	curl -s -X POST http://localhost:8000/packages/install \
		-H "Content-Type: application/json" \
		-d '{"package": "$(PACKAGE)"}' | jq .

# Chat with the assistant
chat:
	@echo "Usage: make chat MSG='<your message>'"
	@if [ -z "$(MSG)" ]; then \
		echo "Error: MSG not set. Example: make chat MSG='Hello'"; \
		exit 1; \
	fi
	curl -s -X POST http://localhost:8000/chat/ \
		-H "Content-Type: application/json" \
		-d '{"message": "$(MSG)"}' | jq .

# View logs
logs:
	docker-compose logs -f

# Shell into container
shell:
	docker-compose exec openaura bash

# Reset database
reset-db:
	docker-compose down
	rm -f data/openaura.db
	docker-compose up -d
