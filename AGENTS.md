# FinAgent Agent Guidance

FinAgent is an enterprise tax, expense approval, and contract risk platform. Read `README.md`, `docs/00-project-plan.md`, and the relevant design documents under `docs/` before changing architecture or business state.

## Agent skills

### Issue tracker

Issues and specs live in GitHub Issues for `Yangjon1/finAgent`. Use the `gh` CLI. See `docs/agents/issue-tracker.md`.

### Triage labels

Use the default labels: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, and `wontfix`. See `docs/agents/triage-labels.md`.

### Domain docs

This is a single-context repository. Use the root `GLOSSARY.md` and `docs/adr/` for domain terms and architecture decisions. See `docs/agents/domain.md`.

## Engineering constraints

- Keep deterministic rules, permissions, state transitions, budget checks, payment conditions, and database transactions outside LLM reasoning.
- Do not implement LangGraph Agent behavior before the relevant business service and Tool boundary exist.
- Preserve tenant isolation, auditability, optimistic locking, and the API response envelope.
- Run focused backend tests and frontend checks after changes.
