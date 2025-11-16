#!/bin/bash

# Configuration
IMAGE_NAME="my-game"
CONTAINER_NAME="my-game-container"
PORT_5000=5000
PORT_8765=8765
URL="http://127.0.0.1:5000/"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if image exists
if docker image inspect $IMAGE_NAME >/dev/null 2>&1; then
    echo -e "${YELLOW}Image '$IMAGE_NAME' already exists, skipping build${NC}"
else
    echo -e "${GREEN}Building Docker image...${NC}"
    if docker build -t $IMAGE_NAME .; then
        echo -e "${GREEN}✓ Build successful${NC}"
    else
        echo -e "${RED}✗ Build failed${NC}"
        exit 1
    fi
fi

# Stop and remove existing container if it exists
if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo -e "${YELLOW}Stopping and removing existing container...${NC}"
    docker stop $CONTAINER_NAME >/dev/null 2>&1
    docker rm $CONTAINER_NAME >/dev/null 2>&1
fi

echo -e "${GREEN}Starting Docker container...${NC}"
if docker run -d --name $CONTAINER_NAME -p $PORT_5000:$PORT_5000 -p $PORT_8765:$PORT_8765 $IMAGE_NAME; then
    echo -e "${GREEN}✓ Container started${NC}"
else
    echo -e "${RED}✗ Failed to start container${NC}"
    exit 1
fi

# Wait a moment for the server to start
echo -e "${YELLOW}Waiting for server to start...${NC}"
sleep 2

# Open browser
echo -e "${GREEN}Opening browser at $URL${NC}"
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    open $URL
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    if command -v xdg-open > /dev/null; then
        xdg-open $URL
    elif command -v gnome-open > /dev/null; then
        gnome-open $URL
    else
        echo -e "${YELLOW}Please open $URL manually${NC}"
    fi
else
    echo -e "${YELLOW}Please open $URL manually${NC}"
fi

echo -e "${GREEN}✓ Application is running!${NC}"
echo -e "Container name: ${CONTAINER_NAME}"
echo -e "To view logs: ${YELLOW}docker logs -f ${CONTAINER_NAME}${NC}"
echo -e "To stop: ${YELLOW}docker stop ${CONTAINER_NAME}${NC}"