if (!(Test-Path .env)) { Copy-Item .env.example .env }
podman compose --env-file .env up --build postgres runtime
