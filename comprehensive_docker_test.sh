#!/bin/bash
# Comprehensive Docker Test Script for Pokemon Environment
# This script tests the Docker deployment thoroughly

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
IMAGE_NAME="${1:-pokemon-env:latest}"
CONTAINER_NAME="pokemon-env-test-$$"
SHOWDOWN_PORT=8000
OPENENV_PORT=9980
TEST_TIMEOUT=120

echo "================================================================================"
echo "COMPREHENSIVE POKEMON ENVIRONMENT DOCKER TEST"
echo "================================================================================"
echo ""
echo "Image: $IMAGE_NAME"
echo "Container: $CONTAINER_NAME"
echo "Timeout: ${TEST_TIMEOUT}s"
echo ""

# Cleanup function
cleanup() {
    echo ""
    echo "Cleaning up..."
    docker stop "$CONTAINER_NAME" 2>/dev/null || true
    docker rm "$CONTAINER_NAME" 2>/dev/null || true
}

# Set trap for cleanup
trap cleanup EXIT

# Test 1: Image exists
echo "Test 1: Checking if image exists..."
if docker image inspect "$IMAGE_NAME" >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Image exists${NC}"
else
    echo -e "${RED}❌ Image not found: $IMAGE_NAME${NC}"
    echo "Build the image first with:"
    echo "  docker build -t pokemon-env:latest -f src/envs/pokemon_env/server/Dockerfile ."
    exit 1
fi

# Test 2: Start container
echo ""
echo "Test 2: Starting container..."
docker run -d \
    -p $SHOWDOWN_PORT:8000 \
    -p $OPENENV_PORT:9980 \
    --name "$CONTAINER_NAME" \
    "$IMAGE_NAME"

echo -e "${GREEN}✅ Container started${NC}"

# Test 3: Wait for services to be ready
echo ""
echo "Test 3: Waiting for services to start (max ${TEST_TIMEOUT}s)..."
START_TIME=$(date +%s)

# Wait for Pokemon Showdown
echo -n "  Waiting for Pokemon Showdown (port $SHOWDOWN_PORT)... "
while ! curl -s http://localhost:$SHOWDOWN_PORT >/dev/null 2>&1; do
    CURRENT_TIME=$(date +%s)
    ELAPSED=$((CURRENT_TIME - START_TIME))
    if [ $ELAPSED -gt $TEST_TIMEOUT ]; then
        echo -e "${RED}❌ Timeout${NC}"
        echo "Container logs:"
        docker logs "$CONTAINER_NAME"
        exit 1
    fi
    sleep 1
done
echo -e "${GREEN}✅${NC}"

# Wait for OpenEnv
echo -n "  Waiting for OpenEnv (port $OPENENV_PORT)... "
while ! curl -s http://localhost:$OPENENV_PORT/health >/dev/null 2>&1; do
    CURRENT_TIME=$(date +%s)
    ELAPSED=$((CURRENT_TIME - START_TIME))
    if [ $ELAPSED -gt $TEST_TIMEOUT ]; then
        echo -e "${RED}❌ Timeout${NC}"
        echo "Container logs:"
        docker logs "$CONTAINER_NAME"
        exit 1
    fi
    sleep 1
done
echo -e "${GREEN}✅${NC}"

STARTUP_TIME=$(($(date +%s) - START_TIME))
echo -e "${GREEN}✅ Both services started in ${STARTUP_TIME}s${NC}"

# Test 4: Health check endpoints
echo ""
echo "Test 4: Testing health check endpoints..."

# Pokemon Showdown health
echo -n "  Pokemon Showdown (GET /)... "
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:$SHOWDOWN_PORT/)
if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "301" ] || [ "$HTTP_CODE" = "302" ]; then
    echo -e "${GREEN}✅ HTTP $HTTP_CODE${NC}"
else
    echo -e "${RED}❌ HTTP $HTTP_CODE${NC}"
    exit 1
fi

# OpenEnv health
echo -n "  OpenEnv (GET /health)... "
HEALTH_RESPONSE=$(curl -s http://localhost:$OPENENV_PORT/health)
if echo "$HEALTH_RESPONSE" | grep -q "status"; then
    echo -e "${GREEN}✅ $HEALTH_RESPONSE${NC}"
else
    echo -e "${RED}❌ Unexpected response: $HEALTH_RESPONSE${NC}"
    exit 1
fi

# Test 5: Container health check
echo ""
echo "Test 5: Docker health check..."
sleep 10  # Wait for Docker health check to run
HEALTH_STATUS=$(docker inspect --format='{{.State.Health.Status}}' "$CONTAINER_NAME" 2>/dev/null || echo "no-healthcheck")
echo -n "  Health status: "
if [ "$HEALTH_STATUS" = "healthy" ]; then
    echo -e "${GREEN}✅ $HEALTH_STATUS${NC}"
elif [ "$HEALTH_STATUS" = "starting" ]; then
    echo -e "${YELLOW}⏳ $HEALTH_STATUS (waiting...)${NC}"
    sleep 20
    HEALTH_STATUS=$(docker inspect --format='{{.State.Health.Status}}' "$CONTAINER_NAME")
    if [ "$HEALTH_STATUS" = "healthy" ]; then
        echo -e "  ${GREEN}✅ Now $HEALTH_STATUS${NC}"
    else
        echo -e "  ${RED}❌ Still $HEALTH_STATUS${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  $HEALTH_STATUS${NC}"
fi

# Test 6: API endpoints
echo ""
echo "Test 6: Testing API endpoints..."

# Test /state endpoint (before reset)
echo -n "  GET /state (initial)... "
STATE_RESPONSE=$(curl -s http://localhost:$OPENENV_PORT/state)
if echo "$STATE_RESPONSE" | grep -q "episode_id"; then
    echo -e "${GREEN}✅ Valid response${NC}"
else
    echo -e "${YELLOW}⚠️  Unexpected format${NC}"
fi

# Test /reset endpoint
echo -n "  POST /reset... "
RESET_RESPONSE=$(curl -s -X POST http://localhost:$OPENENV_PORT/reset)
if echo "$RESET_RESPONSE" | grep -q "observation"; then
    echo -e "${GREEN}✅ Valid response${NC}"
    
    # Extract some observation data
    if echo "$RESET_RESPONSE" | python3 -m json.tool >/dev/null 2>&1; then
        echo "    Response contains valid JSON"
        # Check for key fields
        if echo "$RESET_RESPONSE" | grep -q "active_pokemon"; then
            echo "    ✓ Contains active_pokemon"
        fi
        if echo "$RESET_RESPONSE" | grep -q "available_moves"; then
            echo "    ✓ Contains available_moves"
        fi
    fi
else
    echo -e "${RED}❌ Invalid response${NC}"
    echo "Response: $RESET_RESPONSE"
    exit 1
fi

# Test /step endpoint
echo -n "  POST /step... "
STEP_PAYLOAD='{"action_type": "move", "action_index": 0}'
STEP_RESPONSE=$(curl -s -X POST \
    -H "Content-Type: application/json" \
    -d "$STEP_PAYLOAD" \
    http://localhost:$OPENENV_PORT/step)

if echo "$STEP_RESPONSE" | grep -q "observation"; then
    echo -e "${GREEN}✅ Valid response${NC}"
    
    # Check for done/reward fields
    if echo "$STEP_RESPONSE" | grep -q "done"; then
        echo "    ✓ Contains done flag"
    fi
    if echo "$STEP_RESPONSE" | grep -q "reward"; then
        echo "    ✓ Contains reward"
    fi
else
    echo -e "${RED}❌ Invalid response${NC}"
    echo "Response: $STEP_RESPONSE"
    exit 1
fi

# Test 7: Container logs
echo ""
echo "Test 7: Checking container logs..."
LOG_OUTPUT=$(docker logs "$CONTAINER_NAME" 2>&1 | tail -n 20)

echo -n "  Checking for errors in logs... "
if echo "$LOG_OUTPUT" | grep -iq "error\|exception\|fatal"; then
    echo -e "${YELLOW}⚠️  Found error messages${NC}"
    echo "Recent errors:"
    echo "$LOG_OUTPUT" | grep -i "error\|exception\|fatal" | head -n 5
else
    echo -e "${GREEN}✅ No errors${NC}"
fi

echo -n "  Checking supervisor status... "
if echo "$LOG_OUTPUT" | grep -q "entered RUNNING state"; then
    echo -e "${GREEN}✅ Services running${NC}"
else
    echo -e "${YELLOW}⚠️  Status unclear${NC}"
fi

# Test 8: Resource usage
echo ""
echo "Test 8: Checking resource usage..."
STATS=$(docker stats "$CONTAINER_NAME" --no-stream --format "{{.CPUPerc}} {{.MemUsage}}")
CPU=$(echo "$STATS" | awk '{print $1}')
MEM=$(echo "$STATS" | awk '{print $2}')

echo "  CPU: $CPU"
echo "  Memory: $MEM"

# Test 9: Port accessibility
echo ""
echo "Test 9: Verifying port accessibility..."
echo -n "  Port $SHOWDOWN_PORT (Showdown)... "
if nc -z localhost $SHOWDOWN_PORT 2>/dev/null; then
    echo -e "${GREEN}✅ Accessible${NC}"
else
    echo -e "${RED}❌ Not accessible${NC}"
fi

echo -n "  Port $OPENENV_PORT (OpenEnv)... "
if nc -z localhost $OPENENV_PORT 2>/dev/null; then
    echo -e "${GREEN}✅ Accessible${NC}"
else
    echo -e "${RED}❌ Not accessible${NC}"
fi

# Test 10: Battle flow test
echo ""
echo "Test 10: Testing complete battle flow..."
python3 << 'PYTHON_TEST'
import sys
import json
import requests

try:
    print("  Initializing client...")
    base_url = "http://localhost:9980"
    
    # Reset
    print("  1. Reset environment...")
    reset_resp = requests.post(f"{base_url}/reset", timeout=30)
    reset_resp.raise_for_status()
    reset_data = reset_resp.json()
    
    if "observation" not in reset_data:
        print("    ❌ No observation in reset response")
        sys.exit(1)
    print("    ✅ Reset successful")
    
    # Take a few steps
    print("  2. Taking 3 battle steps...")
    for i in range(3):
        step_data = {"action_type": "move", "action_index": 0}
        step_resp = requests.post(
            f"{base_url}/step",
            json=step_data,
            timeout=30
        )
        step_resp.raise_for_status()
        step_result = step_resp.json()
        
        if "observation" not in step_result:
            print(f"    ❌ No observation in step {i+1} response")
            sys.exit(1)
        
        print(f"    ✅ Step {i+1} completed (done={step_result.get('done', False)})")
        
        if step_result.get("done"):
            print("    ℹ️  Battle ended early")
            break
    
    # Check state
    print("  3. Checking state...")
    state_resp = requests.get(f"{base_url}/state", timeout=10)
    state_resp.raise_for_status()
    state_data = state_resp.json()
    
    if "episode_id" in state_data and "step_count" in state_data:
        print(f"    ✅ State valid (steps={state_data.get('step_count')})")
    else:
        print("    ❌ Invalid state response")
        sys.exit(1)
    
    print("\n  ✅ Battle flow test completed successfully")
    
except requests.exceptions.RequestException as e:
    print(f"\n  ❌ Request failed: {e}")
    sys.exit(1)
except Exception as e:
    print(f"\n  ❌ Test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
PYTHON_TEST

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Battle flow test failed${NC}"
    exit 1
fi

# Test 11: Security checks
echo ""
echo "Test 11: Security checks..."

echo -n "  Checking if running as non-root... "
CONTAINER_USER=$(docker exec "$CONTAINER_NAME" whoami 2>/dev/null || echo "unknown")
if [ "$CONTAINER_USER" = "pokemonenv" ] || [ "$CONTAINER_USER" = "root" ]; then
    if [ "$CONTAINER_USER" = "root" ]; then
        echo -e "${YELLOW}⚠️  Running as root (consider using non-root user)${NC}"
    else
        echo -e "${GREEN}✅ Running as $CONTAINER_USER${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  User: $CONTAINER_USER${NC}"
fi

echo -n "  Checking Showdown security flag... "
SHOWDOWN_CMD=$(docker exec "$CONTAINER_NAME" ps aux | grep "pokemon-showdown" | head -n 1)
if echo "$SHOWDOWN_CMD" | grep -q "\-\-no-security"; then
    echo -e "${YELLOW}⚠️  Running with --no-security flag${NC}"
    echo "    (Acceptable for dev/testing, remove for production)"
else
    echo -e "${GREEN}✅ Security enabled${NC}"
fi

# Summary
echo ""
echo "================================================================================"
echo "TEST SUMMARY"
echo "================================================================================"
echo ""
echo -e "${GREEN}✅ All critical tests passed${NC}"
echo ""
echo "Container Details:"
echo "  Name: $CONTAINER_NAME"
echo "  Image: $IMAGE_NAME"
echo "  Startup Time: ${STARTUP_TIME}s"
echo "  CPU Usage: $CPU"
echo "  Memory Usage: $MEM"
echo ""
echo "Services:"
echo "  Pokemon Showdown: http://localhost:$SHOWDOWN_PORT"
echo "  OpenEnv API: http://localhost:$OPENENV_PORT"
echo ""
echo "To keep the container running:"
echo "  docker rm -f $CONTAINER_NAME && docker run -d -p $SHOWDOWN_PORT:8000 -p $OPENENV_PORT:9980 --name pokemon-env-dev $IMAGE_NAME"
echo ""
echo "================================================================================"
