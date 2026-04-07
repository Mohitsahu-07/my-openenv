from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from env import DataCustodianEnv, Action, Observation
from pydantic import BaseModel
from typing import Optional, Any

app = FastAPI(
    title="Data Custodian OpenEnv Environment API",
    description="API exposing the Data Custodian SQLite Environment per the OpenEnv specification.",
    version="1.0.0",
)

# Global environment instance (session-based in production)
env_instance = None


# ─── Health / Metadata / Schema (required by openenv validate --url) ───

@app.get("/health")
def health():
    """Health endpoint required by OpenEnv runtime validation."""
    return {"status": "healthy"}


@app.get("/metadata")
def metadata():
    """Metadata endpoint required by OpenEnv runtime validation."""
    return {
        "name": "data-custodian",
        "description": (
            "An OpenEnv environment where the AI agent acts as a Data Engineer. "
            "The agent is dropped into a messy legacy SQLite database and must "
            "explore the schema, clean the formatting, extract nested JSON, "
            "and normalize the schema to third normal form."
        ),
    }


@app.get("/schema")
def schema():
    """Schema endpoint required by OpenEnv runtime validation."""
    return {
        "action": Action.model_json_schema(),
        "observation": Observation.model_json_schema(),
        "state": {
            "type": "object",
            "properties": {
                "episode_id": {"type": "string"},
                "step_count": {"type": "integer"},
            },
        },
    }


# ─── Core OpenEnv Endpoints: reset / step / state ───

@app.post("/reset")
async def reset(request: Request):
    """
    Reset the environment. Accepts optional JSON body with task_id.
    Handles: no body, empty body, {}, {"task_id": "easy"/"medium"/"hard"}
    """
    global env_instance
    try:
        # Robustly parse optional body
        task_id = "easy"
        body_bytes = await request.body()
        if body_bytes:
            try:
                body = await request.json()
                if isinstance(body, dict) and "task_id" in body:
                    task_id = body["task_id"]
            except Exception:
                pass  # If body isn't valid JSON, use default

        env_instance = DataCustodianEnv(task_id=task_id)
        obs = env_instance.reset()
        return {"observation": obs.model_dump()}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/step")
def step(action: Action):
    """Execute a step in the environment."""
    global env_instance
    if not env_instance:
        raise HTTPException(
            status_code=400,
            detail="Environment not initialized. Call /reset first.",
        )
    obs, reward, done, info = env_instance.step(action)
    return {
        "observation": obs.model_dump(),
        "reward": reward,
        "done": done,
        "info": info,
    }


@app.get("/state")
def state():
    """Return current environment state."""
    global env_instance
    if not env_instance:
        raise HTTPException(
            status_code=400, detail="Environment not initialized."
        )
    return {"state": env_instance.state().model_dump()}


@app.get("/")
def root():
    """Root health-check (legacy compat)."""
    return {"status": "ok", "environment": "data_custodian"}
