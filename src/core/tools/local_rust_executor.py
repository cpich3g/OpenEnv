"""Local Rust Executor utilities."""

from __future__ import annotations

import subprocess
import textwrap
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Optional

from core.env_server.types import CodeExecResult


class RustExecutor:
    """Compile and execute Rust snippets with configurable limits.

    The executor writes code to a temporary crate, compiles it with ``rustc``,
    and runs the produced binary, returning captured stdout/stderr alongside an
    exit code. Snippets lacking an explicit ``fn main`` are wrapped so users can
    provide just a body of statements.

    Args:
        edition: Rust edition passed to ``rustc --edition``.
        compile_timeout: Seconds allowed for ``rustc``.
        run_timeout: Seconds allowed for the compiled binary.

    Example:
        >>> executor = RustExecutor()
        >>> result = executor.run("println!(\"Hello\");")
        >>> result.stdout
        'Hello\n'
    """

    def __init__(self, *, edition: str = "2021", compile_timeout: int = 10, run_timeout: int = 10) -> None:
        self._edition = edition
        self._compile_timeout = compile_timeout
        self._run_timeout = run_timeout

    def run(self, code: str) -> CodeExecResult:
        """Compile and execute the provided Rust code."""
        with TemporaryDirectory(prefix="openenv-rust-") as tmp_dir:
            tmp_path = Path(tmp_dir)
            source_path = tmp_path / "main.rs"
            binary_path = tmp_path / "program"

            prepared_code = self._wrap_if_needed(code)
            source_path.write_text(prepared_code, encoding="utf-8")

            compile_proc = self._run_compile(source_path, binary_path)
            if compile_proc.returncode != 0:
                return CodeExecResult(
                    stdout=compile_proc.stdout,
                    stderr=compile_proc.stderr,
                    exit_code=compile_proc.returncode,
                )

            run_proc = self._run_binary(binary_path)
            return CodeExecResult(
                stdout=run_proc.stdout,
                stderr=self._merge_stderr(compile_proc.stderr, run_proc.stderr),
                exit_code=run_proc.returncode,
            )

    def _wrap_if_needed(self, code: str) -> str:
        stripped = code.strip()
        if "fn main" in stripped:
            return stripped + ("\n" if not stripped.endswith("\n") else "")
        indented = textwrap.indent(stripped, "    ") if stripped else ""
        return "fn main() {\n" + indented + ("\n" if indented else "") + "}\n"

    def _run_compile(self, source_path: Path, binary_path: Path) -> subprocess.CompletedProcess[str]:
        try:
            return subprocess.run(
                [
                    "rustc",
                    str(source_path),
                    "--edition",
                    self._edition,
                    "-o",
                    str(binary_path),
                ],
                check=False,
                text=True,
                capture_output=True,
                timeout=self._compile_timeout,
            )
        except subprocess.TimeoutExpired as exc:
            return subprocess.CompletedProcess(
                args=exc.cmd,
                returncode=1,
                stdout="",
                stderr=f"rustc timed out after {self._compile_timeout}s",
            )

    def _run_binary(self, binary_path: Path) -> subprocess.CompletedProcess[str]:
        try:
            return subprocess.run(
                [str(binary_path)],
                check=False,
                text=True,
                capture_output=True,
                timeout=self._run_timeout,
            )
        except subprocess.TimeoutExpired as exc:
            return subprocess.CompletedProcess(
                args=exc.cmd,
                returncode=1,
                stdout="",
                stderr=f"binary execution timed out after {self._run_timeout}s",
            )

    @staticmethod
    def _merge_stderr(compile_stderr: str, run_stderr: str) -> str:
        if compile_stderr and run_stderr:
            return f"{compile_stderr}\n{run_stderr}"
        return compile_stderr or run_stderr
