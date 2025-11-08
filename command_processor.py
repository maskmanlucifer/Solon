#!/usr/bin/env python3
"""
Command Processor - parses commands and executes behaviors
"""

import re
from typing import Dict, Any, Optional
from behavior_registry import BehaviorRegistry
from window_manager import (
    move_windows_to_display,
    maximize_window,
    minimize_window,
    close_windows_except,
    apply_window_behavior
)
from app_launcher import (
    launch_app,
    open_repo_in_editor,
    open_cursor_with_repo,
    open_vscode_with_repo
)
from port_manager import kill_port


class CommandProcessor:
    def __init__(self, registry: BehaviorRegistry = None):
        if registry is None:
            registry = BehaviorRegistry()
        self.registry = registry
    
    def process_command(self, command: str) -> Dict[str, Any]:
        """Process a command and return result"""
        command = command.strip()
        
        if not command:
            return {"success": False, "error": "Empty command"}
        
        # Try to match with registered behaviors
        match = self.registry.match_command(command)
        
        if match:
            return self.execute_behavior(match['behavior'], match.get('params', {}))
        
        # Try direct command parsing as fallback
        return self.parse_direct_command(command)
    
    def execute_behavior(self, behavior: Dict, params: Dict) -> Dict[str, Any]:
        """Execute a behavior's actions"""
        actions = behavior.get('actions', [])
        results = []
        
        for action in actions:
            action_type = action.get('type')
            result = None
            
            if action_type == 'launch_app':
                app = self._substitute_params(action.get('app', ''), params)
                args = [self._substitute_params(arg, params) for arg in action.get('args', [])]
                result = launch_app(app, args)
            
            elif action_type == 'move_windows':
                app = self._substitute_params(action.get('app', ''), params)
                display = action.get('display', 1)
                maximize = action.get('maximize', False)
                result = move_windows_to_display(app, display, maximize)
            
            elif action_type == 'close_windows_except':
                app = self._substitute_params(action.get('app', ''), params)
                repo_path = self._substitute_params(action.get('repo_path', ''), params)
                result = close_windows_except(app, repo_path)
            
            elif action_type == 'kill_port':
                port_str = self._substitute_params(action.get('port', ''), params)
                try:
                    port = int(port_str)
                    result = kill_port(port)
                except ValueError:
                    result = False
            
            results.append(result)
        
        success = all(results) if results else False
        return {
            "success": success,
            "behavior": behavior.get('name'),
            "results": results
        }
    
    def parse_direct_command(self, command: str) -> Dict[str, Any]:
        """Parse direct commands (fallback for unregistered commands)"""
        command_lower = command.lower()
        
        # Open cursor/vscode with repo
        if 'open cursor' in command_lower or 'open vscode' in command_lower:
            repo_match = re.search(r'(?:cursor|vscode|code).*?(\w+)', command_lower)
            if repo_match:
                repo_name = repo_match.group(1)
                if 'cursor' in command_lower:
                    result = open_cursor_with_repo(repo_name)
                else:
                    result = open_vscode_with_repo(repo_name)
                return {"success": result, "command": "open_repo"}
        
        # Move windows
        if 'move' in command_lower:
            app_match = re.search(r'move\s+(\w+)', command_lower)
            display_match = re.search(r'(w\d+|display\s*\d+)', command_lower)
            
            if app_match and display_match:
                app = app_match.group(1).capitalize()
                display_str = display_match.group(1)
                display_num = 1
                if 'w1' in display_str or 'display 1' in display_str:
                    display_num = 1
                elif 'w2' in display_str or 'display 2' in display_str:
                    display_num = 2
                
                maximize = 'maximize' in command_lower
                result = move_windows_to_display(app, display_num, maximize)
                return {"success": result, "command": "move_windows"}
        
        # Close port
        if 'close port' in command_lower or 'kill port' in command_lower:
            port_match = re.search(r'port\s*(\d+)', command_lower)
            if port_match:
                port = int(port_match.group(1))
                result = kill_port(port)
                return {"success": result, "command": "kill_port"}
        
        # Close windows except repo
        if 'close' in command_lower and 'except' in command_lower:
            app_match = re.search(r'close\s+(\w+)', command_lower)
            repo_match = re.search(r'except\s+(\w+)', command_lower)
            
            if app_match and repo_match:
                app = app_match.group(1).capitalize()
                repo_name = repo_match.group(1)
                # Try to find repo path
                from app_launcher import find_repo_in_desktop
                repo_path = find_repo_in_desktop(repo_name)
                if repo_path:
                    result = close_windows_except(app, repo_path)
                    return {"success": result, "command": "close_windows_except"}
        
        return {"success": False, "error": f"Unknown command: {command}"}
    
    def _substitute_params(self, text: str, params: Dict) -> str:
        """Substitute parameters in text"""
        result = text
        for key, value in params.items():
            result = result.replace(f'{{{key}}}', str(value))
        return result

