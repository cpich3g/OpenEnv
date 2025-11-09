#!/usr/bin/env python3
# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.

"""
Simple example demonstrating Pokemon Battle Environment usage via HTTP.

Prerequisites:
1. Pokemon environment server running:
   docker run -d -p 8000:8000 -p 9980:9980 pokemon-env:latest
   
2. Install client library:
   pip install -e .

Usage:
    python examples/pokemon_env_example.py
"""

from src.envs.pokemon_env import PokemonEnv, PokemonAction

def main():
    # Create client connected to HTTP server
    client = PokemonEnv(base_url="http://localhost:9980")
    
    print("Pokemon Battle Environment Example")
    print("=" * 50)
    
    # Reset environment to start new battle
    result = client.reset()
    print(f"\n✅ Battle started!")
    print(f"Episode ID: {result.episode_id}")
    print(f"Active Pokemon: {result.observation.active_pokemon.species}")
    print(f"HP: {result.observation.active_pokemon.hp}/{result.observation.active_pokemon.max_hp}")
    print(f"Available moves: {len(result.observation.available_moves)}")
    
    # Take actions until battle ends
    step_count = 0
    total_reward = 0.0
    
    while not result.done:
        step_count += 1
        
        # Choose first available move (simple strategy)
        if result.observation.available_moves:
            action = PokemonAction(
                action_type="move",
                action_index=0
            )
            print(f"\nStep {step_count}: Using move {result.observation.available_moves[0]}")
        else:
            # No moves available, switch to first available Pokemon
            action = PokemonAction(
                action_type="switch",
                action_index=0
            )
            print(f"\nStep {step_count}: Switching Pokemon")
        
        # Execute action
        result = client.step(action)
        total_reward += result.reward
        
        print(f"Reward: {result.reward:.3f}")
        print(f"Active: {result.observation.active_pokemon.species} "
              f"(HP: {result.observation.active_pokemon.hp}/{result.observation.active_pokemon.max_hp})")
        
        # Safety limit
        if step_count >= 100:
            print("\n⚠️  Reached step limit (100)")
            break
    
    # Battle finished
    print("\n" + "=" * 50)
    print(f"Battle finished in {step_count} steps")
    print(f"Total reward: {total_reward:.3f}")
    
    if result.reward > 0:
        print("🎉 Victory!")
    elif result.reward < 0:
        print("💀 Defeated")
    else:
        print("🤝 Draw")

if __name__ == "__main__":
    main()
