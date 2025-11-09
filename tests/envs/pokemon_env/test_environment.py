# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""
Tests for Pokemon Battle Environment (direct environment testing).

These tests run against the environment directly without HTTP,
requiring a Pokemon Showdown server on localhost:8000.

Prerequisites:
    1. Pokemon Showdown server running on localhost:8000
       - Clone: git clone https://github.com/smogon/pokemon-showdown.git
       - Install: cd pokemon-showdown && npm install
       - Configure: cp config/config-example.js config/config.js
       - Run: node pokemon-showdown start --no-security
    
    2. poke-env installed:
       - pip install poke-env
"""

import logging
import pytest

from envs.pokemon_env.models import PokemonAction
from envs.pokemon_env.server.pokemon_environment import PokemonEnvironment

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@pytest.fixture
def pokemon_env():
    """Create a Pokemon environment for testing."""
    env = PokemonEnvironment(battle_format="gen8randombattle")
    yield env
    env.close()


@pytest.fixture
def pokemon_env_dense():
    """Create a Pokemon environment with dense rewards."""
    env = PokemonEnvironment(
        battle_format="gen8randombattle",
        reward_mode="dense"
    )
    yield env
    env.close()


def test_environment_creation():
    """Test that we can create a Pokemon environment."""
    env = PokemonEnvironment(battle_format="gen8randombattle")
    
    assert env is not None
    assert env.player_username is not None
    assert env.battle_format == "gen8randombattle"
    assert env.reward_mode == "sparse"
    
    env.close()


def test_reset(pokemon_env):
    """Test that reset() returns a valid initial observation."""
    obs = pokemon_env.reset()
    
    assert obs is not None
    assert pokemon_env.state.episode_id is not None
    assert pokemon_env.state.battle_id is not None
    assert obs.turn >= 0
    
    # Should have an active pokemon
    assert obs.active_pokemon is not None
    assert obs.active_pokemon.species is not None
    assert 0 <= obs.active_pokemon.hp_percent <= 1.0
    
    # Should have opponent
    assert obs.opponent_active_pokemon is not None
    
    # Should have legal actions
    assert len(obs.available_moves) > 0 or len(obs.available_switches) > 0
    assert len(obs.legal_actions) > 0


def test_single_step(pokemon_env):
    """Test that step() executes an action and updates state."""
    obs = pokemon_env.reset()
    
    # Take a move action
    action = PokemonAction(action_type="move", action_index=0)
    obs = pokemon_env.step(action)
    
    assert obs is not None
    assert obs.turn >= 1
    assert obs.reward is not None
    assert isinstance(obs.done, bool)
    
    if obs.active_pokemon:
        assert obs.active_pokemon.species is not None


def test_full_battle(pokemon_env):
    """Test that we can complete a full battle."""
    obs = pokemon_env.reset()
    
    max_turns = 100
    turn = 0
    
    while not obs.done and turn < max_turns:
        turn += 1
        
        # Choose a legal action
        if obs.available_moves:
            action = PokemonAction(action_type="move", action_index=0)
        elif obs.available_switches:
            action = PokemonAction(action_type="switch", action_index=0)
        else:
            pytest.fail("No legal actions available")
        
        obs = pokemon_env.step(action)
    
    # Battle should end within max turns
    assert turn < max_turns or obs.done
    
    if obs.done:
        assert pokemon_env.state.is_battle_finished
        assert pokemon_env.state.battle_winner is not None


def test_illegal_move(pokemon_env):
    """Test that illegal moves are handled gracefully."""
    obs = pokemon_env.reset()
    
    # Try an out-of-bounds move
    action = PokemonAction(action_type="move", action_index=99)
    
    # Should not raise an exception
    obs = pokemon_env.step(action)
    
    assert obs is not None
    assert obs.turn >= 1
    
    # Should have error in metadata
    if "last_error" in obs.metadata:
        assert obs.metadata["last_error"] is not None
        assert obs.metadata.get("illegal_action_count", 0) > 0


def test_dense_rewards(pokemon_env_dense):
    """Test that dense reward mode works."""
    obs = pokemon_env_dense.reset()
    
    rewards = []
    
    for i in range(5):
        if obs.done:
            break
        
        action = PokemonAction(action_type="move", action_index=0)
        obs = pokemon_env_dense.step(action)
        rewards.append(obs.reward)
    
    # Dense rewards should sometimes be non-zero during battle
    # (though not guaranteed in just 5 steps)
    assert len(rewards) > 0
    assert all(isinstance(r, (int, float)) for r in rewards)
