from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

import mlflow
from dotenv import load_dotenv


@dataclass
class MLflowTrackerConfig:
    env_file: str = "mcp_server/.env"
    tracking_uri: str = "databricks"
    experiment_basename: str = "Claims_Assessment_Prompting_Study"
    app_name: str = "AIA_Capstone_2302990"
    strict: bool = False  # if True, raise on logging failures


@dataclass
class AssessmentRunPayload:
    # Core run identity
    run_name: str
    workflow_type: str
    model_name: str = "gpt-5.2"
    prompt_version: Optional[str] = None

    # Business/context params
    claim_id: Optional[str] = None
    policy_id: Optional[str] = None
    recommendation: Optional[str] = None
    confidence_level: Optional[str] = None
    coverage_conclusion: Optional[str] = None

    # Rule summary metrics
    mandatory_rules_failed: Optional[int] = None
    total_rules_passed: Optional[int] = None

    # Judge metrics
    judge_completeness_score: Optional[float] = None
    judge_consistency_score: Optional[float] = None
    judge_hallucination_risk_score: Optional[float] = None
    judge_clarity_score: Optional[float] = None
    judge_overall_score: Optional[float] = None

    # Optional extras
    tags: Dict[str, str] = field(default_factory=dict)
    params: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, float] = field(default_factory=dict)
    artifacts: Dict[str, Any] = field(default_factory=dict)  # name -> dict/list/str


class MLflowTracker:
    def __init__(self, config: Optional[MLflowTrackerConfig] = None):
        self.config = config or MLflowTrackerConfig()
        self._ready = False
        self._experiment_name: Optional[str] = None

    def initialize(self) -> None:
        """Load env, set Databricks auth env vars, set tracking URI, ensure experiment."""
        load_dotenv(self.config.env_file)

        host = os.getenv("DATABRICKS_HOST")
        token = os.getenv("DATABRICKS_TOKEN")

        if not host or not token:
            msg = "DATABRICKS_HOST / DATABRICKS_TOKEN missing."
            if self.config.strict:
                raise RuntimeError(msg)
            print(f"[MLflowTracker] {msg} Logging disabled.")
            self._ready = False
            return

        os.environ["DATABRICKS_HOST"] = host
        os.environ["DATABRICKS_TOKEN"] = token

        mlflow.set_tracking_uri(self.config.tracking_uri)

        self._experiment_name = self._resolve_experiment_name()
        self._ensure_experiment(self._experiment_name)
        mlflow.set_experiment(self._experiment_name)

        self._ready = True

    def _resolve_experiment_name(self) -> str:
        """Use /Users/<email>/<experiment> if possible, fallback to root path."""
        fallback = f"/{self.config.experiment_basename}"
        try:
            from databricks.sdk import WorkspaceClient  # optional dependency
            host = os.getenv("DATABRICKS_HOST")
            token = os.getenv("DATABRICKS_TOKEN")
            ws = WorkspaceClient(host=host, token=token)
            me = ws.current_user.me()
            return f"/Users/{me.user_name}/{self.config.experiment_basename}"
        except Exception:
            return fallback

    def _ensure_experiment(self, experiment_name: str) -> None:
        try:
            mlflow.create_experiment(experiment_name)
        except Exception:
            # already exists or parent path issue; try find existing
            exp = mlflow.get_experiment_by_name(experiment_name)
            if not exp and self.config.strict:
                raise RuntimeError(f"Unable to create/find experiment: {experiment_name}")

    def is_ready(self) -> bool:
        return self._ready

    def log_assessment_run(self, payload: AssessmentRunPayload) -> Optional[str]:
        """
        Log a production assessment run and return run_id.
        Returns None if not ready / failed and strict=False.
        """
        if not self._ready:
            if self.config.strict:
                raise RuntimeError("MLflowTracker not initialized.")
            return None

        try:
            with mlflow.start_run(run_name=payload.run_name):
                # Standard tags
                mlflow.set_tag("app", self.config.app_name)
                mlflow.set_tag("component", "mcp_assessment")
                mlflow.set_tag("workflow_type", payload.workflow_type)
                mlflow.set_tag("logged_at_utc", datetime.now(timezone.utc).isoformat())

                for k, v in payload.tags.items():
                    if v is not None:
                        mlflow.set_tag(k, str(v))

                # Standard params
                std_params = {
                    "workflow_type": payload.workflow_type,
                    "model_name": payload.model_name,
                    "prompt_version": payload.prompt_version,
                    "claim_id": payload.claim_id,
                    "policy_id": payload.policy_id,
                    "recommendation": payload.recommendation,
                    "confidence_level": payload.confidence_level,
                    "coverage_conclusion": payload.coverage_conclusion,
                }
                for k, v in std_params.items():
                    if v is not None:
                        mlflow.log_param(k, v)

                for k, v in payload.params.items():
                    if v is not None:
                        mlflow.log_param(k, v)

                # Standard metrics
                std_metrics = {
                    "mandatory_rules_failed": payload.mandatory_rules_failed,
                    "total_rules_passed": payload.total_rules_passed,
                    "judge_completeness_score": payload.judge_completeness_score,
                    "judge_consistency_score": payload.judge_consistency_score,
                    "judge_hallucination_risk_score": payload.judge_hallucination_risk_score,
                    "judge_clarity_score": payload.judge_clarity_score,
                    "judge_overall_score": payload.judge_overall_score,
                }
                for k, v in std_metrics.items():
                    if v is not None:
                        mlflow.log_metric(k, float(v))

                for k, v in payload.metrics.items():
                    if v is not None:
                        mlflow.log_metric(k, float(v))

                # Artifacts (dict/list auto-json; string plain text)
                for name, data in payload.artifacts.items():
                    self._log_inline_artifact(name, data)

                run_id = mlflow.active_run().info.run_id
                return run_id

        except Exception as e:
            if self.config.strict:
                raise
            print(f"[MLflowTracker] log_assessment_run failed: {e}")
            return None

    def log_evaluation_run(
        self,
        run_name: str,
        params: Dict[str, Any],
        metrics: Dict[str, float],
        artifacts: Optional[Dict[str, Any]] = None,
        tags: Optional[Dict[str, str]] = None,
    ) -> Optional[str]:
        """Generic logger for evaluation script (4 strategies x 20 claims)."""
        payload = AssessmentRunPayload(
            run_name=run_name,
            workflow_type=str(params.get("policy_type", "unknown")),
            model_name=str(params.get("model_name", "gpt-5.2")),
            prompt_version=params.get("prompt_version"),
            claim_id=params.get("claim_id"),
            tags=tags or {},
            params=params,
            metrics=metrics,
            artifacts=artifacts or {},
        )
        return self.log_assessment_run(payload)

    def _log_inline_artifact(self, name: str, data: Any) -> None:
        """
        Logs lightweight artifacts without forcing caller file I/O.
        """
        artifact_dir = Path(".mlflow_tmp_artifacts")
        artifact_dir.mkdir(parents=True, exist_ok=True)

        stem = name.replace("/", "_")
        if isinstance(data, (dict, list)):
            p = artifact_dir / f"{stem}.json"
            p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        else:
            p = artifact_dir / f"{stem}.txt"
            p.write_text(str(data), encoding="utf-8")

        mlflow.log_artifact(str(p))