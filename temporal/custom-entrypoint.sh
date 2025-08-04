#!/bin/bash
set -e

echo "Starting Temporal with custom configuration..."

# Get the container's IP address on the first network interface
CONTAINER_IP=$(hostname -i | awk '{print $1}')
echo "Container IP: $CONTAINER_IP"

# Export required environment variables
export TEMPORAL_BROADCAST_ADDRESS="${TEMPORAL_BROADCAST_ADDRESS:-$CONTAINER_IP}"
export BIND_ON_IP="0.0.0.0"

echo "Setting TEMPORAL_BROADCAST_ADDRESS to: $TEMPORAL_BROADCAST_ADDRESS"

# If config doesn't exist, copy template
if [ ! -f /etc/temporal/config/docker.yaml ]; then
    cp /etc/temporal/config/config_template.yaml /etc/temporal/config/docker.yaml
fi

# Replace bindOnIP in the config to bind to all interfaces
sed -i 's/bindOnIP: .*/bindOnIP: 0.0.0.0/g' /etc/temporal/config/docker.yaml

# Set broadcast address to the container IP
sed -i "s/broadcastAddress: .*/broadcastAddress: $TEMPORAL_BROADCAST_ADDRESS/g" /etc/temporal/config/docker.yaml

# Execute the original entrypoint
exec /etc/temporal/entrypoint.sh "$@"