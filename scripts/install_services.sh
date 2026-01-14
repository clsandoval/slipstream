#!/bin/bash
# Install Slipstream systemd services

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "Installing Slipstream services..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root (sudo)"
    exit 1
fi

# Create swim user if doesn't exist
if ! id "swim" &>/dev/null; then
    echo "Creating swim user..."
    useradd -m -G audio swim
fi

# Create data directory
mkdir -p /home/swim/.slipstream
chown swim:swim /home/swim/.slipstream

# Copy project to /opt/slipstream
if [ "$PROJECT_DIR" != "/opt/slipstream" ]; then
    echo "Copying project to /opt/slipstream..."
    mkdir -p /opt/slipstream
    cp -r "$PROJECT_DIR"/* /opt/slipstream/
    chown -R swim:swim /opt/slipstream
fi

# Install systemd service
echo "Installing STT service..."
cp "$PROJECT_DIR/services/slipstream-stt.service" /etc/systemd/system/

# Reload systemd
systemctl daemon-reload

# Enable service
systemctl enable slipstream-stt.service

echo "Installation complete!"
echo ""
echo "To start the STT service:"
echo "  sudo systemctl start slipstream-stt"
echo ""
echo "To view logs:"
echo "  journalctl -u slipstream-stt -f"
