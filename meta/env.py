from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict, Tuple
import sqlite3
import os
from db_generator import generate_db

class Observation(BaseModel):
    last_query: Optional[str] = None
    query_result: Optional[List[Dict[str, Any]]] = None
    query_error: Optional[str] = None
    schema_info: str

class Action(BaseModel):
    action_type: str = Field(..., description="'execute_sql' or 'submit_task'")
    query: Optional[str] = Field(None, description="The SQL query to execute")

class Reward(BaseModel):
    score: float
    message: str

class DataCustodianEnv:
    def __init__(self, task_id="easy"):
        self.task_id = task_id
        self.db_path = "legacy.db"
        self.conn = None
        self.last_observation = None
        self.is_done = False
        self.reset()
        
    def _get_schema(self) -> str:
        if not self.conn:
            return ""
        c = self.conn.cursor()
        c.execute("SELECT sql FROM sqlite_master WHERE type='table'")
        schemas = [row[0] for row in c.fetchall() if row[0]]
        return "\n\n".join(schemas)

    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None

    def reset(self) -> Observation:
        self.close()
        generate_db(self.task_id, self.db_path)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.is_done = False
        
        obs = Observation(
            last_query=None,
            query_result=None,
            query_error=None,
            schema_info=self._get_schema()
        )
        self.last_observation = obs
        return obs

    def state(self) -> Observation:
        return self.last_observation

    def step(self, action: Action) -> Tuple[Observation, float, bool, dict]:
        if self.is_done:
            return self.last_observation, 0.0, True, {"error": "Episode already done"}
            
        reward_score = 0.0
        
        if action.action_type == "execute_sql":
            if not action.query:
                obs = self.last_observation.copy()
                obs.query_error = "No SQL query provided."
                return obs, 0.0, False, {}

            c = self.conn.cursor()
            query_result = None
            query_error = None
            try:
                c.execute(action.query)
                self.conn.commit()
                if action.query.strip().upper().startswith("SELECT") or action.query.strip().upper().startswith("PRAGMA"):
                    rows = c.fetchall()
                    query_result = [dict(row) for row in rows][:50]
                else:
                    # Give small partial reward for successful modifications
                    reward_score = 0.1
                
                obs = Observation(
                    last_query=action.query,
                    query_result=query_result,
                    query_error=None,
                    schema_info=self._get_schema()
                )
            except Exception as e:
                obs = Observation(
                    last_query=action.query,
                    query_result=None,
                    query_error=str(e),
                    schema_info=self._get_schema()
                )
                
            self.last_observation = obs
            return obs, reward_score, False, {}
            
        elif action.action_type == "submit_task":
            # Grade it
            final_score = self._grade()
            self.is_done = True
            return self.last_observation, final_score, True, {"message": "Task submitted"}
            
        else:
            return self.last_observation, 0.0, False, {"error": "Unknown action"}

    def _grade(self) -> float:
        c = self.conn.cursor()
        grade = 0.0
        if self.task_id == "easy":
            try:
                c.execute("SELECT email, phone FROM users")
                rows = c.fetchall()
                if not rows: return 0.0
                all_good = True
                for r in rows:
                    email, phone = r["email"], r["phone"]
                    if email != email.lower(): all_good = False
                    if not phone.replace("-", "").isdigit() or "-" in phone: all_good = False
                if all_good: grade = 1.0
            except Exception:
                pass
                
        elif self.task_id == "medium":
            try:
                c.execute("PRAGMA table_info(orders)")
                columns = [row["name"] for row in c.fetchall()]
                if "metadata" not in columns and "payment_method" in columns and "shipping" in columns:
                    c.execute("SELECT payment_method, shipping FROM orders")
                    rows = c.fetchall()
                    if rows[0]["payment_method"] == "credit" and rows[0]["shipping"] == "fast" and \
                       rows[1]["payment_method"] == "paypal" and rows[1]["shipping"] == "slow":
                        grade = 1.0
            except Exception:
                pass
                
        elif self.task_id == "hard":
            try:
                # Check if purchases is dropped
                c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='purchases'")
                if not c.fetchone():
                    # Check customers
                    c.execute("SELECT * FROM customers")
                    customers = c.fetchall()
                    if len(customers) == 2:
                        # Check orders
                        c.execute("SELECT * FROM orders")
                        orders = c.fetchall()
                        if len(orders) == 3:
                            grade = 1.0
            except Exception:
                pass
        
        return grade

# Standard entry point if tested as openenv python file
def make_env(task_id: str = "easy", **kwargs):
    return DataCustodianEnv(task_id=task_id)
