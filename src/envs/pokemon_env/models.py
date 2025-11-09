# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""
Data models for Pokemon Battle Environment.

This module defines the Action, Observation, and State types for Pokemon battles
via poke-env integration.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional

from core.env_server import Action, Observation, State


@dataclass
class RewardConfig:
    """
    Configuration for reward shaping in dense reward mode.
    
    Attributes:
        faint_opponent_bonus: Reward for fainting an opponent Pokemon
        faint_self_penalty: Penalty for losing one of your Pokemon
        hp_damage_coefficient: Reward per % HP damage dealt to opponent
        status_inflict_bonus: Reward for inflicting status effect (burn, paralyze, etc.)
        status_remove_bonus: Reward for removing status from your Pokemon
        stat_boost_bonus: Reward for stat boosts (Swords Dance, Dragon Dance, etc.)
        buff_remove_bonus: Reward for removing opponent's stat boosts
        hp_recovery_bonus: Reward for HP recovery moves
        final_win_bonus: Bonus reward for winning the battle
        final_loss_penalty: Penalty for losing the battle
    """
    faint_opponent_bonus: float = 0.2
    faint_self_penalty: float = 0.2
    hp_damage_coefficient: float = 0.05
    status_inflict_bonus: float = 0.1
    status_remove_bonus: float = 0.1
    stat_boost_bonus: float = 0.05
    buff_remove_bonus: float = 0.05
    hp_recovery_bonus: float = 0.05
    final_win_bonus: float = 10.0
    final_loss_penalty: float = 10.0


@dataclass
class PokemonAction(Action):
    """
    Action for Pokemon battles.

    Attributes:
        action_type: Type of action - "move", "switch", "forfeit", or "default"
        action_index: Index of the move (0-3) or switch target (0-5)
        move_id: Optional move identifier (e.g., "thunderbolt")
        switch_pokemon: Optional Pokemon to switch to (by species name or index)
        mega_evolve: Whether to mega evolve this turn (if applicable)
        z_move: Whether to use a Z-move this turn (if applicable)
        dynamax: Whether to dynamax this turn (if applicable)
        terastallize: Whether to terastallize this turn (if applicable)
    """
    action_type: Literal["move", "switch", "forfeit", "default"] = "move"
    action_index: int = 0
    move_id: Optional[str] = None
    switch_pokemon: Optional[str] = None
    mega_evolve: bool = False
    z_move: bool = False
    dynamax: bool = False
    terastallize: bool = False


@dataclass
class PokemonData:
    """
    Simplified Pokemon data for observations.
    
    Stat Masking Rules:
    - Player Pokemon: All stats visible (seen=True)
    - Opponent Pokemon (revealed): All stats visible (seen=True)
    - Opponent Pokemon (unrevealed): Base stats masked as -1 (seen=False)
    
    Unrevealed Pokemon have species="unknown" or "unrevealed" and attack/defense/
    special_attack/special_defense/speed set to -1 to indicate hidden values.
    This simulates real Pokemon battles where you can't see opponent stats until
    they're revealed in battle.
    """
    species: str
    hp_percent: float
    max_hp: int
    current_hp: int
    level: int
    status: Optional[str]
    types: List[str]
    ability: Optional[str]
    item: Optional[str]
    
    # Base stats - may be -1 for opponent Pokemon (hidden/unknown)
    attack: int
    defense: int
    special_attack: int
    special_defense: int
    speed: int
    
    boosts: Dict[str, int] = field(default_factory=dict)
    moves: List[Dict[str, Any]] = field(default_factory=list)
    
    fainted: bool = False
    active: bool = False
    seen: bool = True  # False for unrevealed opponent Pokemon


@dataclass
class PokemonObservation(Observation):
    """
    Observation from Pokemon battle environment.

    This represents the full battle state visible to the agent.

    Attributes:
        active_pokemon: Currently active Pokemon on your side
        opponent_active_pokemon: Currently active opponent Pokemon
        team: Your full team of 6 Pokemon
        opponent_team: Opponent's team (may have limited visibility)
        available_moves: List of move indices you can use (0-3)
        available_switches: List of Pokemon indices you can switch to (0-5)
        legal_actions: Combined list of legal action descriptors
        field_conditions: Dict of field effects (weather, terrain, hazards, etc.)
        turn: Current turn number
        forced_switch: Whether you must switch (active Pokemon fainted)
        can_mega_evolve: Whether mega evolution is possible this turn (convenience field)
        can_z_move: Whether a Z-move is possible this turn (convenience field)
        can_dynamax: Whether dynamax is possible this turn (convenience field)
        can_terastallize: Whether terastallization is possible this turn (convenience field)
        battle_format: Battle format (e.g., "gen8randombattle", "gen8ou")
        
    Note: The can_* fields are provided at the observation level for convenience.
    They reflect whether the current active Pokemon can use these mechanics.
    In poke-env, these are properties of the active Pokemon, not individual team members.
    """
    active_pokemon: Optional[PokemonData] = None
    opponent_active_pokemon: Optional[PokemonData] = None
    team: List[PokemonData] = field(default_factory=list)
    opponent_team: List[PokemonData] = field(default_factory=list)
    
    available_moves: List[int] = field(default_factory=list)
    available_switches: List[int] = field(default_factory=list)
    legal_actions: List[Dict[str, Any]] = field(default_factory=list)
    
    field_conditions: Dict[str, Any] = field(default_factory=dict)
    turn: int = 0
    forced_switch: bool = False
    
    can_mega_evolve: bool = False
    can_z_move: bool = False
    can_dynamax: bool = False
    can_terastallize: bool = False
    
    battle_format: str = "gen8randombattle"
    battle_id: Optional[str] = None


@dataclass
class PokemonState(State):
    """
    State for Pokemon battle environment.

    Attributes:
        battle_format: Battle format being used
        player_username: Player's username
        server_url: Pokemon Showdown server URL
        battle_id: Current battle ID
        is_battle_finished: Whether the battle has concluded
        battle_winner: Winner of the battle (if finished)
    """
    battle_format: str = "gen8randombattle"
    player_username: str = "player"
    server_url: str = "localhost:8000"
    battle_id: Optional[str] = None
    is_battle_finished: bool = False
    battle_winner: Optional[str] = None
