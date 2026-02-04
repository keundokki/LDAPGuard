#!/bin/bash

# LDAPGuard Multi-Architecture Build Script
# Builds Docker images for both amd64 and arm64 architectures

set -e

echo "🏗️  LDAPGuard Multi-Architecture Builder"
echo "======================================"
echo ""

# Check if buildx is available
if ! docker buildx version &> /dev/null; then
    echo "❌ Error: docker buildx is not available"
    echo "Please install Docker Buildx: https://docs.docker.com/build/install-buildx/"
    exit 1
fi

# Create builder instance if it doesn't exist
BUILDER_NAME="ldapguard-builder"
if ! docker buildx ls | grep -q "^$BUILDER_NAME"; then
    echo "📦 Creating builder instance: $BUILDER_NAME"
    docker buildx create --name "$BUILDER_NAME" --use
else
    echo "✅ Using existing builder: $BUILDER_NAME"
    docker buildx use "$BUILDER_NAME"
fi

echo ""
echo "🔨 Building multi-architecture images..."
echo "  Architectures: linux/amd64, linux/arm64"
echo ""

# Build arguments
PLATFORMS="linux/amd64,linux/arm64"
DOCKERFILES=("Dockerfile.api" "Dockerfile.worker" "Dockerfile.web")
TAGS=("ldapguard-api" "ldapguard-worker" "ldapguard-web")

# Check if we should push (requires GHCR authentication)
PUSH_FLAG="--load"
if [ "$1" == "--push" ]; then
    PUSH_FLAG="--push"
    echo "📤 Images will be pushed to GHCR"
fi

for i in "${!DOCKERFILES[@]}"; do
    DOCKERFILE="${DOCKERFILES[$i]}"
    TAG="${TAGS[$i]}"
    
    echo "🏗️  Building $TAG from $DOCKERFILE..."
    
    if [ "$PUSH_FLAG" == "--push" ]; then
        docker buildx build \
            --file "$DOCKERFILE" \
            --platforms "$PLATFORMS" \
            --tag "ghcr.io/keundokki/$TAG:latest" \
            --tag "ghcr.io/keundokki/$TAG:$(git rev-parse --short HEAD)" \
            --push \
            .
    else
        docker buildx build \
            --file "$DOCKERFILE" \
            --platforms "$PLATFORMS" \
            --tag "$TAG:latest" \
            --load \
            .
    fi
    
    echo "✅ Built $TAG"
    echo ""
done

echo "✨ All images built successfully!"
echo ""

if [ "$PUSH_FLAG" == "--load" ]; then
    echo "💡 Tip: To push to GHCR, run:"
    echo "   ./scripts/build-multiarch.sh --push"
fi
