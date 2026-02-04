#!/bin/bash

# LDAPGuard Quick Start Script

set -e

echo "🔒 LDAPGuard Setup Script"
echo "=========================="
echo ""

# Check if docker-compose or podman-compose is available
if command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
elif command -v podman-compose &> /dev/null; then
    COMPOSE_CMD="podman-compose"
else
    echo "❌ Error: Neither docker-compose nor podman-compose found"
    echo "Please install Docker Compose or Podman Compose first"
    exit 1
fi

echo "✅ Found: $COMPOSE_CMD"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from .env.example..."
    cp .env.example .env
    
    # Generate random keys
    SECRET_KEY=$(openssl rand -hex 32)
    ENCRYPTION_KEY=$(openssl rand -hex 32)
    POSTGRES_PASSWORD=$(openssl rand -hex 16)
    
    # Update .env with generated keys
    sed -i "s/SECRET_KEY=.*/SECRET_KEY=$SECRET_KEY/" .env
    sed -i "s/ENCRYPTION_KEY=.*/ENCRYPTION_KEY=$ENCRYPTION_KEY/" .env
    sed -i "s/POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=$POSTGRES_PASSWORD/" .env
    sed -i "s/your-secure-password-here/$POSTGRES_PASSWORD/g" .env
    
    echo "✅ Generated secure keys in .env file"
    echo ""
else
    echo "✅ .env file already exists"
    echo ""
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p logs backups
echo "✅ Directories created"
echo ""

# Start services
echo "🚀 Starting LDAPGuard services..."
$COMPOSE_CMD up -d

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check service health
echo ""
echo "🏥 Checking service health..."

if command -v curl &> /dev/null; then
    if curl -s http://localhost:8000/health > /dev/null; then
        echo "✅ API is healthy"
    else
        echo "⚠️  API is starting up..."
    fi
else
    echo "⚠️  curl not found, skipping health check"
fi

echo ""
echo "=========================================="
echo "✨ LDAPGuard is now running!"
echo "=========================================="
echo ""
echo "📍 Access points:"
echo "   - Web UI:  http://localhost:3000"
echo "   - API:     http://localhost:8000"
echo "   - API Docs: http://localhost:8000/docs"
echo "   - Metrics:  http://localhost:8000/metrics"
echo ""
echo "📊 View logs:"
echo "   $COMPOSE_CMD logs -f"
echo ""
echo "🛑 Stop services:"
echo "   $COMPOSE_CMD down"
echo ""
echo "📚 Documentation: README.md"
echo ""
