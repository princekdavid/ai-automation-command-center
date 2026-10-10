# AI Automation Command Center

A framework-agnostic QA automation control plane. The current MVP discovers a local automation project, normalizes pytest tests into a Test Explorer, reports adapter capabilities, and supports explicitly authorized single-test execution through a controlled local pytest adapter.

## Current MVP scope

- Python/FastAPI API for project and test discovery
- Read-only discovery with generated-directory and symlink exclusions
- Normalized test metadata and adapter capability reporting
- React/TypeScript Test Explorer with search and test details
- Explicitly authorized local pytest execution, timeout, and normalized JUnit results
- Local SQLite run history with minimized normalized summaries
- Deterministic failure categories displayed alongside failed results
- Backend pytest and frontend build workflows in GitHub Actions

The MVP does **not** yet include background runs/cancellation, evidence artifact storage, remote repository connections, additional execution adapters, or AI analysis. See [Implementation Status](IMPLEMENTATION_STATUS.md) and [Changelog](CHANGELOG.md).

## Requirements

- Python 3.11 or newer
- Node.js 20 or newer and npm

No paid AI API or hosted coding agent is required for the current MVP.

## Run locally

### 1. Start the backend

From the repository root:

```bash
cd backend
python -m venv .venv
```

Activate the environment:

- macOS/Linux: `source .venv/bin/activate`
- Windows PowerShell: `.venv\\Scripts\\Activate.ps1`

Install dependencies and start the API:

```bash
python -m pip install --upgrade pip
pip install -e ".[dev]"
uvicorn aac.api:app --reload --host 127.0.0.1 --port 8000
```

Health check: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

### 2. Start the frontend

In a second terminal from the repository root:

```bash
cd frontend
npm install
npm run dev
```

Open the local Vite URL printed in the terminal (normally [http://localhost:5173](http://localhost:5173)).

The API permits only the two local Vite origins by default. For a different trusted frontend origin, set `AAC_CORS_ORIGINS` to a comma-separated list of exact origins before starting the backend. Do not use wildcard origins for a deployed environment.

To point the frontend at another API URL, set `VITE_API_BASE_URL` before starting/building Vite; it defaults to `http://localhost:8000`.

## Use the Test Explorer

1. Enter the absolute local path to a trusted project directory that the backend process can access.
2. Select **Discover tests**.
3. Select a discovered test to inspect its normalized metadata.
4. To execute it, explicitly check the authorization box and choose **Run selected test**.
5. Review the normalized status, failure category, and message.
6. View recent runs in the Local Run History section.

**Execution safety:** running a test may execute arbitrary code from that project. Only authorize projects you trust. The authorization checkbox is not an OS-level sandbox. Keep the API bound to localhost unless you have implemented appropriate network access controls and authentication.

**Local history:** compact execution summaries are stored in SQLite at `~/.ai-automation-command-center/history.sqlite3` by default. Set `AAC_RUN_DB_PATH` to use another location. Raw stdout/stderr and raw failure messages are not persisted; the database is not encrypted and has no retention policy yet. See [Execution Contract](docs/EXECUTION_CONTRACT.md).

## Validate changes

Backend:

```bash
cd backend
pip install -e ".[dev]"
pytest
```

Frontend:

```bash
cd frontend
npm install
npm run build
```

Do not treat a change as validated until the relevant checks have passed on the exact commit under review.

## Project rules

- Keep framework-specific discovery and execution inside adapters.
- Use normalized contracts at the UI/API boundary.
- Do not claim support for a capability unless it is implemented and validated.
- Do not add paid AI services, secrets, auto-merge, deployments, or repository-mutating behavior without a separate documented decision.
- Keep implementation status and changelog current with each meaningful milestone.
