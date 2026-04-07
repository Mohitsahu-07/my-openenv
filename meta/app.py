from fastapi import FastAPI, HTTPException
from env import DataCustodianEnv, Action
from pydantic import BaseModel

app = FastAPI(title="Data Custodian OpenEnv Environment API",
              description="API exposing the Data Custodian SQLite Environment per the OpenEnv specification.")

# We keep a simple global instance for the hackathon demo.
# In a robust production setting, this would be session-based.
env_instance = None

class ResetResponse(BaseModel):
    observation: dict

@app.post("/reset/{task_id}", response_model=ResetResponse)
def reset(task_id: str):
    global env_instance
    try:
        env_instance = DataCustodianEnv(task_id=task_id)
        obs = env_instance.reset()
        return {"observation": obs.model_dump()}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/step")
def step(action: Action):
    global env_instance
    if not env_instance:
         raise HTTPException(status_code=400, detail="Environment not initialized. Call /reset first.")
    
    obs, reward, done, info = env_instance.step(action)
    return {"observation": obs.model_dump(), "reward": reward, "done": done, "info": info}

@app.get("/state")
def state():
    global env_instance
    if not env_instance:
         raise HTTPException(status_code=400, detail="Environment not initialized.")
    return {"state": env_instance.state().model_dump()}

@app.get("/")
def health():
    return {"status": "ok", "environment": "data_custodian"}
