# Copilot instructions for HydroWire (rov-interface)

Purpose: concise, machine-friendly guidance for Copilot sessions working on this repository.

---
Build, test, and package

- Install runtime deps: pip install -r requirements.txt
- Install dev deps: pip install -r dev-requirements.txt
- Editable dev env: pip install -e ".[dev]"

- Run full tests: pytest tests/ -v
- Quick CI-style run: pytest -q
- Run a single test: pytest tests/test_client.py::test_send_command_with_device_id -q
- Run tests by keyword: pytest -k "keyword" -v

- Build package: python -m build
- Check built artifacts: twine check dist/*

(Workflows: .github/workflows/ci.yml runs pytest -q; publish.yml runs pytest -v, python -m build, twine check)

---
High-level architecture

- Package: `hydrowire/` — library entry points, device helpers, and optional GUI helper.
- hydrowire/client.py — WebSocketCommandClient: async context-manager that connects, sends JSON payloads, and optionally awaits a response.
- hydrowire/manager.py — HydroWireManager: high-level manager that creates/owns the client, routes commands to devices, supports optional GUI attachment (background thread), and provides convenience functions (`start()`, `get_manager()`). A module-global `_manager` is used as a singleton helper.
- hydrowire/devices/ — small device helpers (e.g., led, basic_pwm) used by callers.
- tests/ — integration-style tests that start local websockets servers and validate sent JSON payloads.
- Packaging: pyproject.toml + setuptools; CI runs tests across Python versions and publishes built artifacts.

---
Key conventions (repo-specific)

- Async-first API: public functions are async; tests use pytest-asyncio.

- Canonical command shape: callers pass a command dict containing an "action" key. Sent payloads MUST be:
  {"device": "<device_id>", "cmd": "<action>", "params": { ...other keys... }}
  Tests and callers rely on this exact transformation ("action" -> "cmd", remaining keys under "params").

- Client lifecycle: WebSocketCommandClient connects lazily; prefer using `async with WebSocketCommandClient(...)` or call HydroWireManager.initialize() before sending commands. HydroWireManager raises if not initialized.

- GUI integration: HydroWireManager.start(gui_enabled=True) launches a GUI in a separate thread. The manager attempts graceful shutdown by calling the provided stop callable (sync or async) and joining the thread.

- Tests & ports: Tests start ephemeral websocket servers on explicit ports (8765, 8766). Keep tests deterministic by binding to explicit ports or using fixtures that allocate free ports.

- Minimal runtime deps: websockets is the runtime dependency; dev deps include pytest and pytest-asyncio (listed in pyproject.toml).

---
Where to look first

- README.md — usage examples and quick-start
- pyproject.toml — dependency matrix and supported Python versions
- hydrowire/client.py and hydrowire/manager.py — core implementation
- tests/ — example usage and test patterns (websocket server handlers)
- .github/workflows/* — CI commands and release steps

---
Other AI-config files found

- .github/copilot-instructions.md (this file)
- No CLAUDE.md, .cursorrules, AGENTS.md, .windsurfrules, CONVENTIONS.md, or similar assistant configs detected.

---
Suggested improvements (optional)

- Add a tiny CONTRIBUTING.md with testing guidelines (port allocation, async test patterns) if multiple contributors run tests concurrently.
- Consider adding a simple pre-commit config or lint step (black/ruff) in CI if style enforcement is desired — not added here to avoid inventing requirements.

---
Changes applied

- Consolidated and clarified build/test/package commands
- Clarified architecture and command shape rules
- Documented GUI lifecycle and test port conventions

---
If this update looks good, confirm and Copilot will commit the change. After committing, would you like to configure any MCP servers relevant to this project?

If you want further expansion (linters, troubleshooting checklist, example fixtures for free-port tests), say which area to cover and Copilot will add it.
