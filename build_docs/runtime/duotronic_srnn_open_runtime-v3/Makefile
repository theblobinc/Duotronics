.PHONY: up down test health logs mcp ollama milvus llama-cpp

up:
	podman compose --env-file .env up --build postgres runtime

down:
	podman compose --env-file .env down

test:
	python -m compileall app
	PYTHONPATH=app python -m pytest -q tests

health:
	curl -s http://127.0.0.1:$${APP_PORT:-8080}/health | python -m json.tool

logs:
	podman compose --env-file .env logs -f runtime

mcp:
	podman compose --env-file .env run --rm -i mcp

ollama:
	podman compose --profile ollama --env-file .env up --build

milvus:
	podman compose --profile milvus --env-file .env up --build

llama-cpp:
	podman compose --profile llama-cpp --env-file .env up --build
