# LangGraph Orchestration Framework Skeleton

A clean, production-ready python orchestration framework skeleton powered by **LangGraph**. It supports triggering workflows via:
1. **CLI Commands** (ideal for scheduled crons, scripting, and interactive prompt testing).
2. **FastAPI Web Server** (ideal for webhook receivers, APIs, and microservice architectures).

---

## Project Structure

```
├── .env.example                # Template configuration file
├── .env                        # Local configuration file (not committed to git)
├── requirements.txt            # Package dependencies
└── src
    └── orchestration
        ├── __init__.py         # Package entrypoint exposing the compiled graph
        ├── config.py           # Configuration loader (dotenv + environment variables)
        ├── state.py            # TypedDict state schema definition
        ├── graph.py            # LangGraph StateGraph design (nodes, conditional routing)
        ├── cli.py              # CLI utility entrypoint
        └── server.py           # FastAPI Web Server entrypoint
```

---

## Getting Started

### 1. Prerequisites
Ensure you have **Python 3.10+** installed.

### 2. Setup Virtual Environment
Initialize a virtual environment and install dependencies:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Configuration
Copy the template `.env.example` to `.env`:
```bash
cp .env.example .env
```
Edit `.env` to configure your settings.
- **Mock Mode**: If `OPENAI_API_KEY` is left blank, the framework automatically runs in **Mock/Simulation mode** (no keys required).
- **Real LLM Mode**: Provide an `OPENAI_API_KEY` and optional custom `OPENAI_API_BASE` (e.g. LiteLLM, Ollama, OpenRouter, vLLM) and `OPENAI_MODEL_NAME`.
- **API Security**: The `API_KEY` setting protects web API routes. Requests must include the header `X-API-Key: <your-key>`. If empty, validation is bypassed for local development.

---

## Running and Testing

### 1. CLI Entrypoint
You can trigger orchestration directly from the terminal.

#### Prompt trigger:
```bash
python3 -m src.orchestration.cli prompt --text "Create a summary report"
```

#### Cron simulation:
```bash
python3 -m src.orchestration.cli cron --job-name "weekly_db_cleanup"
```

#### Webhook hook simulation:
```bash
python3 -m src.orchestration.cli hook --event "user_created" --data '{"id": 42, "role": "admin"}'
```

---

### 2. FastAPI Web Server
Run the local reloading development server:
```bash
python3 -m src.orchestration.server
```
The server will start on [http://localhost:8000](http://localhost:8000). You can access the interactive API docs at [http://localhost:8000/docs](http://localhost:8000/docs).

#### Test Endpoints via `curl`

*(Assuming default `API_KEY=secret-token-12345` is configured in your `.env`)*

##### Health check (No authentication required):
```bash
curl -X GET http://localhost:8000/health
```

##### Trigger User Prompt:
```bash
curl -X POST http://localhost:8000/api/v1/prompt \
  -H "Content-Type: application/json" \
  -H "X-API-Key: secret-token-12345" \
  -d '{"text": "Refactor python module", "payload": {"priority": "high"}}'
```

##### Trigger Webhook:
```bash
curl -X POST http://localhost:8000/api/v1/hook \
  -H "Content-Type: application/json" \
  -H "X-API-Key: secret-token-12345" \
  -d '{"event": "subscription_cancelled", "data": {"user_id": 999}}'
```

##### Trigger Cron:
```bash
curl -X POST http://localhost:8000/api/v1/cron \
  -H "Content-Type: application/json" \
  -H "X-API-Key: secret-token-12345" \
  -d '{"job_name": "nightly_data_backup", "metadata": {"destination": "s3://backups"}}'
```
