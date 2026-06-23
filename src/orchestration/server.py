import uvicorn
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Header, Depends, status
from pydantic import BaseModel

from src.orchestration.config import API_KEY, HOST, PORT, print_config
from src.orchestration.graph import app as orchestrator_app

app = FastAPI(
    title="Orchestration Framework API",
    description="LangGraph-based backend API for crons, hooks, and user prompts.",
    version="1.0.0"
)

# ----------------------------------------------------
# Security / API Key Verification Dependency
# ----------------------------------------------------

async def verify_api_key(x_api_key: Optional[str] = Header(None)):
    """
    Validates X-API-Key header matches the configured key (if API_KEY is set).
    """
    # If API_KEY is not set in environment, we disable authentication for easy local dev
    if not API_KEY:
        return
        
    if x_api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-API-Key header."
        )

# ----------------------------------------------------
# Request Schemas
# ----------------------------------------------------

class CronRequest(BaseModel):
    job_name: str
    metadata: Optional[Dict[str, Any]] = None

class HookRequest(BaseModel):
    event: str
    data: Optional[Dict[str, Any]] = None

class PromptRequest(BaseModel):
    text: str
    payload: Optional[Dict[str, Any]] = None

# ----------------------------------------------------
# Endpoints
# ----------------------------------------------------

@app.get("/health", tags=["System"])
def health_check():
    """
    Unauthenticated health status endpoint.
    """
    return {"status": "healthy", "service": "orchestrator"}

@app.post(
    "/api/v1/cron",
    tags=["Triggers"],
    dependencies=[Depends(verify_api_key)]
)
async def trigger_cron(request: CronRequest):
    """
    Called by cron schedulers. Runs a cron-specific orchestration flow.
    """
    payload = {"job_name": request.job_name, **(request.metadata or {})}
    
    initial_state = {
        "source": "cron",
        "user_prompt": f"Triggered cron job: {request.job_name}",
        "payload": payload,
        "messages": [],
        "errors": []
    }
    
    try:
        final_state = orchestrator_app.invoke(initial_state)
        return {
            "status": final_state.get("status"),
            "response": final_state.get("response"),
            "errors": final_state.get("errors")
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Workflow run failed: {str(e)}"
        )

@app.post(
    "/api/v1/hook",
    tags=["Triggers"],
    dependencies=[Depends(verify_api_key)]
)
async def trigger_hook(request: HookRequest):
    """
    Called by incoming webhooks (e.g. GitHub hooks, database triggers).
    """
    payload = {"event": request.event, "event_data": (request.data or {})}
    
    initial_state = {
        "source": "hook",
        "user_prompt": f"Triggered webhook event: {request.event}",
        "payload": payload,
        "messages": [],
        "errors": []
    }
    
    try:
        final_state = orchestrator_app.invoke(initial_state)
        return {
            "status": final_state.get("status"),
            "response": final_state.get("response"),
            "errors": final_state.get("errors")
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Workflow run failed: {str(e)}"
        )

@app.post(
    "/api/v1/prompt",
    tags=["Triggers"],
    dependencies=[Depends(verify_api_key)]
)
async def trigger_prompt(request: PromptRequest):
    """
    Called by interactive user prompt interfaces.
    """
    initial_state = {
        "source": "prompt",
        "user_prompt": request.text,
        "payload": request.payload or {},
        "messages": [],
        "errors": []
    }
    
    try:
        final_state = orchestrator_app.invoke(initial_state)
        return {
            "status": final_state.get("status"),
            "response": final_state.get("response"),
            "errors": final_state.get("errors")
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Workflow run failed: {str(e)}"
        )

# ----------------------------------------------------
# Main Run Entrypoint
# ----------------------------------------------------

@app.on_event("startup")
def startup_event():
    print_config()

def start():
    uvicorn.run("src.orchestration.server:app", host=HOST, port=PORT, reload=True)

if __name__ == "__main__":
    start()
