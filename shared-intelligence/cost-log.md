# Shared Intelligence — Cost & Token Log
> **Purpose:** Log token usage and estimated cost per agent per task. Flag tasks exceeding threshold.
> **Requirement:** Mandatory per Governance Principle #8
> **Threshold:** Flag tasks > 50,000 tokens to orchestrator.
> **Model pricing (2026):** claude-sonnet-4-6 — $3/M input, $15/M output (approximate)

---

## Cost Log

| Date | Agent | Task | Model | Tokens In | Tokens Out | Cost (est.) | Flag |
|------|-------|------|-------|-----------|------------|-------------|------|
| 2026-02-25 | Orchestrator | Governance v3.0 integration | sonnet-4-6 | ~45,000 | ~12,000 | ~$0.315 | — |

---

## Session Hook Log
> Auto-appended by PostToolUse hook in `.claude/settings.local.json`
> Format: [PRE/POST/STOP/NOTIFY] timestamp tool=X status=Y

<!-- Hook entries appended below this line -->

---

## Monthly Summary

| Month | Total Sessions | Est. Total Tokens | Est. Total Cost |
|-------|---------------|-------------------|-----------------|
| 2026-02 | 1 (governance setup) | ~57,000 | ~$0.315 |

---

## Notes
- Costs are estimates based on approximate token counts
- Actual billing tracked in Anthropic Console
- Flag any session > $5 USD to orchestrator for review
[PRE] 10:10:18 tool=unknown
[POST] 10:10:18 tool=unknown status=done
[PRE] 10:10:23 tool=unknown
[POST] 10:10:23 tool=unknown status=done
[PRE] 10:10:24 tool=unknown
[POST] 10:10:24 tool=unknown status=done
[PRE] 10:10:26 tool=unknown
[POST] 10:10:27 tool=unknown status=done
[PRE] 10:10:30 tool=unknown
[POST] 10:10:30 tool=unknown status=done
[PRE] 10:10:32 tool=unknown
[POST] 10:10:33 tool=unknown status=done
[PRE] 10:10:40 tool=unknown
[POST] 10:10:40 tool=unknown status=done
[PRE] 10:10:49 tool=unknown
[POST] 10:10:50 tool=unknown status=done
[PRE] 10:11:00 tool=unknown
[POST] 10:11:00 tool=unknown status=done
[PRE] 10:11:07 tool=unknown
[POST] 10:11:07 tool=unknown status=done
[PRE] 10:11:23 tool=unknown
[POST] 10:11:23 tool=unknown status=done
[PRE] 10:11:32 tool=unknown
[POST] 10:11:33 tool=unknown status=done
[PRE] 10:11:38 tool=unknown
[POST] 10:11:38 tool=unknown status=done
[PRE] 10:11:43 tool=unknown
[POST] 10:11:43 tool=unknown status=done
[PRE] 10:11:46 tool=unknown
[POST] 10:11:46 tool=unknown status=done
[PRE] 10:11:49 tool=unknown
[POST] 10:11:49 tool=unknown status=done
[PRE] 10:11:52 tool=unknown
[POST] 10:11:52 tool=unknown status=done
[PRE] 10:11:56 tool=unknown
[POST] 10:11:57 tool=unknown status=done
[PRE] 10:12:02 tool=unknown
[POST] 10:12:02 tool=unknown status=done
[PRE] 10:12:16 tool=unknown
[POST] 10:12:16 tool=unknown status=done
[PRE] 10:12:32 tool=unknown
[POST] 10:12:32 tool=unknown status=done
[PRE] 10:12:46 tool=unknown
[POST] 10:12:47 tool=unknown status=done
[PRE] 10:13:08 tool=unknown
[POST] 10:13:08 tool=unknown status=done
[PRE] 10:13:16 tool=unknown
[POST] 10:13:17 tool=unknown status=done
[PRE] 10:13:20 tool=unknown
[POST] 10:13:21 tool=unknown status=done
[PRE] 10:13:24 tool=unknown
[POST] 10:13:25 tool=unknown status=done
[PRE] 10:13:29 tool=unknown
[POST] 10:13:29 tool=unknown status=done
[PRE] 10:13:35 tool=unknown
[POST] 10:13:35 tool=unknown status=done
[PRE] 10:13:44 tool=unknown
[POST] 10:13:44 tool=unknown status=done
[PRE] 10:13:48 tool=unknown
[POST] 10:13:49 tool=unknown status=done
[PRE] 10:13:56 tool=unknown
[POST] 10:13:56 tool=unknown status=done
[PRE] 10:14:05 tool=unknown
[POST] 10:14:05 tool=unknown status=done
[PRE] 10:14:37 tool=unknown
[POST] 10:14:37 tool=unknown status=done
[PRE] 10:15:08 tool=unknown
[POST] 10:15:08 tool=unknown status=done
[PRE] 10:15:21 tool=unknown
[POST] 10:15:21 tool=unknown status=done
[PRE] 10:15:30 tool=unknown
[POST] 10:15:31 tool=unknown status=done
[PRE] 10:15:34 tool=unknown
[POST] 10:15:37 tool=unknown status=done
[PRE] 10:15:40 tool=unknown
[PRE] 10:15:46 tool=unknown
