# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""
FastAPI application for the Pokemon Battle Environment.

This module creates an HTTP server that exposes Pokemon battles
over HTTP endpoints, making them compatible with HTTPEnvClient.

Usage:
    # Development (with auto-reload):
    uvicorn envs.pokemon_env.server.app:app --reload --host 0.0.0.0 --port 9980

    # Production:
    uvicorn envs.pokemon_env.server.app:app --host 0.0.0.0 --port 9980 --workers 4

    # Or run directly:
    python -m envs.pokemon_env.server.app

Environment variables:
    POKEMON_BATTLE_FORMAT: Battle format (default: "gen8randombattle")
    POKEMON_PLAYER_USERNAME: Player username (default: "player")
    POKEMON_REWARD_MODE: Reward mode - "sparse" or "dense" (default: "sparse")
    POKEMON_MAX_TURNS: Maximum turns per battle (default: "1000")
    
    Reward coefficients (dense mode only):
    POKEMON_FAINT_OPPONENT_BONUS: Reward for opponent faint (default: "0.2")
    POKEMON_FAINT_SELF_PENALTY: Penalty for own faint (default: "0.2")
    POKEMON_HP_DAMAGE_COEF: HP damage coefficient (default: "0.05")
    POKEMON_STATUS_INFLICT_BONUS: Status effect bonus (default: "0.1")
    POKEMON_STATUS_REMOVE_BONUS: Status removal bonus (default: "0.1")
    POKEMON_STAT_BOOST_BONUS: Stat boost bonus (default: "0.05")
    POKEMON_BUFF_REMOVE_BONUS: Buff removal bonus (default: "0.05")
    POKEMON_HP_RECOVERY_BONUS: HP recovery bonus (default: "0.05")
    POKEMON_FINAL_WIN_BONUS: Final win bonus (default: "10.0")
    POKEMON_FINAL_LOSS_PENALTY: Final loss penalty (default: "10.0")
"""

import os

from core.env_server import create_app

from ..models import PokemonAction, PokemonObservation, RewardConfig
from .pokemon_environment import PokemonEnvironment

import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

battle_format = os.getenv("POKEMON_BATTLE_FORMAT", "gen8randombattle")
player_username = os.getenv("POKEMON_PLAYER_USERNAME", "player")
reward_mode = os.getenv("POKEMON_REWARD_MODE", "sparse")
max_turns = int(os.getenv("POKEMON_MAX_TURNS", "1000"))

# Parse reward config from environment variables
reward_config = RewardConfig(
    faint_opponent_bonus=float(os.getenv("POKEMON_FAINT_OPPONENT_BONUS", "0.2")),
    faint_self_penalty=float(os.getenv("POKEMON_FAINT_SELF_PENALTY", "0.2")),
    hp_damage_coefficient=float(os.getenv("POKEMON_HP_DAMAGE_COEF", "0.05")),
    status_inflict_bonus=float(os.getenv("POKEMON_STATUS_INFLICT_BONUS", "0.1")),
    status_remove_bonus=float(os.getenv("POKEMON_STATUS_REMOVE_BONUS", "0.1")),
    stat_boost_bonus=float(os.getenv("POKEMON_STAT_BOOST_BONUS", "0.05")),
    buff_remove_bonus=float(os.getenv("POKEMON_BUFF_REMOVE_BONUS", "0.05")),
    hp_recovery_bonus=float(os.getenv("POKEMON_HP_RECOVERY_BONUS", "0.05")),
    final_win_bonus=float(os.getenv("POKEMON_FINAL_WIN_BONUS", "10.0")),
    final_loss_penalty=float(os.getenv("POKEMON_FINAL_LOSS_PENALTY", "10.0")),
)

env = PokemonEnvironment(
    battle_format=battle_format,
    player_username=player_username,
    reward_mode=reward_mode,
    reward_config=reward_config,
    max_turns=max_turns,
)

app = create_app(env, PokemonAction, PokemonObservation, env_name="pokemon_env")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=9980)
