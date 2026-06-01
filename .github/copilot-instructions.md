# Copilot instructions for HydroWire (rov-interface)

Purpose: short, machine-friendly guidance for Copilot sessions working on this repository.

---
Build / Test / Publish

- Install runtime deps: pip install -r requirements.txt
- Install dev deps: pip install -r dev-requirements.txt
- Install editable dev environment: pip install -e ".[dev]"

- Run full tests: pytest tests/ -v
- CI-style quick run: pytest -q
- Run a single test: pytest tests/test_client.py::test_send_command_with_device_id -v
- Run tests by keyword: pytest -k "keyword" -v

- Build package: python -m build
- Check built artifacts: twine check dist/*

(Workflows: .github/workflows/ci.yml runs pytest -q; publish.yml runs pytest tests/ -v, python -m build, and twine check)

---
High-level architecture (big picture)

- Package: `hydrowire/` — library entry points and device modules.
- hydrowire/client.py — WebSocketCommandClient: async context-manager that connects to a WebSocket, sends JSON payloads and optionally awaits a response.
- hydrowire/manager.py — HydroWireManager: high-level manager that creates/owns the client, routes commands to devices, supports optional GUI attachment, and exposes convenience top-level `start()` / `get_manager()` functions. A module-global `_manager` provides a singleton-style helper.
- hydrowire/devices/ — small device helper modules (e.g., led, basic_pwm) used by callers.
- tests/ — integration-style unit tests that start a local websockets server (websockets.serve) and assert on sent JSON payloads.
- Packaging: pyproject.toml + setuptools build; CI uses actions to run tests across Python versions and publish with twine.

---
Key repo-specific conventions and patterns

- Async-first: public API uses async/await. Use pytest-asyncio for tests (already in dev deps).

- Command shape (canonical): callers pass an input dict with an "action" key and other parameters. On send, client transforms this into a payload of the form:
  {"device": "<device_id>", "cmd": "<action>", "params": { ...other keys... }}
  Routines and tests rely on this exact shape. Preserve the "action" -> "cmd" transformation and the `params` grouping when adding features or tests.

- Client lifecycle: WebSocketCommandClient connects lazily on first use and implements async context-manager semantics (use `async with` or call `connect()`/`close()` from the manager). HydroWireManager.initialize() must be called before sending commands (manager raises if not initialized).

- Tests: tests instantiate ephemeral websockets servers on localhost and ports (8765, 8766 in existing tests). Keep tests deterministic by binding to explicit free ports or using pytest fixtures mirroring the existing pattern.

- Packaging & CI:
  - pyproject.toml contains metadata and optional dev extras (.[dev]) used by CI.
  - GH Actions: .github/workflows/ci.yml and publish.yml define test matrix and publish steps — follow those commands when reproducing CI locally.

- Minimal external dependencies: websockets is the runtime dependency; test-suite depends on pytest and pytest-asyncio.

---
Useful quick commands (copy/paste)

- Install dev env: pip install -e ".[dev]"
- Run one test: pytest tests/test_client.py::test_send_command_with_device_id -q
- Run tests across suite: pytest tests/ -v
- Build artifact: python -m build

---
Where to look next

- README.md — usage examples, quick-start snippets
- pyproject.toml — packaging metadata and dev extras
- hydrowire/client.py and hydrowire/manager.py — main implementation to inspect for behavior or extension points
- .github/workflows/* — CI and publish commands

---
If you want this expanded to include recommended linters / formatters or a troubleshooting checklist (test failures, common pitfalls when mocking websockets), say which area to cover and Copilot will add it.

---
Suggested improvements for Copilot sessions

- Python & environment: Project supports Python 3.9–3.13 (see pyproject.toml). Use a venv and install dev extras: pip install -e ".[dev]".
- Running tests: CI-style quick run: pytest -q. Run a single test: pytest tests/test_client.py::test_send_command_with_device_id -q
- Key files to inspect: hydrowire/client.py, hydrowire/manager.py, tests/*.py, pyproject.toml, .github/workflows/*
- Command shape & lifecycle: Preserve the command JSON shape (action -> cmd, params grouping) and call HydroWireManager.initialize() before sending commands.
- Tests: Tests create ephemeral websockets servers on localhost (ports 8765, 8766). Keep tests deterministic by binding to explicit ports or using fixtures.
- CI & publishing: .github/workflows/ci.yml runs pytest -q; publishing uses python -m build and twine check dist/*.
- AI assistant configs found: .github/copilot-instructions.md (this file). No CLAUDE.md, .cursorrules, AGENTS.md, or other common AI assistant config files detected.

---
If you'd like these suggestions folded into the top sections, or want additional checks (linters, coverage, or troubleshooting steps), say which and Copilot will update the file.
