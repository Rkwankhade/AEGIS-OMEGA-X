#!/bin/bash
# AEGIS OMEGA X — RUN ALL TESTS
# Usage: ./test.sh

AEGIS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${AEGIS_DIR}/.venv/bin/activate" 2>/dev/null || true

echo "╔══════════════════════════════════════════════════╗"
echo "║   AEGIS OMEGA X — TEST SUITE                    ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""

cd "$AEGIS_DIR"

export NEO4J_URI="bolt://localhost:7687"
export NEO4J_USER="neo4j"
export NEO4J_PASS="AegisOmegaX2024!"
export POSTGRES_URL="postgresql://aegis:AegisOmegaX2024!@localhost:5432/aegis_omega"
export REDIS_URL="redis://localhost:6379"

python -m pytest DEPLOY/tests/test_all_layers.py \
    -v \
    --tb=short \
    --no-header \
    -q \
    2>&1 | tee logs/test-results.log

echo ""
echo "Test results saved to: logs/test-results.log"
