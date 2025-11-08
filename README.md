# Solon

A lightweight personal automation assistant for macOS that listens to voice commands, launches apps, opens projects, and arranges windows across connected displays.

## Features

- **Daemon Service**: Runs automatically on macOS startup
- **Voice Commands**: Optional voice recognition support
- **CLI Interface**: Command-line interface for quick commands
- **GUI Configuration**: Native macOS GUI for configuring app rules and behaviors
- **Window Management**: Move and organize windows across multiple displays
- **Application Launching**: Launch apps and open projects in editors
- **Port Management**: Kill processes running on specific ports
- **Display Monitoring**: Automatically apply rules when displays connect/disconnect
- **Startup Management**: Control which apps stay open on login

## Installation

### Prerequisites

- macOS (tested on macOS 10.15+)
- Python 3.8 or higher
- pip
- **PortAudio** (required for voice recognition): `brew install portaudio`

### Setup

1. **Clone or navigate to the Solon directory**:
   ```bash
   cd /Users/as/Desktop/maskman/Solon
   ```

2. **Install PortAudio** (required for `pyaudio`):
   ```bash
   brew install portaudio
   ```

3. **Install Python dependencies**:
   ```bash
   pip3 install -r requirements.txt
   ```

4. **Make scripts executable**:
   ```bash
   chmod +x solon_daemon.py solon_cli.py solon_gui.py voice_listener.py
   ```

5. **Update the launchd plist file**:
   Edit `com.solon.daemon.plist` and update the paths to match your system:
   - Update the Python path in `ProgramArguments` if needed
   - Update the Solon directory path

6. **Install the launchd service**:
   ```bash
   cp com.solon.daemon.plist ~/Library/LaunchAgents/
   launchctl load ~/Library/LaunchAgents/com.solon.daemon.plist
   ```

   To unload:
   ```bash
   launchctl unload ~/Library/LaunchAgents/com.solon.daemon.plist
   ```

## Usage

### GUI Configuration

Launch the GUI to configure app rules:

```bash
python3 solon_gui.py
```

The GUI allows you to:
- **Startup Apps**: Select which apps to keep open on login (if they have "open on login" setting)
- **Display Rules**: Configure which apps move to W1, W2, or stay on laptop when displays connect
- **Window Behaviors**: Set maximize, minimize, or keep same for each app
- **Add/Remove Rules**: Use dropdowns to add new rules or modify existing ones

### CLI Commands

Use the CLI to send commands to the daemon:

```bash
python3 solon_cli.py "open cursor lucifer"
python3 solon_cli.py "move cursor to w1"
python3 solon_cli.py "close port 3000"
python3 solon_cli.py "close cursor except lucifer"
```

### Voice Commands (Optional)

Start the voice listener:

```bash
python3 voice_listener.py
```

Say commands like:
- "Open cursor lucifer"
- "Move cursor to w1"
- "Close port 3000"

The default wake word is "solon". You can change it:
```bash
python3 voice_listener.py "hey solon"
```

### Supported Commands

#### Application Launching
- `open cursor <repo_name>` - Open Cursor with repo from Desktop
- `open vscode <repo_name>` - Open VSCode with repo from Desktop
- `open code <repo_name>` - Alias for VSCode

#### Window Management
- `move <app> to w1` - Move app windows to display 1 (W1)
- `move <app> to w2` - Move app windows to display 2 (W2)
- `move <app> to w1 maximize` - Move and maximize on W1
- `move cursor to display 1` - Alternative syntax

#### Port Management
- `close port <port_number>` - Kill all processes on port
- `kill port <port_number>` - Alias for close port

#### Window Closing
- `close <app> except <repo>` - Close all windows except those with repo

## Configuration Files

### behaviors.yaml

Defines command patterns and their actions. Located in `config/behaviors.yaml`.

Example:
```yaml
behaviors:
  - name: "open_cursor_repo"
    pattern: "open cursor.*{repo}"
    actions:
      - type: launch_app
        app: "Cursor"
        args: ["{repo}"]
```

### app_rules.json

Stores GUI-configured rules. Located in `config/app_rules.json`.

Structure:
```json
{
  "startup": {
    "keep_open": ["Cursor", "Terminal"],
    "close_others": true
  },
  "display_rules": {
    "w1": [
      {
        "app": "Cursor",
        "behavior": "maximize",
        "maximize": true
      }
    ],
    "w2": [],
    "laptop": []
  }
}
```

## Architecture

### Core Components

- **solon_daemon.py**: Main daemon process with socket communication
- **solon_cli.py**: Command-line interface client
- **solon_gui.py**: Native macOS GUI for configuration
- **window_manager.py**: Window manipulation using AppleScript
- **app_launcher.py**: Application launching and project opening
- **port_manager.py**: Port and process management
- **behavior_registry.py**: Behavior loading and management
- **command_processor.py**: Command parsing and execution
- **display_monitor.py**: Display connection monitoring
- **voice_listener.py**: Optional voice recognition

### Communication

The daemon listens on a Unix domain socket: `/tmp/solon.sock`

Commands are sent as plain text strings and responses are JSON.

## Troubleshooting

### Daemon not running

Check if the daemon is running:
```bash
ps aux | grep solon_daemon
```

Check logs:
```bash
tail -f ~/Library/Logs/solon_daemon.log
tail -f ~/Library/Logs/solon_daemon.err.log
```

### Permission issues

The daemon needs Accessibility permissions to control windows:
1. System Preferences → Security & Privacy → Privacy → Accessibility
2. Add Python or Terminal to allowed apps

### Voice recognition not working

- Ensure microphone permissions are granted
- Check that `pyaudio` is installed correctly
- On macOS, you may need to install PortAudio: `brew install portaudio`

### Installation errors with pyobjc-framework-Metal

If you encounter build errors with `pyobjc-framework-Metal` (often due to macOS SDK compatibility), the project only requires `pyobjc-framework-Cocoa` for the GUI. The `requirements.txt` has been updated to install only the necessary frameworks. If you still encounter issues, you can install dependencies individually:

```bash
pip3 install pyobjc-core pyobjc-framework-Cocoa pyyaml speechrecognition pyaudio
```

## Development

### Project Structure

```
Solon/
├── solon_daemon.py          # Main daemon process
├── solon_cli.py             # CLI client
├── solon_gui.py             # GUI configuration app
├── window_manager.py        # Window management
├── app_launcher.py          # App launching
├── port_manager.py          # Port management
├── behavior_registry.py     # Behavior system
├── display_monitor.py       # Display monitoring
├── voice_listener.py        # Voice recognition
├── command_processor.py     # Command parsing/execution
├── config/
│   ├── behaviors.yaml       # Behavior definitions
│   └── app_rules.json       # GUI-configured rules
├── com.solon.daemon.plist   # Launchd service file
├── requirements.txt         # Python dependencies
└── README.md                # This file
```

## License

MIT License

## Contributing

Contributions welcome! Please feel free to submit a Pull Request.
