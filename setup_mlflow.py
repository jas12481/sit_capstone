"""
MLflow Setup Script — AIA Capstone Project
Run this once to verify Databricks connection and create the experiment.
Usage: python3 setup_mlflow.py
"""

import mlflow
import os
from dotenv import load_dotenv

load_dotenv("mcp_server/.env")

DATABRICKS_HOST = os.getenv("DATABRICKS_HOST")
DATABRICKS_TOKEN = os.getenv("DATABRICKS_TOKEN")

if not DATABRICKS_HOST or not DATABRICKS_TOKEN:
    print("ERROR: DATABRICKS_HOST or DATABRICKS_TOKEN not set in mcp_server/.env")
    exit(1)

os.environ["DATABRICKS_HOST"] = DATABRICKS_HOST
os.environ["DATABRICKS_TOKEN"] = DATABRICKS_TOKEN

# ── CONNECT ───────────────────────────────────────────────────────────────────

mlflow.set_tracking_uri("databricks")
print(f"Tracking URI: {mlflow.get_tracking_uri()}")
print(f"Databricks host: {DATABRICKS_HOST}")

# ── CREATE EXPERIMENT ─────────────────────────────────────────────────────────

EXPERIMENT_NAME = "/Claims_Assessment_Prompting_Study"

# ── GET ACTUAL USERNAME FROM DATABRICKS ───────────────────────────────────────

try:
    from databricks.sdk import WorkspaceClient
    w = WorkspaceClient(host=DATABRICKS_HOST, token=DATABRICKS_TOKEN)
    me = w.current_user.me()
    username = me.user_name
    EXPERIMENT_NAME = f"/Users/{username}/Claims_Assessment_Prompting_Study"
    print(f"Databricks username: {username}")
    print(f"Experiment path: {EXPERIMENT_NAME}")
except Exception as e:
    print(f"Could not fetch username: {e}")
    print("Using root path instead")

try:
    experiment_id = mlflow.create_experiment(EXPERIMENT_NAME)
    print(f"\nCreated experiment: {EXPERIMENT_NAME}")
    print(f"Experiment ID: {experiment_id}")
except Exception as e:
    print(f"\nCreate experiment error: {e}")
    try:
        experiment = mlflow.get_experiment_by_name(EXPERIMENT_NAME)
        if experiment:
            print(f"Experiment already exists: {EXPERIMENT_NAME}")
            print(f"Experiment ID: {experiment.experiment_id}")
        else:
            print("Experiment not found either — check Databricks credentials")
            exit(1)
    except Exception as e2:
        print(f"Get experiment error: {e2}")
        exit(1)

# ── LOG TEST RUN ──────────────────────────────────────────────────────────────

mlflow.set_experiment(EXPERIMENT_NAME)

with mlflow.start_run(run_name="setup_test"):
    mlflow.log_param("project", "AIA_Capstone_2302990")
    mlflow.log_param("student", "Jasbir_Kaur")
    mlflow.log_param("test", "connection_check")
    mlflow.log_metric("test_metric", 1.0)
    run_id = mlflow.active_run().info.run_id
    print(f"\nTest run logged successfully")
    print(f"Run ID: {run_id}")

print("\nMLflow + Databricks connection verified.")
print(f"View your experiment at: {DATABRICKS_HOST}#mlflow/experiments")