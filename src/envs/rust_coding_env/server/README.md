# Rust Coding Environment Server

This directory contains the server-side implementation of the Rust coding
environment. It wraps the `RustCodeActEnv` class in a FastAPI application and
packages everything into a Docker image that exposes the OpenEnv HTTP API.

## Structure

- `rust_codeact_env.py` – Implements the environment logic using the
  `RustExecutor` helper.
- `rust_transforms.py` – Safety and quality transforms applied to every
  observation.
- `app.py` – FastAPI entrypoint used by `uvicorn`.
- `Dockerfile` – Builds a container with the Rust toolchain installed via
  `rustup`.

## Local Development

```bash
# Run the server directly (requires rustup installed locally)
PYTHONPATH=src uvicorn envs.rust_coding_env.server.app:app --reload
```

## Docker Image

```bash
# Build
docker build -f src/envs/rust_coding_env/server/Dockerfile -t rust-coding-env:latest .

# Run interactively
docker run --rm -p 8000:8000 rust-coding-env:latest
```

The container is based on the OpenEnv base image and installs Rust via `rustup`
so the tests can compile with `rustc --test`.
