#!/usr/bin/env python3
"""
Window Manager for macOS - handles window manipulation using AppleScript
"""

import subprocess
import json
import os
from typing import List, Dict, Optional, Tuple


def run_applescript(script: str) -> str:
    """Execute AppleScript and return output"""
    try:
        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"AppleScript error: {e.stderr}")
        return ""


def get_connected_displays() -> List[Dict]:
    """Get list of connected displays"""
    script = '''
    tell application "System Events"
        set displays to {}
        repeat with d in (every desktop)
            set displayName to name of d
            set displayBounds to bounds of d
            set end of displays to {displayName, displayBounds}
        end repeat
        return displays
    end tell
    '''
    result = run_applescript(script)
    displays = []
    # Parse display info (simplified - actual parsing would be more complex)
    return displays


def get_app_windows(app_name: str) -> List[Dict]:
    """Get all windows for a specific application"""
    script = f'''
    tell application "System Events"
        tell process "{app_name}"
            set windowList to {{}}
            repeat with w in windows
                try
                    set windowInfo to {{name of w, id of w, position of w, size of w}}
                    set end of windowList to windowInfo
                end try
            end repeat
            return windowList
        end tell
    end tell
    '''
    result = run_applescript(script)
    # Parse window info
    return []


def move_windows_to_display(app_name: str, display_num: int, maximize: bool = False) -> bool:
    """Move all windows of an app to a specific display"""
    script = f'''
    tell application "{app_name}"
        activate
        set windowCount to count of windows
        if windowCount > 0 then
            repeat with w in windows
                try
                    set bounds of w to {{100, 100, 1200, 800}}
                end try
            end repeat
        end if
    end tell
    '''
    
    if maximize:
        script += f'''
    tell application "{app_name}"
        repeat with w in windows
            try
                tell application "System Events"
                    tell process "{app_name}"
                        set value of attribute "AXFullScreen" of w to true
                    end tell
                end tell
            end try
        end repeat
    end tell
    '''
    
    result = run_applescript(script)
    return result != ""


def maximize_window(app_name: str) -> bool:
    """Maximize all windows of an application"""
    script = f'''
    tell application "System Events"
        tell process "{app_name}"
            repeat with w in windows
                try
                    set value of attribute "AXFullScreen" of w to true
                end try
            end repeat
        end tell
    end tell
    '''
    result = run_applescript(script)
    return result != ""


def minimize_window(app_name: str) -> bool:
    """Minimize all windows of an application"""
    script = f'''
    tell application "System Events"
        tell process "{app_name}"
            repeat with w in windows
                try
                    set minimized of w to true
                end try
            end repeat
        end tell
    end tell
    '''
    result = run_applescript(script)
    return result != ""


def close_windows_except(app_name: str, repo_path: str) -> bool:
    """Close all windows except those containing the specified repo path"""
    script = f'''
    tell application "{app_name}"
        repeat with w in windows
            try
                set windowPath to path of w
                if windowPath does not contain "{repo_path}" then
                    close w
                end if
            on error
                try
                    set windowTitle to name of w
                    if windowTitle does not contain "{os.path.basename(repo_path)}" then
                        close w
                    end if
                end try
            end try
        end repeat
    end tell
    '''
    result = run_applescript(script)
    return result != ""


def get_window_info(app_name: str) -> List[Dict]:
    """Get information about all windows of an application"""
    return get_app_windows(app_name)


def move_window_to_display_by_index(app_name: str, window_index: int, display_num: int) -> bool:
    """Move a specific window by index to a display"""
    script = f'''
    tell application "{app_name}"
        if (count of windows) > {window_index} then
            set targetWindow to item {window_index + 1} of windows
            set bounds of targetWindow to {{100, 100, 1200, 800}}
        end if
    end tell
    '''
    result = run_applescript(script)
    return result != ""


def apply_window_behavior(app_name: str, behavior: str) -> bool:
    """Apply a behavior (maximize, minimize, keep_same) to all windows of an app"""
    if behavior == "maximize":
        return maximize_window(app_name)
    elif behavior == "minimize":
        return minimize_window(app_name)
    elif behavior == "keep_same":
        return True  # No action needed
    return False

