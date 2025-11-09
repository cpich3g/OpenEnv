# Pokemon Battle Environment

OpenEnv integration for Pokemon battles using poke-env and Pokemon Showdown.

## Features

- ✅ Full Pokemon battle simulation via poke-env
- ✅ HTTP-based OpenEnv interface
- ✅ Configurable reward modes (sparse/dense)
- ✅ Memory leak prevention with automatic cleanup
- ✅ Thread-safe concurrent request handling
- ✅ Comprehensive battle state tracking
- ✅ Gen 9 support with modern mechanics

## Quick Start

### Local Development

```bash
# Start Pokemon Showdown
cd /tmp && git clone https://github.com/smogon/pokemon-showdown.git
cd pokemon-showdown && npm install
node pokemon-showdown start --no-security

# Start Pokemon Environment Server
export PYTHONPATH=/Users/sanyambhutani/GH/OpenEnv/src
python -m envs.pokemon_env.server.app
```

### Using the HTTP Client

```python
from envs.pokemon_env import PokemonEnv, PokemonAction

# Connect to server
client = PokemonEnv(base_url="http://localhost:9980")

# Reset and play
result = client.reset()
print(f"Active: {result.observation.active_pokemon.species}")

# Take action
action = PokemonAction(action_type="move", action_index=0)
result = client.step(action)
print(f"Reward: {result.reward}, Done: {result.done}")
```

### Docker

**Recommended: All-in-One Container** (simplest approach)

The main Dockerfile includes both Pokemon Showdown and OpenEnv in a single container:

```bash
# Build the all-in-one image (run from project root directory)
docker build -t pokemon-env:latest -f src/envs/pokemon_env/server/Dockerfile .

# Run the container (both services start automatically)
docker run -d --name pokemon-env -p 8000:8000 -p 9980:9980 pokemon-env:latest

# Test
curl http://localhost:8000        # Pokemon Showdown
curl http://localhost:9980/health # OpenEnv server

# Optional: Override the OpenEnv port
docker run -d --name pokemon-env -p 8000:8000 -p 8080:8080 -e PORT=8080 pokemon-env:latest
```

**Advanced: Separate Containers** (for specialized deployments)

If you need to run Pokemon Showdown and OpenEnv in separate containers:

```bash
# Build separate images
docker build -t pokemon-showdown:latest -f src/envs/pokemon_env/server/Dockerfile.showdown .
docker build -t pokemon-env:latest -f src/envs/pokemon_env/server/Dockerfile.pokemonenv .

# Create Docker network for container communication
docker network create pokemon-network

# Run Pokemon Showdown server
docker run -d --name pokemon-showdown --network pokemon-network -p 8000:8000 pokemon-showdown:latest

# Run OpenEnv server (pointing to the Showdown container)
docker run -d --name pokemon-env --network pokemon-network -p 9980:9980 \
    -e SHOWDOWN_SERVER_URL=pokemon-showdown:8000 pokemon-env:latest

# Test
curl http://localhost:9980/health
```

## Configuration

Environment variables:
- `POKEMON_BATTLE_FORMAT` - Battle format (default: `gen8randombattle`)
- `POKEMON_REWARD_MODE` - Reward mode: `sparse` or `dense` (default: `sparse`)
- `POKEMON_MAX_TURNS` - Maximum turns per battle (default: `1000`)
- `POKEMON_PLAYER_USERNAME` - Player username (default: auto-generated)

### Dense Reward Coefficients

When using `POKEMON_REWARD_MODE=dense`, you can customize reward coefficients:

- `POKEMON_FAINT_OPPONENT_BONUS` - Reward per opponent Pokemon fainted (default: `0.2`)
- `POKEMON_FAINT_SELF_PENALTY` - Penalty per own Pokemon fainted (default: `0.2`)
- `POKEMON_HP_DAMAGE_COEF` - Reward per % HP damage to opponent (default: `0.05`)
- `POKEMON_STATUS_INFLICT_BONUS` - Reward for inflicting status (burn, paralyze, etc.) (default: `0.1`)
- `POKEMON_STATUS_REMOVE_BONUS` - Reward for removing status from own Pokemon (default: `0.1`)
- `POKEMON_STAT_BOOST_BONUS` - Reward per stat boost level (Swords Dance, etc.) (default: `0.05`)
- `POKEMON_BUFF_REMOVE_BONUS` - Reward for removing opponent's stat boosts (default: `0.05`)
- `POKEMON_HP_RECOVERY_BONUS` - Reward for HP recovery moves (default: `0.05`)
- `POKEMON_FINAL_WIN_BONUS` - Bonus for winning the battle (default: `10.0`)
- `POKEMON_FINAL_LOSS_PENALTY` - Penalty for losing the battle (default: `10.0`)

Example with custom rewards:

```bash
docker run -d \
  -e POKEMON_REWARD_MODE=dense \
  -e POKEMON_FINAL_WIN_BONUS=20.0 \
  -e POKEMON_FAINT_OPPONENT_BONUS=0.5 \
  -p 8000:8000 -p 9980:9980 \
  pokemon-env:latest
```

## Architecture

### Battle Flow

```
HTTP Client → FastAPI Server → PokemonEnvironment
                                      ↓
                              OpenEnvPokemonPlayer
                                      ↓
                              poke-env (POKE_LOOP)
                                      ↓
                     Pokemon Showdown Server (Node.js)
                              (WebSocket)
```

### Key Design Decisions

1. **Event Loop Bridging**: Uses `asyncio.run_coroutine_threadsafe()` to safely bridge FastAPI's event loop with poke-env's POKE_LOOP background thread
2. **Turn Synchronization**: Waits for actual turn completion signals instead of polling or sleeping
3. **Thread-Safe Design**: Single lock prevents concurrent reset/step operations; proper async primitives for cross-thread communication
4. **Memory Cleanup**: Old battles automatically cleaned up every 10 episodes
5. **Battle Cancellation**: Previous battle tasks cancelled on reset to prevent resource leaks
6. **Action Validation**: Validates all action indices against available moves/switches before execution
7. **Dense Rewards**: Configurable reward shaping based on damage, faints, status effects, and battle outcome

### Reward Modes

- **sparse** (default): `+1` for win, `-1` for loss, `0` otherwise
- **dense**: Comprehensive reward shaping with configurable coefficients:
  - **Pokemon faints**: Reward for opponent faints, penalty for own faints
  - **HP damage**: Reward proportional to opponent HP damage dealt
  - **Status effects**: Reward for inflicting status (burn, paralyze, toxic, etc.)
  - **Status removal**: Reward for removing status from own Pokemon (Heal Bell, Aromatherapy, etc.)
  - **Stat boosts**: Reward for stat increases (Swords Dance, Dragon Dance, etc.)
  - **Buff removal**: Reward for removing opponent buffs (Haze, Whirlwind, etc.)
  - **HP recovery**: Reward for healing moves (Roost, Recover, etc.)
  - **Final outcome**: Large bonus/penalty for winning/losing (default: ±10.0)

Configure via `POKEMON_REWARD_MODE` environment variable or `RewardConfig` class in code.

## Examples

### Simple Battle Loop

```python
from src.envs.pokemon_env import PokemonEnv, PokemonAction

client = PokemonEnv(base_url="http://localhost:9980")
result = client.reset()

while not result.done:
    # Choose first available move
    action = PokemonAction(action_type="move", action_index=0)
    result = client.step(action)
    print(f"Reward: {result.reward}, HP: {result.observation.active_pokemon.hp}")
```

See `examples/pokemon_env_example.py` for a complete working example.

## Testing

The environment includes comprehensive pytest-based tests:

```bash
# Run all Pokemon environment tests
pytest tests/envs/pokemon_env/

# Run specific test file
pytest tests/envs/pokemon_env/test_environment.py  # Direct environment testing
pytest tests/envs/pokemon_env/test_client.py        # HTTP client testing

# Run with verbose output
pytest tests/envs/pokemon_env/ -v
```

**Test Coverage:**
- Environment creation and configuration
- Reset functionality
- Single-step and multi-step battles
- Action validation (illegal moves)
- Dense reward computation
- HTTP client integration
- State endpoint queries

## Known Limitations

- Single battle at a time (no concurrent battles per environment instance)
- Random battles only tested (custom teams supported but untested)
- Singles format only (doubles would require model changes)

## Performance

- Battle initialization: < 2s
- Step execution: < 0.5s
- Full battle (50 turns): < 30s
- Memory: Stable over 100+ episodes (with automatic cleanup)

## Troubleshooting

### Connection Issues

**Problem:** `Connection refused` or `Failed to connect`

**Solutions:**
- Verify Pokemon Showdown is running: `curl http://localhost:8000`
- Check Docker container status: `docker ps`
- Check server logs: `docker logs pokemon-env`

### Battle Timeouts

**Problem:** `Battle timeout` or requests hanging

**Solutions:**
- Restart Pokemon Showdown server (may be overloaded)
- Increase `POKEMON_MAX_TURNS` environment variable
- Check for network issues between containers

### Memory Growth

**Problem:** Memory usage grows over time

**Solutions:**
- Automatic cleanup runs every 10 episodes (default behavior)
- Restart server if memory continues growing
- Monitor with: `docker stats pokemon-env`

### Illegal Moves

**Problem:** `Illegal move` errors or unexpected forfeit

**Solutions:**
- Check action indices are within valid range
- Verify `available_moves` and `available_switches` in observation
- Review battle logs for specific error messages
- Use `action_type="forfeit"` to explicitly surrender

### Docker Build Failures

**Problem:** Docker build fails or images don't run

**Solutions:**
- Ensure building from project root directory
- Use correct Dockerfile path: `-f src/envs/pokemon_env/server/Dockerfile`
- Check Node.js 18+ is available in base image
- Verify all dependencies in `requirements.txt`

## Credits

- [poke-env](https://github.com/hsahovic/poke-env) - Pokemon battle simulation library
- [Pokemon Showdown](https://github.com/smogon/pokemon-showdown) - Battle engine (Node.js)
- [OpenEnv](https://github.com/meta-pytorch/openenv) - HTTP environment framework
