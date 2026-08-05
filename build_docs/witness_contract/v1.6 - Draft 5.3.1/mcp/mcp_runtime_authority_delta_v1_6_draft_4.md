# MCP Runtime Authority Delta - v1.6 Draft 4

Status: Draft 4 MCP delta.
Generated: 2026-05-08

## Scope

Draft 4 extends the MCP runtime authority model to account for Agent Lab backup
records and execute-system-command mutation evidence.

## Delta from Draft 3

Draft 3 separated verified MCP tools from target MCP tools and added direct
mutation controls. Draft 4 adds a stronger rule for automated command execution:
backup records must be captured, but backup records alone do not authorize the
mutation outcome.

## Authority ladder

1. command requested;
2. policy evaluated;
3. preflight backup created;
4. command executed;
5. changed files recorded;
6. validation run recorded;
7. rollback route recorded;
8. human approval recorded if needed;
9. promotion commit recorded.

Only steps 1-4 are implied by simple backup-log observations. Steps 5-9 remain
required for release-sensitive promotion.
