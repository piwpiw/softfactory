# Bohemian Marketing Mission (Orchestrated)

Mission date: 2026-03-02
Mode: queue-driven (run_all_agents.py)
Scope: migrate bohemian-marketing implementation into existing orchestrator + agent system

## Activation
- Task source: `orchestrator/task-queue.json`
- Runner: `python run_all_agents.py`
- Teams: coordination, product, architecture, backend, frontend, qa, security, devops, ops-communication

## Mapping
- A -> coordination (PA-01)
- B/H -> frontend (PA-06)
- C -> backend (PA-05)
- D -> architecture (PA-04)
- E -> security (PA-08)
- F -> product (PA-02/PA-03)
- G -> devops (PA-09)
- I -> qa (PA-07)
- J -> ops-communication (PA-10)

## Expected output
- Queue-driven execution markers under `agent_workspaces/*/run_*.json`
- Task state progression from `pending` -> `in_progress` -> `done/failed`
- Artifact links in each task for handoff and traceability
