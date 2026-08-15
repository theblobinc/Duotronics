# Fusion Center MCP Integration

The runtime adapts the MIT-licensed `Draichi/fusion-center` source connectors under a bounded `fusion.*` namespace.

## Tool groups

- News and discovery: GDELT, curated RSS, DuckDuckGo, public archive catalogue metadata
- Physical context: NASA FIRMS thermal anomalies
- Digital context: IODA outages and Cloudflare Radar metrics
- Public-channel context: Telegram channel catalogue, search and metadata
- Threat intelligence: AlienVault OTX indicators and pulses
- Analysis: deterministic planning and entity/time/space correlation

Every source call returns a `xavi-fusion-result-v1` envelope containing retrieval time, query arguments, source metadata and the pinned upstream commit.

The Agent Skill library is mounted separately at `/runtime/corpus/skills`, while the Witness Contract remains the principal corpus mounted at `/runtime/corpus`.
