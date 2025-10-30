"""Rust code execution environment for OpenEnv."""

from __future__ import annotations

import re
import subprocess
import textwrap
import uuid
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Tuple

from core.env_server import Environment
from core.env_server.types import CodeExecResult
from core.tools import RustExecutor

from ..models import RustAction, RustObservation, RustState
from .rust_transforms import create_safe_rust_transform


class RustCodeActEnv(Environment):
    """Execute Rust code and optional tests while tracking episode state."""

    def __init__(self) -> None:
        self._executor = RustExecutor()
        self._state = RustState()
        self.transform = create_safe_rust_transform()

    def reset(self) -> RustObservation:
        self._executor = RustExecutor()
        self.transform = create_safe_rust_transform()
        self._state = RustState(episode_id=str(uuid.uuid4()), step_count=0)

        observation = RustObservation(
            stdout="",
            stderr="",
            exit_code=0,
            tests_passed=0,
            tests_failed=0,
            code_compiles=True,
            metadata={"core_code": "", "test_code": "", "last_code": ""},
        )
        return self._apply_transform(observation)

    def step(self, action: RustAction) -> RustObservation:
        if not isinstance(action, RustAction):
            raise ValueError(f"Expected RustAction, received {type(action)!r}")

        core_program = self._prepare_core_program(action.core_code)
        core_result = self._executor.run(core_program)
        code_compiles = core_result.exit_code == 0

        tests_passed = 0
        tests_failed = 0
        final_stdout = core_result.stdout
        final_stderr = core_result.stderr
        final_exit = core_result.exit_code

        if code_compiles and action.test_code.strip():
            test_result = self._run_tests(action.core_code, action.test_code)
            tests_passed, tests_failed = self._parse_test_summary(
                test_result.stdout, test_result.stderr
            )
            if test_result.exit_code != 0 and tests_failed == 0 and tests_passed == 0:
                tests_failed = 1
            final_stdout = test_result.stdout
            final_stderr = test_result.stderr
            final_exit = test_result.exit_code
        elif not code_compiles:
            tests_passed = 0
            tests_failed = 0

        reward = self._calculate_reward(code_compiles, tests_passed, tests_failed)

        self._state.step_count += 1
        self._state.last_exit_code = final_exit
        self._state.last_code_compiles = code_compiles
        self._state.total_tests_passed = tests_passed
        self._state.total_tests_failed = tests_failed

        combined_code = (action.core_code + "\n\n" + action.test_code).strip()
        metadata = {
            "core_code": action.core_code,
            "test_code": action.test_code,
            "last_code": combined_code,
        }

        observation = RustObservation(
            stdout=final_stdout,
            stderr=final_stderr,
            exit_code=final_exit,
            tests_passed=tests_passed,
            tests_failed=tests_failed,
            code_compiles=code_compiles,
            reward=reward,
            metadata=metadata,
        )

        return self._apply_transform(observation)

    @property
    def state(self) -> RustState:
        return self._state

    def _prepare_core_program(self, core_code: str) -> str:
        header = "#![allow(unused)]\n"
        body = core_code.rstrip()
        if "fn main" not in body:
            body = f"{body}\n\nfn main() {{}}\n" if body else "fn main() {}\n"
        else:
            body += "\n"
        return header + body

    def _run_tests(self, core_code: str, test_code: str) -> CodeExecResult:
        source = self._build_test_source(core_code, test_code)
        with TemporaryDirectory(prefix="openenv-rust-tests-") as tmp_dir:
            tmp_path = Path(tmp_dir)
            source_path = tmp_path / "lib.rs"
            binary_path = tmp_path / "rust_tests"
            source_path.write_text(source, encoding="utf-8")

            try:
                compile_proc = subprocess.run(
                    [
                        "rustc",
                        "--test",
                        str(source_path),
                        "--edition",
                        self._executor._edition,  # type: ignore[attr-defined]
                        "-o",
                        str(binary_path),
                    ],
                    check=False,
                    text=True,
                    capture_output=True,
                    timeout=self._executor._compile_timeout,  # type: ignore[attr-defined]
                )
            except subprocess.TimeoutExpired:
                return CodeExecResult(
                    stdout="",
                    stderr=f"rustc --test timed out after {self._executor._compile_timeout}s",  # type: ignore[attr-defined]
                    exit_code=1,
                )

            if compile_proc.returncode != 0:
                return CodeExecResult(
                    stdout=compile_proc.stdout,
                    stderr=compile_proc.stderr,
                    exit_code=compile_proc.returncode,
                )

            try:
                run_proc = subprocess.run(
                    [str(binary_path), "--nocapture"],
                    check=False,
                    text=True,
                    capture_output=True,
                    timeout=self._executor._run_timeout,  # type: ignore[attr-defined]
                )
            except subprocess.TimeoutExpired:
                return CodeExecResult(
                    stdout="",
                    stderr=f"test binary timed out after {self._executor._run_timeout}s",  # type: ignore[attr-defined]
                    exit_code=1,
                )

            return CodeExecResult(
                stdout=run_proc.stdout,
                stderr=self._merge_stderr(compile_proc.stderr, run_proc.stderr),
                exit_code=run_proc.returncode,
            )

    def _build_test_source(self, core_code: str, test_code: str) -> str:
        header = "#![allow(unused)]\n"
        core = core_code.rstrip()
        tests = test_code.strip()
        if not tests:
            return header + core + "\n"

        indented_tests = textwrap.indent(tests, "    ")
        module = (
            "\n#[cfg(test)]\n"
            "mod openenv_tests {\n"
            "    use super::*;\n"
            f"{indented_tests}\n"
            "}\n"
        )
        return header + core + module

    def _parse_test_summary(self, stdout: str, stderr: str) -> Tuple[int, int]:
        combined = f"{stdout}\n{stderr}"
        summary = re.search(
            r"test result:\s*(ok|FAILED)\.\s*(\d+)\s+passed;\s*(\d+)\s+failed",
            combined,
        )
        if summary:
            return int(summary.group(2)), int(summary.group(3))

        alt = re.search(r"(\d+)\s+passed;\s*(\d+)\s+failed", combined)
        if alt:
            return int(alt.group(1)), int(alt.group(2))

        return 0, 0

    def _calculate_reward(self, code_compiles: bool, tests_passed: int, tests_failed: int) -> int:
        if not code_compiles:
            return -3

        reward = 1 + (3 * tests_passed) - tests_failed
        if tests_passed > 0 and tests_failed == 0:
            reward += 2
        return reward

    @staticmethod
    def _merge_stderr(compile_stderr: str, run_stderr: str) -> str:
        if compile_stderr and run_stderr:
            return f"{compile_stderr}\n{run_stderr}"
        return compile_stderr or run_stderr
