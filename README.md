# AI Automation Command Center

A framework-agnostic QA automation control plane. The current MVP discovers a local automation project, normalizes pytest tests into a Test Explorer, reports adapter capabilities, supports explicitly authorized single-test execution, records local execution history, and optionally retains bounded evidence artifacts.

## Current MVP scope

- Python/FastAPI API for project and test discovery
- Read-only discovery with generated-directory and symlink exclusions
- Normalized test metadata and adapter capability reporting
- React/TypeScript Test Explorer with search and test details
- Explicitly authorized local pytest execution with timeout and normalized JUnit results
- Background execution lifecycle, status polling, and cooperative cancellation
- Local SQLite execution history with minimized normalized summaries
- Deterministic failure categories and regression fixtures
- Opt-in local evidence artifact storage with per-file and total size limits, retention, and digest verification
- Backend pytest and frontend build workflows in GitHub Actions

The current cumulative candidate is [PR #17](https://github.com/princekdavid/ai-automation-command-center/pull/17), kept as a draft and not merged. Additional framework adapters, remote repository connections, multi-user authentication/authorization, OS-level execution sandboxing, and AI analysis are not implemented. See [Implementation Status](IMPLEMENTATION_STATUS.md), [Changelog](CHANGELOG.md), and [the artifact-retention notes](docs/EVIDENCE_ARTIFACT_RETENTION.md).

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
6. View recent runs and any retained evidence in Local Run History.

**Execution safety:** running a test may execute arbitrary code from that project. The authorization checkbox is not an OS-level sandbox or identity/access-control mechanism. Only authorize projects you trust. Keep the API bound to localhost. The API has no user authentication; do not expose it to a LAN, public network, or untrusted browser origin without implementing and reviewing authentication and network access controls.

**Local history:** compact execution summaries are stored in SQLite at `~/.ai-automation-command-center/history.sqlite3` by default. Set `AAC_RUN_DB_PATH` to use another location. Raw stdout/stderr and raw per-test failure messages are not persisted; the database is not encrypted and has no retention policy yet.

**Evidence artifacts:** persistence is disabled by default. Enable it deliberately with `AAC_ARTIFACTS_ENABLED=true`; optionally set `AAC_ARTIFACTS_DIR` to a dedicated local directory. The default is `~/.ai-automation-command-center/artifacts`. JUnit reports may contain customer data, identifiers, or secrets emitted by tests. Treat artifact storage as sensitive local data; do not enable it for untrusted projects or store secrets intentionally. See [artifact-retention limits and known boundaries](docs/EVIDENCE_ARTIFACT_RETENTION.md).

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

Do not treat a change as validated until the relevant checks have passed on the exact code commit under review.

## Project rules

- Keep framework-specific discovery and execution inside adapters.
- Use normalized contracts at the UI/API boundary.
- Do not claim support for a capability unless it is implemented and validated.
- Do not add paid AI services, secrets, auto-merge, deployments, or repository-mutating behavior without a separate documented decision.
- Keep implementation status and changelog current with each meaningful milestone.
