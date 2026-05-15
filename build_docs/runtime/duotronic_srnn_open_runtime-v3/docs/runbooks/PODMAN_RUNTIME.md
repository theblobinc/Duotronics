# Podman Runtime Runbook

## Core start

```bash
cp .env.example .env
podman compose --env-file .env up --build postgres redis minio runtime
```

## Add models

```bash
podman compose --profile models --env-file .env up --build
```

Pull an Ollama model on the host or inside the container:

```bash
podman exec -it duotronic-ollama ollama pull llama3.2:1b
```

Set in `.env`:

```text
OLLAMA_ENABLED=true
OLLAMA_DEFAULT_MODEL=llama3.2:1b
```

## Add formal observers

```bash
podman compose --profile formal --env-file .env up --build
```

The TLA+ image downloads `tla2tools.jar` at build time. Pin the URL or pre-stage the jar for locked-down environments.
