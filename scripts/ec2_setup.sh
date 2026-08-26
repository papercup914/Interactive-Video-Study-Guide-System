#!/usr/bin/env bash
# ==============================================================================
# AWS EC2 (Ubuntu 24.04 / 22.04 LTS) One-Click Setup Script
# Interactive Video Study Guide System - Backend Environment
# ==============================================================================

set -e

echo "🚀 [1/4] Updating system packages..."
sudo apt-get update -y && sudo apt-get upgrade -y
sudo apt-get install -y curl git ufw fail2ban htop

echo "💾 [2/4] Configuring 2GB Swap Memory for AWS EC2 Free Tier (1GB RAM)..."
if [ ! -f /swapfile ]; then
    sudo fallocate -l 2G /swapfile
    sudo chmod 600 /swapfile
    sudo mkswap /swapfile
    sudo swapon /swapfile
    echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
    echo "  ✅ 2GB Swap memory successfully created and enabled."
else
    echo "  ℹ️ /swapfile already exists. Skipping swap creation."
fi

echo "🐳 [3/4] Installing Docker and Docker Compose plugin..."
if ! command -v docker &> /dev/null; then
    sudo apt-get install -y docker.io docker-compose-v2
    sudo systemctl enable docker
    sudo systemctl start docker
    sudo usermod -aG docker "$USER"
    echo "  ✅ Docker successfully installed."
else
    echo "  ℹ️ Docker is already installed."
fi

echo "🛡️ [4/4] Configuring UFW Firewall (SSH: 22, API: 8000)..."
sudo ufw allow 22/tcp || true
sudo ufw allow 8000/tcp || true
sudo ufw --force enable || true

echo ""
echo "================================================================================"
echo "🎉 AWS EC2 Server Setup Completed Successfully!"
echo "👉 Please log out and reconnect SSH (or run 'newgrp docker') to apply docker permissions."
echo "================================================================================"
