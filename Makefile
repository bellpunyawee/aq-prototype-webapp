.PHONY: up down build clean run-dev run-prod

DOCKER_COMPOSE_DEV = docker compose -f ./docker/dev/docker-compose.yml
DOCKER_COMPOSE_PROD = docker compose -f ./docker/prod/docker-compose.yml

# Define targets and their actions
up:
	$(DOCKER_COMPOSE_DEV) up -d

down:
	$(DOCKER_COMPOSE_DEV) down

build:
	$(DOCKER_COMPOSE_DEV) build

clean:
	$(DOCKER_COMPOSE_DEV) down --rmi all --volumes --remove-orphans

run-dev:
	$(DOCKER_COMPOSE_DEV) up --build --force-recreate

run-prod:
	$(DOCKER_COMPOSE_PROD) up --build --force-recreate -d