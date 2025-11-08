#!/usr/bin/env python3
"""
Behavior Registry - loads and manages behaviors from config files
"""

import yaml
import json
import os
import re
from typing import Dict, List, Optional, Any
from pathlib import Path


class BehaviorRegistry:
    def __init__(self, behaviors_file: str = None, app_rules_file: str = None):
        if behaviors_file is None:
            behaviors_file = os.path.join(
                os.path.dirname(__file__),
                'config',
                'behaviors.yaml'
            )
        if app_rules_file is None:
            app_rules_file = os.path.join(
                os.path.dirname(__file__),
                'config',
                'app_rules.json'
            )
        
        self.behaviors_file = behaviors_file
        self.app_rules_file = app_rules_file
        self.behaviors: List[Dict] = []
        self.app_rules: Dict = {}
        self.load_behaviors()
        self.load_app_rules()
    
    def load_behaviors(self):
        """Load behaviors from YAML file"""
        try:
            with open(self.behaviors_file, 'r') as f:
                data = yaml.safe_load(f)
                self.behaviors = data.get('behaviors', [])
        except FileNotFoundError:
            print(f"Behaviors file not found: {self.behaviors_file}")
            self.behaviors = []
        except Exception as e:
            print(f"Error loading behaviors: {e}")
            self.behaviors = []
    
    def load_app_rules(self):
        """Load app rules from JSON file"""
        try:
            with open(self.app_rules_file, 'r') as f:
                self.app_rules = json.load(f)
        except FileNotFoundError:
            print(f"App rules file not found: {self.app_rules_file}")
            self.app_rules = {
                "startup": {"keep_open": [], "close_others": True},
                "display_rules": {"w1": [], "w2": [], "laptop": []}
            }
        except Exception as e:
            print(f"Error loading app rules: {e}")
            self.app_rules = {
                "startup": {"keep_open": [], "close_others": True},
                "display_rules": {"w1": [], "w2": [], "laptop": []}
            }
    
    def save_app_rules(self):
        """Save app rules to JSON file"""
        try:
            with open(self.app_rules_file, 'w') as f:
                json.dump(self.app_rules, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving app rules: {e}")
            return False
    
    def match_command(self, command: str) -> Optional[Dict]:
        """Match a command string to a behavior pattern"""
        command_lower = command.lower()
        
        for behavior in self.behaviors:
            pattern = behavior.get('pattern', '')
            if not pattern:
                continue
            
            # Extract parameters from pattern (e.g., {repo}, {port})
            param_pattern = pattern.replace('{repo}', r'(.+?)').replace('{port}', r'(\d+)')
            param_pattern = param_pattern.replace('.*', '.*?')
            
            # Try to match
            match = re.search(param_pattern, command_lower, re.IGNORECASE)
            if match:
                # Extract parameters
                params = {}
                if '{repo}' in pattern:
                    params['repo'] = match.group(1) if match.groups() else None
                if '{port}' in pattern:
                    params['port'] = match.group(1) if match.groups() else None
                
                return {
                    'behavior': behavior,
                    'params': params
                }
        
        return None
    
    def get_startup_rules(self) -> Dict:
        """Get startup app rules"""
        return self.app_rules.get('startup', {})
    
    def get_display_rules(self, display: str) -> List[Dict]:
        """Get rules for a specific display (w1, w2, laptop)"""
        display_rules = self.app_rules.get('display_rules', {})
        return display_rules.get(display, [])
    
    def add_display_rule(self, display: str, app: str, behavior: str = "keep_same", maximize: bool = False):
        """Add a display rule"""
        if 'display_rules' not in self.app_rules:
            self.app_rules['display_rules'] = {}
        
        if display not in self.app_rules['display_rules']:
            self.app_rules['display_rules'][display] = []
        
        rule = {
            "app": app,
            "behavior": behavior,
            "maximize": maximize
        }
        
        # Check if rule already exists for this app
        existing = [r for r in self.app_rules['display_rules'][display] if r.get('app') == app]
        if existing:
            existing[0].update(rule)
        else:
            self.app_rules['display_rules'][display].append(rule)
        
        self.save_app_rules()
    
    def remove_display_rule(self, display: str, app: str):
        """Remove a display rule"""
        if 'display_rules' not in self.app_rules:
            return
        
        if display not in self.app_rules['display_rules']:
            return
        
        self.app_rules['display_rules'][display] = [
            r for r in self.app_rules['display_rules'][display] 
            if r.get('app') != app
        ]
        self.save_app_rules()
    
    def add_startup_app(self, app: str):
        """Add an app to keep open on startup"""
        if 'startup' not in self.app_rules:
            self.app_rules['startup'] = {"keep_open": [], "close_others": True}
        
        if 'keep_open' not in self.app_rules['startup']:
            self.app_rules['startup']['keep_open'] = []
        
        if app not in self.app_rules['startup']['keep_open']:
            self.app_rules['startup']['keep_open'].append(app)
            self.save_app_rules()
    
    def remove_startup_app(self, app: str):
        """Remove an app from startup keep open list"""
        if 'startup' not in self.app_rules:
            return
        
        if 'keep_open' in self.app_rules['startup']:
            self.app_rules['startup']['keep_open'] = [
                a for a in self.app_rules['startup']['keep_open'] 
                if a != app
            ]
            self.save_app_rules()
    
    def get_all_behaviors(self) -> List[Dict]:
        """Get all registered behaviors"""
        return self.behaviors
    
    def reload(self):
        """Reload behaviors and app rules from files"""
        self.load_behaviors()
        self.load_app_rules()

