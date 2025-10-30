"""Safety and quality transforms for the Rust coding environment."""

from __future__ import annotations

import re

from core.env_server.base_transforms import CompositeTransform
from core.env_server.interfaces import Transform

from ..models import RustObservation


class RustSafetyTransform(Transform):
    """Penalise potentially dangerous Rust APIs."""

    def __init__(self, penalty: float = -3.0) -> None:
        self.penalty = penalty
        self.dangerous_patterns = [
            r"std::process::Command",
            r"Command::new",
            r"unsafe\s*\{",
            r"std::fs::remove_",
            r"std::net::",
        ]

    def __call__(self, observation: RustObservation):  # type: ignore[override]
        if not isinstance(observation, RustObservation):
            return observation

        metadata = observation.metadata or {}
        code = metadata.get("last_code", "")

        for pattern in self.dangerous_patterns:
            if re.search(pattern, code):
                observation.reward = (observation.reward or 0.0) + self.penalty
                metadata["safety_violation"] = pattern
                observation.metadata = metadata
                return observation

        observation.reward = observation.reward or 0.0
        return observation


class RustQualityTransform(Transform):
    """Encourage concise code and presence of tests."""

    def __init__(self, concise_bonus: float = 0.5, test_bonus: float = 1.0, max_length: int = 250) -> None:
        self.concise_bonus = concise_bonus
        self.test_bonus = test_bonus
        self.max_length = max_length

    def __call__(self, observation: RustObservation):  # type: ignore[override]
        if not isinstance(observation, RustObservation):
            return observation

        metadata = observation.metadata or {}
        code = metadata.get("last_code", "")
        reward = observation.reward or 0.0

        if code and len(code.strip()) <= self.max_length:
            reward += self.concise_bonus
        if "#[test]" in code:
            reward += self.test_bonus

        observation.reward = reward
        observation.metadata = metadata
        return observation


def create_safe_rust_transform() -> CompositeTransform:
    """Create the default transform pipeline for Rust coding env."""

    return CompositeTransform([RustSafetyTransform(), RustQualityTransform()])
