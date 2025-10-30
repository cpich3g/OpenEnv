"""FastAPI app for the Rust coding environment."""

from core.env_server import create_app

from ..models import RustAction, RustObservation
from .rust_codeact_env import RustCodeActEnv

env = RustCodeActEnv()
app = create_app(env, RustAction, RustObservation, env_name="rust_coding_env")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
