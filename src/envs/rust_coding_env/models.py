"""Dataclasses for the Rust coding environment."""

from __future__ import annotations

from dataclasses import dataclass

from core.env_server.types import Action, Observation, State


@dataclass(kw_only=True)
class RustAction(Action):
    """Action containing Rust code to compile and test."""

    core_code: str
    test_code: str = ""


@dataclass(kw_only=True)
class RustObservation(Observation):
    """Result of compiling and executing Rust code."""

    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0
    tests_passed: int = 0
    tests_failed: int = 0
    code_compiles: bool = False


@dataclass
class RustState(State):
    """Environment state tracking episode metadata for Rust execution."""

    last_exit_code: int = 0
    last_code_compiles: bool = False
    total_tests_passed: int = 0
    total_tests_failed: int = 0
