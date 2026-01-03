.PHONY: help env build up down restart logs ps migrate makemigrations superuser shell django-check local-setup local-migrate local-superuser local-run

# Use sudo with docker-compose to bypass permission issues
COMPOSE := sudo docker-compose

help:
	@echo "Targets:"
	@echo "  make env            Copy .env.example -> .env (if missing)"
	@echo "  make build          docker compose build"
	@echo "  make up             docker compose up"
	@echo "  make down           docker compose down"
	@echo "  make restart        down + up"
	@echo "  make logs           docker compose logs -f"
	@echo "  make ps             docker compose ps"
	@echo "  make migrate        Run Django migrations"
	@echo "  make makemigrations Create Django migrations"
	@echo "  make superuser      Create Django superuser"
	@echo "  make shell          Django shell"
	@echo "  make django-check   Django system check"
	@echo "  make local-setup    Setup local environment (install deps, migrate, superuser)"
	@echo "  make local-migrate  Run local Django migrations"
	@echo "  make local-superuser Create local Django superuser"
	@echo "  make local-run      Run local Django development server"

env:
	@test -f .env || cp .env.example .env

build:
	$(COMPOSE) build

up:
	-$(COMPOSE) down --remove-orphans
	-sudo docker stop sportsmeet_web_1 sportsmeet_db_1 2>/dev/null || true
	-sudo docker rm sportsmeet_web_1 sportsmeet_db_1 2>/dev/null || true
	$(COMPOSE) up -d --build

down:
	$(COMPOSE) down

restart: down up

logs:
	$(COMPOSE) logs -f

ps:
	$(COMPOSE) ps

migrate:
	$(COMPOSE) run --rm web python manage.py migrate

makemigrations:
	$(COMPOSE) run --rm web python manage.py makemigrations

superuser:
	$(COMPOSE) run --rm web python manage.py createsuperuser

shell:
	$(COMPOSE) run --rm web python manage.py shell

django-check:
	$(COMPOSE) run --rm web python manage.py check

fix-permissions:
	sudo usermod -aG docker $(USER)
	@echo "Permissions updated. Please log out and log back in for changes to take effect."

local-setup: env
	pip install -r requirements.txt
	python3 manage.py migrate
	@echo "Creating superuser (admin/admin)..."
	@DJANGO_SUPERUSER_PASSWORD=admin DJANGO_SUPERUSER_USERNAME=admin DJANGO_SUPERUSER_EMAIL=admin@example.com python3 manage.py createsuperuser --noinput

local-migrate:
	python3 manage.py migrate

local-superuser:
	python3 manage.py createsuperuser

local-run:
	-@fuser -k 8000/tcp 2>/dev/null || true
	python3 manage.py runserver 0.0.0.0:8000
