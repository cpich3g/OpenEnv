# Rust Coding Environment

Execute and evaluate Rust code snippets through the OpenEnv HTTP interface. This
environment mirrors the Julia coding environment by splitting the payload into
core library code and optional tests, compiling everything with `rustc`, and
reporting rich execution feedback.

## Features

- 🔧 Compile Rust functions and modules in isolation.
- ✅ Run unit tests provided with the action payload via `rustc --test`.
- 📊 Rewards favour compiling code, passing tests, and writing concise snippets.
- 🛡️ Safety and quality transforms penalise dangerous APIs such as
  `std::process::Command` or `unsafe` blocks.

## Client Usage

```python
from envs.rust_coding_env import RustAction, RustCodingEnv

client = RustCodingEnv.from_docker_image("rust-coding-env:latest")

result = client.reset()
print(result.observation.code_compiles)

action = RustAction(
    core_code="""
pub fn add(a: i32, b: i32) -> i32 {
    a + b
}
""",
    test_code="""
#[test]
fn adds_numbers() {
    assert_eq!(add(2, 3), 5);
}
""",
)

result = client.step(action)
print(result.observation.stdout)
print(result.observation.tests_passed)
print(result.reward)

state = client.state()
print(state.total_tests_passed)

client.close()
```

## Server Quick Start

```bash
# Build the Docker image
docker build -f src/envs/rust_coding_env/server/Dockerfile -t rust-coding-env:latest .

# Run the environment locally
docker run --rm -p 8000:8000 rust-coding-env:latest
```

The FastAPI application listens on port `8000` and exposes the standard
`/reset`, `/step`, `/state`, and `/health` endpoints with the OpenEnv web
interface enabled.

## API Reference

### RustAction

| Field      | Type | Description                      |
|------------|------|----------------------------------|
| core_code  | str  | Rust source to compile and reuse |
| test_code  | str  | Optional tests executed with the payload |

### RustObservation

- `stdout`: Combined stdout from compilation and test execution.
- `stderr`: Combined stderr from compilation and test execution.
- `exit_code`: Exit status from the final stage (tests if provided, otherwise compilation run).
- `tests_passed` / `tests_failed`: Counts derived from `rustc --test` output.
- `code_compiles`: Boolean indicating whether the core code compiled successfully.

### RustState

Tracks the latest exit code, whether the previous compilation succeeded, and
aggregated test results across the current episode.

## Reward Signal

1. `-3` if the core code fails to compile.
2. Otherwise start from `+1` and add `+3` per passed test, `-1` per failed test.
3. Receive an additional `+2` bonus when all provided tests pass.

Transforms may further adjust the final reward to encourage safe and concise
solutions.

## Safety Notes

The server relies on the OpenEnv base container plus the official Rust toolchain
installed via `rustup`. Dangerous operations—such as spawning child processes,
unsafe code, or filesystem deletion—are penalised via heuristic transforms.
