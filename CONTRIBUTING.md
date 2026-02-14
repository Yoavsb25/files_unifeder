# Contributing to PDF Batch Merger

Thank you for your interest in contributing. This document points you to the project's code standards and quality targets.

## Code standards and quality bar

The codebase aims for a **9/10** engineering standard across architecture, design, and readability. Contributors should:

- **Read the quality bar** in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) (search for "Quality bar (Target 9/10)"). It covers dependency direction, config schema, single job loading, exception naming, merge state, legacy API deprecation, and method decomposition.
- **Follow the improvement roadmap** in [docs/IMPROVEMENT_ROADMAP.md](docs/IMPROVEMENT_ROADMAP.md) for the full improvement plan, phased execution, and success criteria.
- **Use the Public API** for any external integrations: import only from the `pdf_merger` package root (e.g. `run_merge_job`, `load_config`, `MergeResult`). See the Public API section in `docs/ARCHITECTURE.md`.

## Development and testing

- Run the test suite with `pytest`; see [docs/TESTING.md](docs/TESTING.md) for structure and conventions.
- UI unit tests mock Tkinter/CustomTkinter so no display is required.

## Questions

For licenses, commercial use, or technical support, contact your software provider or the system integrator managing this deployment.
