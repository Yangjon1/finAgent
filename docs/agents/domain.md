# Domain documentation

FinAgent uses the single-context layout:

```text
/
├── GLOSSARY.md
└── docs/adr/
```

Before exploring a domain area, read the root `GLOSSARY.md` when it exists and read ADRs in `docs/adr/` that touch the area. If these files do not exist yet, proceed without treating their absence as a problem. Add glossary terms and ADRs lazily when domain language or architectural decisions are resolved.

Use glossary terms consistently in issue titles, code, tests, and proposals. If a change conflicts with an ADR, identify the conflict explicitly before proceeding.
