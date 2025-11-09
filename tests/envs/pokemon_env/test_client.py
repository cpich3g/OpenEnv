# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""
Tests for Pokemon Battle Environment HTTP Client.

These tests run against the Pokemon environment via HTTP,
requiring both Pokemon Showdown and the OpenEnv HTTP server running.

Prerequisites:
    1. Pokemon environment server running on localhost:9980
       - Local: python -m envs.pokemon_env.server.app
       - Docker: docker run -p 8000:8000 -p 9980:9980 pokemon-env:latest
    
    2. Server accessible at http://localhost:9980

Note:
    These tests require the server to be running. You can configure the
    server URL via the POKEMON_SERVER_URL environment variable.
"""

import os
import pytest
import requests

from envs.pokemon_env.client import PokemonEnv
from envs.pokemon_env.models import PokemonAction


# Get server URL from environment or use default
BASE_URL = os.getenv("POKEMON_SERVER_URL", "http://localhost:9980")


@pytest.fixture(scope="module")
def check_server():
    """Check if the server is running before running tests."""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            pytest.skip(f"Server at {BASE_URL} not healthy")
    except requests.exceptions.RequestException:
        pytest.skip(f"Server at {BASE_URL} not accessible")


@pytest.fixture
def pokemon_client(check_server):
    """Create a Pokemon HTTP client for testing."""
    client = PokemonEnv(base_url=BASE_URL)
    return client


def test_health_check(check_server):
    """Test that the server health endpoint is working."""
    response = requests.get(f"{BASE_URL}/health", timeout=5)
    
    assert response.status_code == 200
    data = response.json()
    assert "status" in data


def test_client_creation():
    """Test that we can create an HTTP client."""
    client = PokemonEnv(base_url=BASE_URL)
    
    assert client is not None
    assert client.base_url == BASE_URL


def test_reset_via_http(pokemon_client):
    """Test that reset() works via HTTP."""
    result = pokemon_client.reset()
    
    assert result is not None
    assert result.observation is not None
    assert isinstance(result.done, bool)
    
    obs = result.observation
    assert obs.turn >= 0
    assert obs.active_pokemon is not None
    assert obs.opponent_active_pokemon is not None
    assert len(obs.available_moves) > 0 or len(obs.available_switches) > 0


def test_step_via_http(pokemon_client):
    """Test that step() works via HTTP."""
    result = pokemon_client.reset()
    
    # Take a move action
    action = PokemonAction(action_type="move", action_index=0)
    result = pokemon_client.step(action)
    
    assert result is not None
    assert result.observation is not None
    assert result.reward is not None
    assert isinstance(result.done, bool)
    
    obs = result.observation
    assert obs.turn >= 1


def test_full_battle_via_http(pokemon_client):
    """Test that we can complete a full battle via HTTP."""
    result = pokemon_client.reset()
    
    max_turns = 100
    turn = 0
    
    while not result.done and turn < max_turns:
        turn += 1
        obs = result.observation
        
        # Choose a legal action
        if obs.available_moves:
            action = PokemonAction(action_type="move", action_index=0)
        elif obs.available_switches:
            action = PokemonAction(action_type="switch", action_index=0)
        else:
            pytest.fail("No legal actions available")
        
        result = pokemon_client.step(action)
    
    # Battle should end within max turns
    assert turn < max_turns or result.done


def test_state_endpoint(pokemon_client):
    """Test that the state endpoint works."""
    result = pokemon_client.reset()
    
    # Take a few steps
    for _ in range(3):
        if result.done:
            break
        action = PokemonAction(action_type="move", action_index=0)
        result = pokemon_client.step(action)
    
    # Query state
    state = pokemon_client.state()
    
    assert state is not None
    assert state.episode_id is not None
    assert state.step_count >= 0
    assert state.battle_id is not None
    assert state.battle_format is not None
    assert state.player_username is not None
