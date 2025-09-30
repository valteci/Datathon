# src/logging_mlflow.py
import os
import time
import requests
import statistics as _st
from typing import Sequence, Optional, List, Dict, Any

class Log:
    def __init__(self,
                 mlflow_url: Optional[str] = None,
                 experiment_name: str = "decision-stats",
                 max_sim_metrics: int = 200):
        self.mlflow = (mlflow_url or os.getenv("MLFLOW_URL", "http://mlflow:5001")).rstrip("/")
        self.model = os.getenv("MODEL", "unknown-model")
        self.exp_name = experiment_name
        self.max_sim_metrics = int(max_sim_metrics)
        self.exp_id = self._ensure_experiment(self.exp_name)

    # ---------- REST helpers ----------
    def _ensure_experiment(self, name: str) -> str:
        r = requests.get(
            f"{self.mlflow}/api/2.0/mlflow/experiments/get-by-name",
            params={"experiment_name": name},
            timeout=10,
        )
        if r.ok and r.json().get("experiment"):
            return r.json()["experiment"]["experiment_id"]
        r = requests.post(
            f"{self.mlflow}/api/2.0/mlflow/experiments/create",
            json={"name": name},
            timeout=10,
        )
        r.raise_for_status()
        return r.json()["experiment_id"]


    def _create_run(self, run_name: Optional[str] = None) -> str:
        payload: Dict[str, Any] = {"experiment_id": self.exp_id}
        if run_name:
            payload["run_name"] = run_name
        r = requests.post(
            f"{self.mlflow}/api/2.0/mlflow/runs/create",
            json=payload,
            timeout=10,
        )
        r.raise_for_status()
        j = r.json()
        return (j.get("run", {}) or {}).get("info", {}).get("run_id") or j.get("run_id")


    def _log_batch(self, run_id: str,
                   metrics: Optional[List[Dict[str, Any]]] = None,
                   params: Optional[List[Dict[str, str]]] = None,
                   tags: Optional[List[Dict[str, str]]] = None) -> None:
        payload = {"run_id": run_id,
                   "metrics": metrics or [],
                   "params": params or [],
                   "tags": tags or []}
        r = requests.post(
            f"{self.mlflow}/api/2.0/mlflow/runs/log-batch",
            json=payload,
            timeout=10,
        )
        r.raise_for_status()


    # ---------- API pública para log ----------
    def log(self,
            duration_ms: float,
            similarities: Sequence[float],
            k: int,
            run_name: Optional[str] = None) -> str:
        run_id = self._create_run(run_name or f"infer-{int(time.time())}")
        ts = int(time.time() * 1000)

        sims = [float(x) for x in (similarities or [])]
        n = len(sims)
        metrics: List[Dict[str, Any]] = [
            {"key": "duration_ms", "value": float(duration_ms), "timestamp": ts, "step": 0}
        ]

        if n:
            sim_mean = sum(sims) / n
            sim_min, sim_max = min(sims), max(sims)
            sim_std = _st.pstdev(sims) if n > 1 else 0.0
            metrics += [
                {"key": "sim_mean", "value": float(sim_mean), "timestamp": ts, "step": 0},
                {"key": "sim_min",  "value": float(sim_min),  "timestamp": ts, "step": 0},
                {"key": "sim_max",  "value": float(sim_max),  "timestamp": ts, "step": 0},
                {"key": "sim_std",  "value": float(sim_std),  "timestamp": ts, "step": 0},
            ]
            capped = sims[: self.max_sim_metrics]
            for idx, val in enumerate(capped):
                metrics.append({"key": "sim", "value": float(val), "timestamp": ts, "step": idx})

        params = [
            {"key": "model", "value": str(self.model)},
            {"key": "k", "value": str(int(k))},
            {"key": "n_sims", "value": str(n)},
        ]
        tags = [{"key": "source", "value": "python-rest"}]
        if n > self.max_sim_metrics:
            tags.append({"key": "sim_truncated",
                         "value": f"1|logged={self.max_sim_metrics}|total={n}"})

        self._log_batch(run_id, metrics=metrics, params=params, tags=tags)
        return run_id


    def now_ms(self) -> int:
        return int(time.time() * 1000)


    def timed(self) -> float:
        return time.time() * 1000.0


    # ---------- NOVO: exportar "todos os dados" em JSON ----------
    @staticmethod
    def fetch_all(mlflow_url: Optional[str] = None,
                  include_history: bool = True,
                  cap_history: int = 1000) -> Dict[str, Any]:
        """
        Consolida tudo do MLflow em JSON:
          - experiments
          - runs (com info)
          - params, tags
          - metrics_latest (últimos valores)
          - metrics_history (histórico completo por métrica, limitado por cap_history)
        Lê MLFLOW_URL do ambiente se mlflow_url não for passado.
        """
        mlflow = (mlflow_url or os.getenv("MLFLOW_URL", "http://mlflow:5001")).rstrip("/")

        def search_experiments() -> List[Dict[str, Any]]:
            items, token = [], None
            while True:
                body = {"max_results": 1000}
                if token:
                    body["page_token"] = token
                r = requests.post(f"{mlflow}/api/2.0/mlflow/experiments/search",
                                json=body, timeout=15)
                r.raise_for_status()
                j = r.json()
                items.extend(j.get("experiments", []) or [])
                token = j.get("next_page_token")
                if not token:
                    break
            return items


        def search_runs(exp_ids: List[str]) -> List[Dict[str, Any]]:
            items, token = [], None
            base = {
                "experiment_ids": exp_ids,
                "max_results": 1000,
                "order_by": ["attributes.start_time DESC"],
            }
            while True:
                body = dict(base)
                if token:
                    body["page_token"] = token
                r = requests.post(f"{mlflow}/api/2.0/mlflow/runs/search",
                                  json=body, timeout=30)
                r.raise_for_status()
                j = r.json()
                items.extend(j.get("runs", []) or [])
                token = j.get("next_page_token")
                if not token:
                    break
            return items


        def get_metric_history(run_id: str, key: str) -> List[Dict[str, Any]]:
            pts, token = [], None
            while True:
                params = {"run_id": run_id, "metric_key": key}
                if token:
                    params["page_token"] = token
                r = requests.get(f"{mlflow}/api/2.0/mlflow/metrics/get-history",
                                 params=params, timeout=30)
                if not r.ok:
                    break
                j = r.json()
                batch = j.get("metrics", []) or []
                for m in batch:
                    pts.append({
                        "timestamp": m.get("timestamp"),
                        "step": m.get("step"),
                        "value": m.get("value"),
                    })
                    if len(pts) >= cap_history:
                        return pts
                token = j.get("next_page_token")
                if not token:
                    break
            return pts

        out: Dict[str, Any] = {"mlflow_url": mlflow, "experiments": []}
        experiments = search_experiments()

        for e in experiments:
            eid = e.get("experiment_id")
            exp_obj = {
                "experiment_id": eid,
                "name": e.get("name"),
                "lifecycle_stage": e.get("lifecycle_stage"),
                "artifact_location": e.get("artifact_location"),
                "runs": [],
            }
            for r in search_runs([eid]):
                info = r.get("info", {}) or {}
                data = r.get("data", {}) or {}
                latest_metrics = {m["key"]: m["value"] for m in data.get("metrics", [])}
                params = {p["key"]: p["value"] for p in data.get("params", [])}
                tags = {t["key"]: t["value"] for t in data.get("tags", [])}

                run_id = info.get("run_id") or r.get("run_id")
                run_obj: Dict[str, Any] = {
                    "run_id": run_id,
                    "run_name": info.get("run_name"),
                    "status": info.get("status"),
                    "start_time": info.get("start_time"),
                    "end_time": info.get("end_time"),
                    "artifact_uri": info.get("artifact_uri"),
                    "metrics_latest": latest_metrics,
                    "params": params,
                    "tags": tags,
                }

                if include_history and latest_metrics:
                    hist: Dict[str, List[Dict[str, Any]]] = {}
                    for k in latest_metrics.keys():
                        hist[k] = get_metric_history(run_id, k)
                    run_obj["metrics_history"] = hist

                exp_obj["runs"].append(run_obj)

            out["experiments"].append(exp_obj)

        return out






