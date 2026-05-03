# NovaPulseManager

NovaPulseManager is a Python backend plus React/Electron frontend for managing
Android automation plugins and visual workflows.

## Development setup

### Backend

Install runtime and development dependencies:

```powershell
uv sync --extra dev
```

Start the backend API server from the repository root:

```powershell
python main.py
```

By default the server binds to `127.0.0.1:8765`. Override with:

```powershell
$env:NOVA_FASTAPI_HOST = "127.0.0.1"
$env:NOVA_FASTAPI_PORT = "8765"
python main.py
```

### Frontend

Install dependencies and start the Vite dev server:

```powershell
cd frontend
npm install
npm run dev
```

To run the Electron shell after building frontend assets:

```powershell
cd frontend
npm run build
npm start
```

## Tests

Run the Python test suite from the repository root:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Tests that need SQLite call `init_database(db_path=...)` and use temporary
database files under `database/.pytest/`, so they do not use
`database/nova_auto_script.db`.

## Plugin layout

Legacy plugins live under:

```text
backend/plugins/{plugin_id}/
  manifest.json
  plugin.py
  models.py
  templates/
```

Each `manifest.json` declares the plugin id, display metadata, and an
`entry_point` such as `plugin.py:OrderPlugin`. The current legacy plugin ids are:

- `start_task`
- `permanent_task`
- `order_task`
- `radar_task`

## Logging

Structured JSON logging uses `structlog` when it is installed. If `structlog`
is absent, `backend/core/logging/config.py` falls back to standard-library
logging with a plain text formatter.
