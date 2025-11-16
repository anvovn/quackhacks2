#!/bin/bash

# Configuration
IMAGE_NAME="my-game"
CONTAINER_NAME="my-game-container"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to display usage
show_usage() {
    echo -e "${BLUE}Docker Management Script${NC}"
    echo -e "Usage: $0 [option]"
    echo ""
    echo -e "Options:"
    echo -e "  ${GREEN}s${NC}  - Stop the running container"
    echo -e "  ${YELLOW}c${NC}  - Cleanup (stop container and delete image)"
    echo -e "  ${BLUE}h${NC}  - Show this help message"
    echo ""
}

# Function to stop container
stop_container() {
    if docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        echo -e "${YELLOW}Stopping container '${CONTAINER_NAME}'...${NC}"
        docker stop $CONTAINER_NAME
        echo -e "${GREEN}✓ Container stopped${NC}"
    else
        echo -e "${YELLOW}Container '${CONTAINER_NAME}' is not running${NC}"
    fi
    
    # Check if stopped container exists and offer to remove it
    if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        echo -e "${YELLOW}Removing stopped container...${NC}"
        docker rm $CONTAINER_NAME
        echo -e "${GREEN}✓ Container removed${NC}"
    fi
}

# Function to cleanup everything
cleanup() {
    echo -e "${RED}Starting cleanup...${NC}"
    
    # Stop and remove container
    if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        echo -e "${YELLOW}Stopping and removing container '${CONTAINER_NAME}'...${NC}"
        docker stop $CONTAINER_NAME >/dev/null 2>&1
        docker rm $CONTAINER_NAME >/dev/null 2>&1
        echo -e "${GREEN}✓ Container removed${NC}"
    else
        echo -e "${YELLOW}No container to remove${NC}"
    fi
    
    # Remove image
    if docker image inspect $IMAGE_NAME >/dev/null 2>&1; then
        echo -e "${YELLOW}Removing image '${IMAGE_NAME}'...${NC}"
        docker rmi -f $IMAGE_NAME
        echo -e "${GREEN}✓ Image deleted${NC}"
    else
        echo -e "${YELLOW}Image '${IMAGE_NAME}' does not exist${NC}"
    fi
    
    echo -e "${GREEN}✓ Cleanup complete${NC}"
}

# Main script logic
if [ $# -eq 0 ]; then
    show_usage
    exit 0
fi

case "$1" in
    s|S)
        stop_container
        ;;
    c|C)
        echo -e "${RED}WARNING: This will delete the Docker image. You'll need to rebuild it.${NC}"
        read -p "Are you sure? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            cleanup
        else
            echo -e "${YELLOW}Cleanup cancelled${NC}"
        fi
        ;;
    h|H|--help)
        show_usage
        ;;
    *)
        echo -e "${RED}Invalid option: $1${NC}"
        echo ""
        show_usage
        exit 1
        ;;
esac