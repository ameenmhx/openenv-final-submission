from fastapi import FastAPI
from pydantic import BaseModel
from environment import ChaosEnvEngine, SystemAction

# 1. Turn on the Web Server and the Game Engine
app = FastAPI(title="ChaosEnv API")
env = ChaosEnvEngine()

# A simple helper model for the reset command
class ResetRequest(BaseModel):
    task_id: str

# ---------------------------------------------------------
# STANDARD OPENENV ENDPOINTS (How the AI plays the game)
# ---------------------------------------------------------

@app.get("/")
def read_root():
    """A simple check to ensure the server is awake."""
    return {"status": "ChaosEnv Server is LIVE and ready for testing."}

@app.post("/reset")
def reset_environment(req: ResetRequest):
    """The AI calls this to start a new game/task."""
    state = env.reset(req.task_id)
    return state

@app.post("/step")
def step_environment(action: SystemAction):
    """The AI calls this to take an action. It returns the new state and reward."""
    state, reward = env.step(action)
    return {"observation": state, "reward": reward}

@app.get("/state")
def get_state():
    """The AI calls this to look at the current state without taking an action."""
    return env.get_state()

# ---------------------------------------------------------
# HACKATHON REQUIRED ENDPOINTS (For the Judges' Robots)
# ---------------------------------------------------------

@app.get("/tasks")
def get_tasks():
    """Judges' robot calls this to see what tasks are available."""
    return {
        "tasks": ["task_1_easy", "task_2_medium", "task_3_hard"],
        "action_schema": SystemAction.model_json_schema()
    }

@app.get("/grader")
def get_grader():
    """Judges' robot calls this to get the final score after a game."""
    # We calculate the current score based on if the system is healthy
    current_score = 1.0 if env.healthy else 0.0
    return {"score": current_score, "feedback": env.last_output}

@app.get("/baseline")
def get_baseline():
    """Judges' robot calls this to trigger the baseline AI test."""
    # We will build the actual AI script in Phase 5. 
    # For now, this just tells the judges the endpoint exists.
    return {"message": "Baseline triggered. Score: 1.0 (Simulation)"}


import uvicorn

def main():
    uvicorn.run("server.app:app", host="0.0.0.0", port=7860)

if __name__ == "__main__":
    main()