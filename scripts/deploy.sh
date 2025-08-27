#!/bin/bash

# Deployment script for manual deployment
# Use this if you want to deploy manually instead of using CI/CD

set -e

echo "🚀 Deploying Renewable Energy Forecasting App..."

# Configuration
IMAGE_NAME="renewable-energy-app"
CONTAINER_NAME="renewable-energy-app"

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ .env file not found!"
    echo "Please create .env file with your Azure SQL credentials"
    exit 1
fi

# Stop and remove existing container
echo "🛑 Stopping existing container..."
sudo docker stop $CONTAINER_NAME 2>/dev/null || true
sudo docker rm $CONTAINER_NAME 2>/dev/null || true

# Build new image
echo "🔨 Building Docker image..."
sudo docker build -t $IMAGE_NAME .

# Run new container
echo "🚀 Starting new container..."
sudo docker run -d \
    --name $CONTAINER_NAME \
    --restart unless-stopped \
    -p 80:5000 \
    --env-file .env \
    -v $(pwd)/logs:/app/logs \
    $IMAGE_NAME

# Show container status
echo "📊 Container status:"
sudo docker ps | grep $CONTAINER_NAME

# Show logs
echo "📝 Recent logs:"
sudo docker logs --tail 20 $CONTAINER_NAME

echo "✅ Deployment completed!"
echo "🌐 App should be available at http://your-server-ip"
