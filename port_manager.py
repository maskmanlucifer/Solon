#!/usr/bin/env python3
"""
Port Manager - manages processes running on specific ports
"""

import subprocess
import os
from typing import List, Optional


def get_processes_on_port(port: int) -> List[int]:
    """Get list of process IDs using a specific port"""
    try:
        result = subprocess.run(
            ['lsof', '-ti', f':{port}'],
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode == 0 and result.stdout.strip():
            pids = [int(pid) for pid in result.stdout.strip().split('\n') if pid]
            return pids
        return []
    except Exception as e:
        print(f"Error getting processes on port {port}: {e}")
        return []


def kill_port(port: int, force: bool = False) -> bool:
    """Kill all processes running on a specific port"""
    pids = get_processes_on_port(port)
    
    if not pids:
        print(f"No processes found on port {port}")
        return False
    
    signal = '-9' if force else '-15'  # SIGKILL vs SIGTERM
    
    success = True
    for pid in pids:
        try:
            subprocess.run(['kill', signal, str(pid)], check=True)
            print(f"Killed process {pid} on port {port}")
        except subprocess.CalledProcessError as e:
            print(f"Failed to kill process {pid}: {e}")
            success = False
    
    return success


def get_port_info(port: int) -> Optional[dict]:
    """Get detailed information about what's running on a port"""
    try:
        result = subprocess.run(
            ['lsof', '-i', f':{port}'],
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode == 0 and result.stdout.strip():
            lines = result.stdout.strip().split('\n')
            if len(lines) > 1:
                # Parse header and first process line
                header = lines[0].split()
                process_line = lines[1].split()
                
                info = {
                    'pid': process_line[1] if len(process_line) > 1 else None,
                    'command': process_line[0] if process_line else None,
                    'user': process_line[2] if len(process_line) > 2 else None,
                }
                return info
        return None
    except Exception as e:
        print(f"Error getting port info: {e}")
        return None


def close_port(port: int) -> bool:
    """Alias for kill_port"""
    return kill_port(port)

