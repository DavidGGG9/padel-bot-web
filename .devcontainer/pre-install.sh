#!/bin/bash

set -eu pipefail # Exit on error, treat unset vars as errors

echo "🔧 Starting pre-install script..."

echo "Setting up .env file for Docker Compose..."
echo COMPOSE_PROJECT_NAME=${localEnv:-$USER} >.env

echo "✅ Pre-install script completed."
