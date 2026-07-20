# CareerOS

> India's AI Career Operating System — an AI layer above the job ecosystem that continuously
> understands a candidate, surfaces genuinely relevant opportunities, and prepares them to win,
> while keeping a human in control of anything that leaves the platform.
>
> CareerOS is **not** a job board, **not** a resume builder, and **not** an auto-applier.

## Status

**Phase:** Implementation — **Milestone M0 (Foundations)**.
Currently only repository scaffolding exists. No application/business logic yet.
See the roadmap: [`docs/roadmap/M0-foundations.md`](docs/roadmap/M0-foundations.md).

## Read this first

Every contributor (human or AI) must read and obey these before writing code:

- [`AGENTS.md`](AGENTS.md) — contributor orientation and golden rules.
- [`docs/engineering-constitution.md`](docs/engineering-constitution.md) — **highest-priority document.**

## Locked architecture documents (source of truth)

These are LOCKED. No code may violate them without an ADR (see [`docs/adr/`](docs/adr/)).

1. [Vision](docs/vision.md)
2. [System Architecture](docs/system-architecture.md)
3. [Domain Model](docs/domain-model.md)
4. [AI Architecture](docs/ai-architecture.md)
5. [Technical Architecture](docs/technical-architecture.md)
6. [Engineering Constitution](docs/engineering-constitution.md)

## Repository layout

Top-level structure (per Technical Architecture §1). Directories are placeholders until
their milestone builds them out.

| Path | Purpose |
|------|---------|
| `apps/` | Deployable apps (web, api, worker; admin in Phase 2) |
| `packages/` | Shared TS packages (contracts, sdk, ui, config) |
| `shared/` | Shared Python (shared_kernel, platform, event_contracts) |
| `agents/` | AI engine (orchestration, subgraphs, tools, memory, prompts) |
| `contexts/` | DDD bounded contexts |
| `evals/` | Golden datasets + eval runners (CI quality gate) |
| `infra/` | Docker, deploy config, migrations |
| `docs/` | Locked specs, ADRs, roadmap |
| `.cursor/rules/` | Cursor rules that enforce the constitution during coding |

## Local development

- [`docs/development.md`](docs/development.md) — clone, install, `docker compose up`, common commands
- [`docs/environments.md`](docs/environments.md) — `CAREEROS_*` settings, secrets, `.env.example`
- [`.env.example`](.env.example) — tracked template (copy to `.env`; never commit secrets)

```bash
docker compose up --build
```

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for the full workflow: branch naming, Conventional
Commits, ADRs, PR/issue templates, Constitution §24 review checklist, and §25 Definition of
Done. Orientation and golden rules: [`AGENTS.md`](AGENTS.md).
Any deviation from a locked document requires an ADR merged first.

## License

Proprietary — see [`LICENSE`](LICENSE). All rights reserved.
