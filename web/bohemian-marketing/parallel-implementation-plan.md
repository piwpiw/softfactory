# Bohemian Marketing Parallel Implementation Plan

This plan is migrated to the existing orchestrator model.

## Execution Mode
- Queue source: `orchestrator/task-queue.json`
- Runner: `python run_all_agents.py`
- Policy: existing `orchestrator/agent-registry.md` authority boundaries

## 10 Agents x 10 Tasks
- Agent A (coordination): BM-A01 ... BM-A10
- Agent B (frontend): BM-B01 ... BM-B10
- Agent C (backend): BM-C01 ... BM-C10
- Agent D (architecture): BM-D01 ... BM-D10
- Agent E (security): BM-E01 ... BM-E10
- Agent F (product): BM-F01 ... BM-F10
- Agent G (devops): BM-G01 ... BM-G10
- Agent H (frontend advanced): BM-H01 ... BM-H10
- Agent I (qa): BM-I01 ... BM-I10
- Agent J (ops communication): BM-J01 ... BM-J10

## Status Tracking
- Source of truth: `orchestrator/task-queue.json`
- Runtime evidence: `agent_workspaces/*/run_*.json`
- Governance: `orchestrator/README.md`, `orchestrator/agent-registry.md`
