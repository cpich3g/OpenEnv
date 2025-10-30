# Docker image for the Rust coding environment

ARG BASE_IMAGE=openenv-base:latest
FROM ${BASE_IMAGE}

# Install prerequisites and Rust toolchain via rustup
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    pkg-config \
    libssl-dev \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --profile minimal --component rustfmt
ENV PATH="/root/.cargo/bin:${PATH}"

RUN rustc --version && cargo --version

# Python dependencies used by the core tooling
RUN pip install --no-cache-dir smolagents

# Copy framework and environment code
COPY src/core/ /app/src/core/
COPY src/envs/rust_coding_env/ /app/src/envs/rust_coding_env/

# Healthcheck for orchestrators
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Launch FastAPI server
CMD ["uvicorn", "envs.rust_coding_env.server.app:app", "--host", "0.0.0.0", "--port", "8000"]
