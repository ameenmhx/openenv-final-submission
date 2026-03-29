import os
import requests
import json
from openai import OpenAI

# The URL where your environment is hosted on Hugging Face
BASE_URL = "https://ameenmhx-chaosenv-simulator.hf.space"

def run_baseline():
    print("🚀 Starting ChaosEnv Baseline Evaluation...")
    
    # The judges will provide their own API key when they run this
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("⚠️ No OPENAI_API_KEY found. Judges will supply this during evaluation.")
        return

    client = OpenAI(api_key=api_key)
    tasks = ["task_1_easy", "task_2_medium", "task_3_hard"]
    
    for task in tasks:
        print(f"\n--- Testing {task.upper()} ---")
        
        # 1. Reset the environment for the new task
        reset_res = requests.post(f"{BASE_URL}/reset", json={"task_id": task})
        observation = reset_res.json()
        
        is_done = False
        step_count = 0
        
        # 2. Let the AI play the game (max 10 steps)
        while not is_done and step_count < 10:
            step_count += 1
            
            # Give the AI the current system state
            prompt = f"""
            You are an autonomous SRE. The server has an outage.
            Current State: {json.dumps(observation)}
            
            Choose your next action. You must respond with ONLY a valid JSON object matching this schema:
            {{"command": "view_logs"|"view_config"|"restart_service"|"rollback_deployment"|"kill_process", "target": "web_server"|"database"|"analytics_worker"}}
            """
            
            try:
                # Ask OpenAI for the next move
                response = client.chat.completions.create(
                    model="gpt-4-turbo",
                    response_format={ "type": "json_object" },
                    messages=[{"role": "user", "content": prompt}]
                )
                
                action = json.loads(response.choices[0].message.content)
                print(f"🤖 AI Action: {action}")
                
                # Send the AI's action to your server
                step_res = requests.post(f"{BASE_URL}/step", json=action)
                result = step_res.json()
                
                observation = result["observation"]
                is_done = result["reward"]["is_done"]
                
            except Exception as e:
                print(f"Error calling AI: {e}")
                break
                
        # 3. Get the final score from the grader
        grader_res = requests.get(f"{BASE_URL}/grader")
        final_score = grader_res.json()["score"]
        print(f"✅ {task} Complete. Final Score: {final_score}/1.0")

if __name__ == "__main__":
    run_baseline()