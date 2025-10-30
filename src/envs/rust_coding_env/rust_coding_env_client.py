"""HTTP client for the Rust coding environment."""

from __future__ import annotations

from typing import Dict

from core.client_types import StepResult
from core.http_env_client import HTTPEnvClient

from .models import RustAction, RustObservation, RustState


class RustCodingEnv(HTTPEnvClient[RustAction, RustObservation]):
    """Client wrapper for interacting with the Rust coding environment server."""

    def _step_payload(self, action: RustAction) -> Dict[str, str]:
        return {
            "core_code": action.core_code,
            "test_code": action.test_code,
        }

    def _parse_result(self, payload: Dict) -> StepResult[RustObservation]:
        observation = RustObservation(**payload["observation"])
        return StepResult(
            observation=observation,
            reward=payload.get("reward"),
            done=bool(payload.get("done", False)),
        )

    def _parse_state(self, payload: Dict) -> RustState:
        return RustState(
            episode_id=payload.get("episode_id"),
            step_count=payload.get("step_count", 0),
            last_exit_code=payload.get("last_exit_code", 0),
            last_code_compiles=payload.get("last_code_compiles", False),
            total_tests_passed=payload.get("total_tests_passed", 0),
            total_tests_failed=payload.get("total_tests_failed", 0),
        )
