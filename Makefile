# Filenames
COMPOSE_FILE_DEV := docker-compose.yml

ifneq (,$(wildcard docker/dev/.env))
    include docker/dev/.env
    export
endif

# Helper function for selecting the compose file
set-compose-file:
	$(eval COMPOSE_FILE=$(if $(filter $(env),prod),$(COMPOSE_FILE_DEPLOY),$(COMPOSE_FILE_DEV)))

# Docker-compose base command
BASE_COMPOSE_CMD = docker-compose -f $(COMPOSE_FILE) 

# Backup directory
BACKUP_DIR := backups

# HELP
# This will output the help for each task
.PHONY: help up down build ssh start stop restart rm ps logs clean list

help: ## This help.
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

.DEFAULT_GOAL := help

env-file:
		@if [ "$(env)" = "dev" ]; then \
        echo "Setting up development environment"; \
			chmod +x ./docker/dev/script/make-env.sh; \
        	./docker/dev/script/make-env.sh; \
    elif [ "$(env)" = "deploy" ]; then \
        echo "Setting up deployment environment"; \
        ./make-env-deploy.sh; \
    else \
        echo "Please specify the environment. Usage: make env env=dev or make env env=deploy"; \
    fi

check-db: set-compose-file
	@echo "Database Host: $(POSTGRES_HOST)"

init: set-compose-file ## Init project and create superuser
	@echo "Initializing project..."
	@$(BASE_COMPOSE_CMD) exec django sh -c "\
		python manage.py makemigrations && \
		python manage.py migrate && \
		python manage.py create_tenant --schema_name=localhost --name=localhost --domain-domain=localhost --domain-is_primary=True --no-input && \
		python manage.py tenant_command migrate -s localhost && \
		python manage.py tenant_command init_countries -s localhost && \
		python manage.py create_tenant_user localhost admin admin@example.com admin123 --superuser"

# DOCKER TASKS
backup: set-compose-file ## Backup tenant databases
	@echo "Starting backup process for tenants..."
	@mkdir -p $(BACKUP_DIR) # Creates the backup directory if it does not exist.
	@$(BASE_COMPOSE_CMD) exec -e PGPASSWORD=$(POSTGRES_PASSWORD) -T db pg_dump -U $(POSTGRES_USER) -h $(POSTGRES_HOST) -d $(POSTGRES_DB) > $(BACKUP_DIR)/backup_$$(date +'%Y%m%d%H%M').sql;
	@echo "Backup completed."

restore: set-compose-file ## Restore database from a backup file
	@echo "Starting database restore..."
	@$(BASE_COMPOSE_CMD) exec -T -e PGPASSWORD=$(POSTGRES_PASSWORD) db psql -U $(POSTGRES_USER) -h $(POSTGRES_HOST) -d $(POSTGRES_DB) < backups/$(SQL_FILE)
	@echo "Database restore completed."

# Build the container
build: set-compose-file## Build the release and development container.
	docker volume create --name=cache
	$(BASE_COMPOSE_CMD) up -d --build $(target)

update: set-compose-file ## Update Docker images to the latest version
	@echo "Updating Docker images to the latest version..."
	$(BASE_COMPOSE_CMD) pull
	@echo "Docker images updated successfully."

ssh: ## Run container in development mode
	docker exec -it $(c) $(user)

static: set-compose-file
	$(BASE_COMPOSE_CMD) exec django python manage.py collectstatic

migrate: set-compose-file
	$(BASE_COMPOSE_CMD) exec django python manage.py migrate

makemigrations: set-compose-file
	$(BASE_COMPOSE_CMD) exec django python manage.py makemigrations

tests: set-compose-file## Run tests in the container.
	$(BASE_COMPOSE_CMD) exec django pytest

lint: set-compose-file## Run tests in the container.
	$(BASE_COMPOSE_CMD) exec django flake8

start: set-compose-file ## Start services based on environment
ifeq ($(env),dev)
	$(call service-start,django db redis)
else
	$(call service-start,$(env))
endif

up: set-compose-file## Spin up the containers
	$(BASE_COMPOSE_CMD) up -d $(target)

stop: set-compose-file ## Stop services based on environment
ifeq ($(env),dev)
	$(call service-stop,django db)
else
	$(call service-stop,$(env))
endif

restart: set-compose-file ## Restart services based on environment
ifeq ($(env),dev)
	$(call service-restart,django db)
else
	$(call service-restart,$(env))
endif

rm: set-compose-file## Stop and remove running containers
	$(BASE_COMPOSE_CMD) down -v $(target)

ps: set-compose-file## Process running containers
	$(BASE_COMPOSE_CMD) ps

logs: set-compose-file## Logs process running containers
	$(BASE_COMPOSE_CMD) logs --tail=100 -f $(target)

clean: ## Clean the generated/compiles files
	echo "nothing clean ..."

list:
	docker ps -all
	docker images
	docker network ls

login-docker:
	docker login -u $(DOCKERHUB_USERNAME) --password-stdin


define service-start
	$(BASE_COMPOSE_CMD) up -d $(1)
endef

define service-stop
	$(BASE_COMPOSE_CMD) stop $(1)
endef

define service-restart
	$(BASE_COMPOSE_CMD) stop $(1) && $(BASE_COMPOSE_CMD) up -d $(1)
endef
