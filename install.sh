#!/bin/bash
#
# openaur Installer
# One-command setup for openaur - Personal AI Assistant
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Banner
echo -e "${BLUE}"
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                                                            ║"
echo "║   ██████╗ ██████╗ ███████╗███╗   ██╗ █████╗ ██╗   ██╗██████╗  ║"
echo "║  ██╔═══██╗██╔══██╗██╔════╝████╗  ██║██╔══██╗██║   ██║██╔══██╗ ║"
echo "║  ██║   ██║██████╔╝█████╗  ██╔██╗ ██║███████║██║   ██║██████╔╝ ║"
echo "║  ██║   ██║██╔═══╝ ██╔══╝  ██║╚██╗██║██╔══██║██║   ██║██╔══██╗ ║"
echo "║  ╚██████╔╝██║     ███████╗██║ ╚████║██║  ██║╚██████╔╝██║  ██║ ║"
echo "║   ╚═════╝ ╚═╝     ╚══════╝╚═╝  ╚═══╝╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝ ║"
echo "║                                                            ║"
echo "║              Personal AI Assistant Installer               ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""

# Check prerequisites
echo -e "${BLUE}Checking prerequisites...${NC}"

if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    echo "Please install Docker first: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Error: Docker Compose is not installed${NC}"
    echo "Please install Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

echo -e "${GREEN}✓ Docker found${NC}"
echo -e "${GREEN}✓ Docker Compose found${NC}"
echo ""

# Check if running in existing directory
if [ -f "docker-compose.yml" ]; then
    echo -e "${YELLOW}⚠️  openaur appears to be already installed in this directory${NC}"
    read -p "Do you want to update/reset instead? (y/N): " update_choice
    if [[ $update_choice =~ ^[Yy]$ ]]; then
        echo ""
        echo -e "${BLUE}Updating openaur...${NC}"
        docker-compose pull
        docker-compose up -d
        echo ""
        echo -e "${GREEN}✓ openaur updated!${NC}"
        echo ""
        echo "Test it: make test"
        echo "Or visit: http://localhost:8000"
        exit 0
    else
        echo "Aborting installation."
        exit 0
    fi
fi

# Get OpenRouter API Key
echo -e "${BLUE}Configuration${NC}"
echo "openaur needs an OpenRouter API key to access AI models."
echo "You can get a free key at: https://openrouter.ai/keys"
echo ""

while true; do
    read -s -p "Enter your OpenRouter API key: " api_key
    echo ""
    
    if [ -z "$api_key" ]; then
        echo -e "${RED}Error: API key is required${NC}"
        continue
    fi
    
    # Basic validation (should start with sk-or-)
    if [[ ! $api_key =~ ^sk-or- ]]; then
        echo -e "${YELLOW}⚠️  This doesn't look like an OpenRouter key (should start with 'sk-or-')${NC}"
        read -p "Continue anyway? (y/N): " force_continue
        if [[ ! $force_continue =~ ^[Yy]$ ]]; then
            continue
        fi
    fi
    
    break
done

echo ""
echo -e "${BLUE}Installing openaur...${NC}"
echo ""

# Clone repository
echo "→ Cloning repository..."
if ! git clone https://github.com/mattstyles333/openaur.git; then
    echo -e "${RED}Error: Failed to clone repository${NC}"
    exit 1
fi

cd openaur

# Create .env file
echo "→ Creating configuration..."
cat > .env << EOF
# OpenRouter API Key
OPENROUTER_API_KEY=$api_key

# Optional settings
# DEBUG=false
# OPENMEMORY_DB_PATH=./data/openmemory.db
EOF

# Build and start
echo "→ Building Docker images (this may take a few minutes)..."
docker-compose build --quiet

echo "→ Starting openaur..."
docker-compose up -d

# Wait for health check
echo "→ Waiting for services to start..."
sleep 5

# Test
echo "→ Testing installation..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                                                        ║${NC}"
    echo -e "${GREEN}║   ✓ openaur installed successfully!                  ║${NC}"
    echo -e "${GREEN}║                                                        ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. cd openaura"
    echo "  2. make test          # Verify it's working"
    echo "  3. make chat MSG=\"Hello\"  # First conversation"
    echo "  4. make crawl BINARY=git  # Register a CLI tool"
    echo ""
    echo "Web UI: http://localhost:8000"
    echo "Documentation: https://mattstyles333.github.io/openaur/"
    echo ""
    echo "To stop: docker-compose down"
    echo "To start again: docker-compose up -d"
    echo ""
else
    echo ""
    echo -e "${YELLOW}⚠️  Installation complete, but health check failed${NC}"
    echo "This might be normal on first startup. Try:"
    echo "  cd openaura && make test"
    echo ""
    echo "If it still fails, check logs: docker-compose logs"
    echo ""
fi
