.PHONY: help install dev prod deploy clean logs test

help: ## Show this help message
	@echo "FastAPI + Cognito + PostgreSQL Project"
	@echo "======================================"
	@echo
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	pip install -r requirements.txt

dev: ## Start development environment
	@echo "🚀 Starting development environment..."
	@chmod +x deploy.sh
	@./deploy.sh dev

prod: ## Deploy to production
	@echo "🚀 Deploying to production..."
	@chmod +x deploy.sh
	@./deploy.sh prod

deploy: dev ## Alias for dev deployment

clean: ## Stop and remove all containers
	@echo "🧹 Cleaning up containers..."
	@docker-compose down --remove-orphans --volumes
	@docker system prune -f

logs: ## View application logs
	@docker-compose logs -f api

test: ## Run tests
	@echo "🧪 Running tests..."
	@docker-compose exec api python -m pytest

health: ## Check API health
	@curl -s http://localhost:8000/health | jq . || echo "API not responding"

setup: ## Initial project setup
	@echo "🔧 Setting up project..."
	@cp .env.example .env
	@echo "✅ Created .env file - please update with your configuration"
	@echo "📋 Next steps:"
	@echo "   1. Update .env with your settings"
	@echo "   2. Run 'make dev' to start development environment"

docs: ## Open API documentation
	@echo "📖 Opening API documentation..."
	@python -c "import webbrowser; webbrowser.open('http://localhost:8000/docs')"