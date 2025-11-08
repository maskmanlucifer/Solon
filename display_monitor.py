#!/usr/bin/env python3
"""
Display Monitor - monitors display connections and triggers app movement rules
"""

import time
import json
import os
from typing import Dict, List, Callable
from pathlib import Path
from window_manager import move_windows_to_display, apply_window_behavior


class DisplayMonitor:
    def __init__(self, config_path: str = None):
        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(__file__),
                'config',
                'app_rules.json'
            )
        self.config_path = config_path
        self.last_display_count = 0
        self.callbacks: List[Callable] = []
    
    def load_config(self) -> Dict:
        """Load app rules configuration"""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                "startup": {"keep_open": [], "close_others": True},
                "display_rules": {"w1": [], "w2": [], "laptop": []}
            }
    
    def get_display_count(self) -> int:
        """Get current number of connected displays"""
        script = '''
        tell application "System Events"
            return count of (every desktop)
        end tell
        '''
        try:
            import subprocess
            result = subprocess.run(
                ['osascript', '-e', script],
                capture_output=True,
                text=True,
                check=True
            )
            return int(result.stdout.strip())
        except:
            return 1
    
    def check_display_change(self):
        """Check if display count has changed"""
        current_count = self.get_display_count()
        if current_count != self.last_display_count:
            if current_count > self.last_display_count:
                # New display connected
                self.on_display_connected(current_count)
            self.last_display_count = current_count
        return current_count
    
    def on_display_connected(self, display_count: int):
        """Handle display connection - apply rules"""
        config = self.load_config()
        display_rules = config.get("display_rules", {})
        
        # Apply rules for W1 (display 2, index 1)
        if display_count >= 2:
            w1_rules = display_rules.get("w1", [])
            for rule in w1_rules:
                app_name = rule.get("app")
                behavior = rule.get("behavior", "keep_same")
                maximize = rule.get("maximize", False)
                
                if app_name:
                    move_windows_to_display(app_name, 1, maximize)
                    if not maximize:
                        apply_window_behavior(app_name, behavior)
        
        # Apply rules for W2 (display 3, index 2)
        if display_count >= 3:
            w2_rules = display_rules.get("w2", [])
            for rule in w2_rules:
                app_name = rule.get("app")
                behavior = rule.get("behavior", "keep_same")
                maximize = rule.get("maximize", False)
                
                if app_name:
                    move_windows_to_display(app_name, 2, maximize)
                    if not maximize:
                        apply_window_behavior(app_name, behavior)
        
        # Trigger callbacks
        for callback in self.callbacks:
            callback(display_count)
    
    def start_monitoring(self, interval: float = 2.0):
        """Start monitoring display connections"""
        self.last_display_count = self.get_display_count()
        
        while True:
            try:
                self.check_display_change()
                time.sleep(interval)
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Display monitor error: {e}")
                time.sleep(interval)
    
    def register_callback(self, callback: Callable):
        """Register a callback to be called when displays change"""
        self.callbacks.append(callback)

