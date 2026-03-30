#!/bin/bash
set -e

echo "=== One-Click Repo End-to-End Test ==="
echo ""

# Clean workspace
echo "1. Cleaning workspace..."
find ~/oc_repo_workspace -maxdepth 1 -mindepth 1 -exec rm -rf {} + 2>/dev/null || true
rm -f ~/oc_repo_workspace/projects.json 2>/dev/null || true
echo "   Done"

# Test install
echo ""
echo "2. Installing Hello-World repo..."
uv run python -m backend.cli install --auto-approve "https://github.com/octocat/Hello-World"
echo ""

# Test list
echo "3. Listing projects..."
uv run python -m backend.cli list
echo ""

# Test history
echo "4. Checking history for Hello-World..."
uv run python -m backend.cli history Hello-World
echo ""

# Test remove
echo "5. Removing Hello-World..."
uv run python -m backend.cli remove --force Hello-World
echo ""

# Verify removed
echo "6. Verifying removal..."
uv run python -m backend.cli list
echo ""

# Test with Flask (real dependencies)
echo "7. Installing Flask repo (auto mode)..."
uv run python -m backend.cli install --auto-approve "https://github.com/pallets/flask"
echo ""

# List again
echo "8. Listing projects..."
uv run python -m backend.cli list
echo ""

# Stop Flask
echo "9. Stopping Flask..."
uv run python -m backend.cli stop flask
echo ""

# List to confirm stopped
echo "10. Confirming stopped..."
uv run python -m backend.cli list
echo ""

# Clean up
echo "11. Cleaning up..."
uv run python -m backend.cli remove --force flask
echo ""

echo "=== All E2E tests passed ==="
