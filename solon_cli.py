#!/usr/bin/env python3
"""
Solon CLI - Command-line interface for interacting with daemon
"""

import socket
import json
import sys
import os

SOCKET_PATH = '/tmp/solon.sock'


def send_command(command: str) -> dict:
    """Send a command to the daemon"""
    if not os.path.exists(SOCKET_PATH):
        print("Error: Daemon is not running. Start it with: solon_daemon.py")
        return {"success": False, "error": "Daemon not running"}
    
    try:
        client_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client_socket.connect(SOCKET_PATH)
        
        client_socket.sendall(command.encode('utf-8'))
        
        response = b''
        while True:
            chunk = client_socket.recv(4096)
            if not chunk:
                break
            response += chunk
        
        client_socket.close()
        
        result = json.loads(response.decode('utf-8'))
        return result
        
    except Exception as e:
        return {"success": False, "error": str(e)}


def main():
    """Main CLI entry point"""
    if len(sys.argv) < 2:
        print("Usage: solon_cli.py <command>")
        print("\nExamples:")
        print("  solon_cli.py 'open cursor lucifer'")
        print("  solon_cli.py 'move cursor to w1'")
        print("  solon_cli.py 'close port 3000'")
        print("  solon_cli.py 'close cursor except lucifer'")
        sys.exit(1)
    
    command = ' '.join(sys.argv[1:])
    result = send_command(command)
    
    if result.get('success'):
        print("✓ Command executed successfully")
        if result.get('behavior'):
            print(f"  Behavior: {result['behavior']}")
    else:
        print(f"✗ Error: {result.get('error', 'Unknown error')}")
        sys.exit(1)


if __name__ == '__main__':
    main()

