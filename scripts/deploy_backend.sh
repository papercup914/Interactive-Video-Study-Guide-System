#!/usr/bin/env bash
# ==============================================================================
# AWS EC2 Backend Build & Deployment Automation Script
# Interactive Video Study Guide System
# ==============================================================================

set -e

# Change directory to project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

echo "🔍 Checking environment variables in backend/.env..."
if [ ! -f "backend/.env" ]; then
    echo "❌ Error: 'backend/.env' not found!"
    echo "👉 Please copy 'backend/.env.example' to 'backend/.env' and fill in your keys:"
    echo "   cp backend/.env.example backend/.env"
    echo "   nano backend/.env"
    exit 1
fi

echo "🐳 Building and starting containers (FastAPI + Celery + Redis)..."
docker compose up -d --build --remove-orphans

echo "⏳ Waiting for backend services to stabilize (5 seconds)..."
sleep 5

echo "📊 Checking container status:"
docker compose ps

echo ""
echo "🚀 Backend is running! You can test the health endpoint with:"
echo "   curl http://localhost:8000/health"
echo "================================================================================"
