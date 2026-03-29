from pydantic import BaseModel, Field
from typing import List, Tuple, Dict, Any

# =====================================================================
# 1. THE DATA SCHEMAS (From Phase 2)
# =====================================================================
class SystemObservation(BaseModel):
    active_alerts: List[str] = Field(description="List of active monitoring alerts.")
    cpu_usage_percent: float = Field(description="Current CPU usage (0.0 to 100.0).")
    memory_usage_percent: float = Field(description="Current Memory usage (0.0 to 100.0).")
    last_terminal_output: str = Field(description="The console output from the previous action.")
    system_healthy: bool = Field(description="Boolean indicating if the outage is fully resolved.")

class SystemAction(BaseModel):
    command: str = Field(description="Options: 'view_logs', 'view_config', 'restart_service', 'rollback_deployment', 'kill_process'")
    target: str = Field(description="Options: 'web_server', 'database', 'analytics_worker'")

class SystemReward(BaseModel):
    score: float = Field(description="Continuous reward from 0.0 to 1.0.")
    is_done: bool = Field(description="True if the episode is over.")
    feedback: str = Field(description="Reasoning for the current score.")

# =====================================================================
# 2. THE SIMULATION ENGINE (The State Machine)
# =====================================================================
class ChaosEnvEngine:
    def __init__(self):
        self.current_task = ""
        self.step_count = 0
        self.max_steps = 10  # If the AI takes more than 10 steps, it fails.
        
        # System State Variables
        self.alerts = []
        self.cpu = 50.0
        self.memory = 50.0
        self.last_output = "System initialized."
        self.healthy = True
        
        # Task Progress Flags
        self.rogue_killed = False 

    def reset(self, task_id: str) -> SystemObservation:
        """Sets up the simulated server crash based on the chosen difficulty."""
        self.current_task = task_id
        self.step_count = 0
        self.healthy = False
        self.rogue_killed = False
        
        if task_id == "task_1_easy":
            self.alerts = ["CRITICAL: Web Server Down - HTTP 500"]
            self.cpu = 45.0
            self.memory = 60.0
            self.last_output = "Alert triggered. Web server unresponsive."
            
        elif task_id == "task_2_medium":
            self.alerts = ["CRITICAL: Database Timeout on Web Server"]
            self.cpu = 30.0
            self.memory = 55.0
            self.last_output = "Alert triggered. Users cannot log in."
            
        elif task_id == "task_3_hard":
            self.alerts = ["FATAL: Database Locked", "WARNING: Memory 99%"]
            self.cpu = 85.0
            self.memory = 99.0
            self.last_output = "Multiple alerts. System cascading failure."

        return self.get_state()

    def get_state(self) -> SystemObservation:
        """Packages the current variables into our Pydantic Observation model."""
        return SystemObservation(
            active_alerts=self.alerts,
            cpu_usage_percent=self.cpu,
            memory_usage_percent=self.memory,
            last_terminal_output=self.last_output,
            system_healthy=self.healthy
        )

    def step(self, action: SystemAction) -> Tuple[SystemObservation, SystemReward]:
        """Processes the AI's command, updates the system, and scores it."""
        self.step_count += 1
        reward_score = 0.0
        is_done = False
        feedback = "Command executed. No change in system health."
        
        cmd = action.command
        tgt = action.target

        # -----------------------------------------
        # Logic for Task 1 (Easy) - Routine Crash
        # -----------------------------------------
        if self.current_task == "task_1_easy":
            if cmd == "restart_service" and tgt == "web_server":
                self.healthy = True
                self.alerts = []
                self.last_output = "SUCCESS: Web server restarted. Traffic flowing normally."
                reward_score = 1.0
                is_done = True
                feedback = "Perfect! You identified the crashed service and restarted it."
            else:
                self.last_output = f"Executed {cmd} on {tgt}. No effect."
                reward_score = -0.1 # Slight penalty for wrong moves

        # -----------------------------------------
        # Logic for Task 2 (Medium) - Bad Deployment
        # -----------------------------------------
        elif self.current_task == "task_2_medium":
            if cmd == "view_logs" and tgt == "web_server":
                self.last_output = "LOGS: 'Connection refused to Database IP 10.0.0.99'"
                reward_score = 0.2 # Partial reward for investigating
                feedback = "Good debugging. Found the connection error."
            elif cmd == "rollback_deployment" and tgt == "web_server":
                self.healthy = True
                self.alerts = []
                self.last_output = "SUCCESS: Rolled back to previous stable config. DB Connected."
                reward_score = 1.0
                is_done = True
                feedback = "Excellent! You rolled back the bad configuration."
            else:
                self.last_output = f"Executed {cmd} on {tgt}. Issue persists."

        # -----------------------------------------
        # Logic for Task 3 (Hard) - Memory Leak
        # -----------------------------------------
        elif self.current_task == "task_3_hard":
            if cmd == "kill_process" and tgt == "analytics_worker":
                self.rogue_killed = True
                self.memory = 45.0
                self.alerts = ["FATAL: Database Locked"] # Memory warning goes away
                self.last_output = "Process terminated. Memory usage dropping."
                reward_score = 0.4 # Partial reward
                feedback = "Great! You killed the memory leak. The DB is still locked."
            elif cmd == "restart_service" and tgt == "database":
                if self.rogue_killed:
                    self.healthy = True
                    self.alerts = []
                    self.last_output = "SUCCESS: Database restarted. System fully recovered."
                    reward_score = 1.0
                    is_done = True
                    feedback = "Flawless execution! Memory freed and DB restored."
                else:
                    self.last_output = "ERROR: Cannot restart DB. Out of memory."
                    reward_score = -0.2
                    feedback = "You must free up memory before restarting the database."
            else:
                self.last_output = f"Executed {cmd} on {tgt}. Issue persists."

        # Fail the AI if it takes too many turns
        if self.step_count >= self.max_steps and not is_done:
            is_done = True
            reward_score = 0.0
            feedback = "Task failed: Exceeded maximum allowed terminal commands."

        # Package the reward
        reward = SystemReward(score=reward_score, is_done=is_done, feedback=feedback)
        
        return self.get_state(), reward