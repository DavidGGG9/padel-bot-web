#!/bin/zsh

set -eu pipefail # Exit on error, treat unset vars as errors

echo "🔧 Starting postinstall script..."

# Move to workspace
if cd /app/workspace; then
    echo "📁 Entered /app/workspace"
else
    echo "❌ Workspace directory not found. Exiting."
    exit 1
fi

# Install dependencies
echo "📦 Installing Python dependencies via uv..."
uv sync --no-progress

# Setup pre-commit hooks
echo "🪝 Installing pre-commit hooks..."
uv run pre-commit install

echo "🚀 READY TO ROCK!"
exit 0
