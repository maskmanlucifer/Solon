#!/usr/bin/env python3
"""
Application Launcher - launches apps and opens projects
"""

import subprocess
import os
from pathlib import Path
from typing import Optional, List


def launch_app(app_name: str, args: List[str] = None) -> bool:
    """Launch an application by name"""
    if args is None:
        args = []
    
    try:
        # Use macOS 'open' command
        cmd = ['open', '-a', app_name]
        if args:
            cmd.extend(args)
        subprocess.run(cmd, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to launch {app_name}: {e}")
        return False
    except Exception as e:
        print(f"Error launching {app_name}: {e}")
        return False


def open_repo_in_editor(editor: str, repo_path: str) -> bool:
    """Open a repository in a specific editor"""
    repo_path = os.path.expanduser(repo_path)
    
    if not os.path.exists(repo_path):
        print(f"Repository path does not exist: {repo_path}")
        return False
    
    # Normalize editor name
    editor_map = {
        "cursor": "Cursor",
        "vscode": "Visual Studio Code",
        "code": "Visual Studio Code",
        "vs code": "Visual Studio Code"
    }
    
    app_name = editor_map.get(editor.lower(), editor)
    
    try:
        # Launch editor with repo path
        subprocess.run(['open', '-a', app_name, repo_path], check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to open {repo_path} in {app_name}: {e}")
        return False


def find_repo_in_desktop(repo_name: str) -> Optional[str]:
    """Find a repository in Desktop subtree"""
    desktop_path = os.path.expanduser("~/Desktop")
    
    if not os.path.exists(desktop_path):
        return None
    
    # Search recursively
    for root, dirs, files in os.walk(desktop_path):
        if repo_name in dirs:
            return os.path.join(root, repo_name)
    
    return None


def open_cursor_with_repo(repo_name: str) -> bool:
    """Open Cursor with a specific repo from Desktop"""
    repo_path = find_repo_in_desktop(repo_name)
    if repo_path:
        return open_repo_in_editor("Cursor", repo_path)
    else:
        print(f"Repository '{repo_name}' not found in Desktop")
        return False


def open_vscode_with_repo(repo_name: str) -> bool:
    """Open VSCode with a specific repo from Desktop"""
    repo_path = find_repo_in_desktop(repo_name)
    if repo_path:
        return open_repo_in_editor("Visual Studio Code", repo_path)
    else:
        print(f"Repository '{repo_name}' not found in Desktop")
        return False


def get_apps_with_login_items() -> List[str]:
    """Get list of apps that are set to open on login"""
    script = '''
    tell application "System Events"
        set loginItems to name of every login item
        return loginItems
    end tell
    '''
    try:
        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True,
            text=True,
            check=True
        )
        # Parse result (simplified)
        return []
    except:
        return []


def is_app_running(app_name: str) -> bool:
    """Check if an application is currently running"""
    script = f'''
    tell application "System Events"
        return (name of processes) contains "{app_name}"
    end tell
    '''
    try:
        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True,
            text=True,
            check=True
        )
        return "true" in result.stdout.lower()
    except:
        return False

