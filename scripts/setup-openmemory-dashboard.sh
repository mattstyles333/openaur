#!/bin/bash
# Build and run OpenMemory dashboard from source

set -e

DASHBOARD_DIR="/tmp/openmemory-dashboard"

# Clone OpenMemory repo if not exists
if [ ! -d "$DASHBOARD_DIR" ]; then
    echo "Cloning OpenMemory repository..."
    git clone https://github.com/CaviraOSS/OpenMemory.git "$DASHBOARD_DIR"
fi

# Build the dashboard image
cd "$DASHBOARD_DIR/dashboard"
echo "Building OpenMemory dashboard image..."
docker build -t openmemory-dashboard:latest .

# Run the dashboard
echo "Starting OpenMemory dashboard on port 8001..."
docker run -d \
    --name openmemory-dashboard \
    --network openaur_openaura-network \
    -p 8001:8080 \
    -e OPENMEMORY_API_URL=http://openaura:8000/memory \
    openmemory-dashboard:latest

echo "✅ OpenMemory dashboard available at http://localhost:8001"
