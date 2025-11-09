# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""
Pokemon Battle Environment for OpenEnv.

This module provides OpenEnv integration for Pokemon battles via poke-env.

Example:
    >>> from envs.pokemon_env import PokemonEnv, PokemonAction
    >>>
    >>> # Connect to a running Pokemon Showdown server
    >>> env = PokemonEnv(battle_format="gen8randombattle")
    >>>
    >>> # Reset and interact
    >>> result = env.reset()
    >>> result = env.step(PokemonAction(action_type="move", action_index=0))
    >>> print(result.reward, result.done)
    >>>
    >>> # Cleanup
    >>> env.close()
"""

from .client import PokemonEnv
from .models import PokemonAction, PokemonObservation, PokemonState, PokemonData, RewardConfig

__all__ = ["PokemonEnv", "PokemonAction", "PokemonObservation", "PokemonState", "PokemonData", "RewardConfig"]
