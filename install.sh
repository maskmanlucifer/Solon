#!/bin/bash
# Installation script for Solon

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PLIST_FILE="$SCRIPT_DIR/com.solon.daemon.plist"
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"
INSTALLED_PLIST="$LAUNCH_AGENTS_DIR/com.solon.daemon.plist"

echo "Installing Solon..."

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not found."
    exit 1
fi

# Check if PortAudio is installed (required for pyaudio)
if ! brew list portaudio &> /dev/null; then
    echo "PortAudio not found. Installing PortAudio (required for voice recognition)..."
    if ! command -v brew &> /dev/null; then
        echo "Error: Homebrew is required to install PortAudio."
        echo "Please install Homebrew first: https://brew.sh"
        exit 1
    fi
    brew install portaudio
fi

# Install Python dependencies
echo "Installing Python dependencies..."
pip3 install -r "$SCRIPT_DIR/requirements.txt"

# Make scripts executable
echo "Making scripts executable..."
chmod +x "$SCRIPT_DIR/solon_daemon.py"
chmod +x "$SCRIPT_DIR/solon_cli.py"
chmod +x "$SCRIPT_DIR/solon_gui.py"
chmod +x "$SCRIPT_DIR/voice_listener.py"

# Update plist file with correct paths
echo "Updating launchd plist file..."
python3_path=$(which python3)
sed "s|/usr/bin/python3|$python3_path|g" "$PLIST_FILE" | \
sed "s|/Users/as/Desktop/maskman/Solon|$SCRIPT_DIR|g" > "$INSTALLED_PLIST"

# Create logs directory
mkdir -p "$HOME/Library/Logs"

# Load the launchd service
echo "Loading launchd service..."
if launchctl list | grep -q "com.solon.daemon"; then
    echo "Unloading existing service..."
    launchctl unload "$INSTALLED_PLIST" 2>/dev/null || true
fi

launchctl load "$INSTALLED_PLIST"

echo ""
echo "✓ Solon installed successfully!"
echo ""
echo "To start the daemon manually:"
echo "  launchctl start com.solon.daemon"
echo ""
echo "To stop the daemon:"
echo "  launchctl stop com.solon.daemon"
echo ""
echo "To uninstall:"
echo "  launchctl unload $INSTALLED_PLIST"
echo "  rm $INSTALLED_PLIST"
echo ""
echo "Open the GUI configuration:"
echo "  python3 $SCRIPT_DIR/solon_gui.py"

