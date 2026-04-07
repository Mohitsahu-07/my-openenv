import os
import json
from openai import OpenAI
from env import DataCustodianEnv, Action

def run_baseline(task_id: str):
    print(f"\n--- Running Baseline for Task: {task_id} ---")
    client = OpenAI(
        base_url='http://localhost:11434/v1',
        api_key='ollama' # required, but unused
    )
    env = DataCustodianEnv(task_id=task_id)
    obs = env.reset()
    
    system_prompt = (
        "You are an expert Data Engineer acting as an autonomous agent to clean a legacy SQLite database.\n"
        "You will receive the current database schema and the results of your last query.\n"
        "You must respond with a JSON object representing your next action.\n"
        "Format:\n"
        "{\n"
        "  \"action_type\": \"execute_sql\" | \"submit_task\",\n"
        "  \"query\": \"<YOUR SQL QUERY HERE>\" (only if action_type is execute_sql)\n"
        "}\n\n"
        "Instructions based on current task:\n"
        "- easy: Update the 'users' table. Format all 'email' correctly to lowercase. Standardize 'phone' by removing all hyphens (-).\n"
        "- medium: Update the 'orders' table. Extract the JSON metadata into two new columns 'payment_method' and 'shipping' using ALTER TABLE and UPDATE with SQLite json_extract, then drop the 'metadata' column natively (ALTER TABLE orders DROP COLUMN metadata).\n"
        "- hard: Normalize the 'purchases' table. Create 'customers' and 'orders' tables with proper columns and foreign keys, insert the unique data, then DROP 'purchases'.\n\n"
        "When the goal is accomplished, output {\"action_type\": \"submit_task\"} to finish."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"The environment is initialized for task '{task_id}'. Current Observation:\n{obs.model_dump_json(indent=2)}"}
    ]

    max_steps = 15

    for step in range(max_steps):
        print(f"Step {step+1}: Generating response...", end=" ")
        
        response = client.chat.completions.create(
            model="llama3", # Local model via Ollama
            messages=messages,
            response_format={"type": "json_object"}
        )
        
        agent_reply = response.choices[0].message.content
        messages.append({"role": "assistant", "content": agent_reply})
        
        try:
            action_dict = json.loads(agent_reply)
            action = Action(**action_dict)
        except Exception as e:
            print(f"Error parsing JSON action: {e}\nAgent sent: {agent_reply}")
            break
            
        print(f"-> {action.action_type}")
        if action.query:
            print(f"Query: {action.query}")

        obs, final_score, done, info = env.step(action)
        
        if done:
            print(f"Episode Completed. Final Graded Score: {final_score}")
            env.close()
            return final_score
            
        messages.append({
            "role": "user", 
            "content": f"Observation after execution:\n{obs.model_dump_json(indent=2)}"
        })
        
    print("Failed to finish task within max steps.")
    env.close()
    return 0.0

if __name__ == "__main__":
    scores = {}
    for t in ["easy", "medium", "hard"]:
        scores[t] = run_baseline(t)
    
    print("\n=== Final Results ===")
    for k, v in scores.items():
        print(f"Task '{k}': {v}/1.0")
