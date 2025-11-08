#!/usr/bin/env python3
"""
Solon Daemon - Main daemon process that runs continuously
"""

import socket
import os
import sys
import json
import signal
import threading
import logging
from pathlib import Path
from command_processor import CommandProcessor
from behavior_registry import BehaviorRegistry
from display_monitor import DisplayMonitor
from app_launcher import get_apps_with_login_items, is_app_running


SOCKET_PATH = '/tmp/solon.sock'
LOG_FILE = os.path.expanduser('~/Library/Logs/solon_daemon.log')


class SolonDaemon:
    def __init__(self):
        self.socket_path = SOCKET_PATH
        self.running = True
        self.processor = CommandProcessor()
        self.registry = BehaviorRegistry()
        self.display_monitor = None
        self.setup_logging()
        self.setup_signal_handlers()
    
    def setup_logging(self):
        """Setup logging"""
        log_dir = os.path.dirname(LOG_FILE)
        os.makedirs(log_dir, exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(LOG_FILE),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger('SolonDaemon')
    
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
        self.cleanup()
        sys.exit(0)
    
    def cleanup(self):
        """Cleanup resources"""
        if os.path.exists(self.socket_path):
            try:
                os.unlink(self.socket_path)
            except:
                pass
    
    def handle_startup(self):
        """Handle startup tasks - manage apps that open on login"""
        self.logger.info("Handling startup tasks...")
        app_rules = self.registry.get_startup_rules()
        keep_open = app_rules.get('keep_open', [])
        close_others = app_rules.get('close_others', True)
        
        login_items = get_apps_with_login_items()
        
        # Close apps that shouldn't be open
        if close_others:
            for app in login_items:
                if app not in keep_open and is_app_running(app):
                    try:
                        # Close the app
                        import subprocess
                        subprocess.run(['osascript', '-e', f'tell application "{app}" to quit'], 
                                     check=False)
                        self.logger.info(f"Closed app on startup: {app}")
                    except Exception as e:
                        self.logger.error(f"Error closing {app}: {e}")
    
    def start_display_monitor(self):
        """Start display monitoring in background thread"""
        self.display_monitor = DisplayMonitor()
        monitor_thread = threading.Thread(
            target=self.display_monitor.start_monitoring,
            daemon=True
        )
        monitor_thread.start()
        self.logger.info("Display monitor started")
    
    def handle_client(self, client_socket, address):
        """Handle a client connection"""
        try:
            data = client_socket.recv(4096).decode('utf-8')
            if not data:
                return
            
            self.logger.info(f"Received command: {data}")
            
            # Process command
            result = self.processor.process_command(data)
            
            # Send response
            response = json.dumps(result)
            client_socket.sendall(response.encode('utf-8'))
            
        except Exception as e:
            self.logger.error(f"Error handling client: {e}")
            error_response = json.dumps({"success": False, "error": str(e)})
            try:
                client_socket.sendall(error_response.encode('utf-8'))
            except:
                pass
        finally:
            client_socket.close()
    
    def run(self):
        """Run the daemon"""
        self.logger.info("Starting Solon daemon...")
        
        # Handle startup tasks
        self.handle_startup()
        
        # Start display monitor
        self.start_display_monitor()
        
        # Remove old socket if exists
        self.cleanup()
        
        # Create socket
        server_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        server_socket.bind(self.socket_path)
        server_socket.listen(5)
        
        # Set socket permissions
        os.chmod(self.socket_path, 0o666)
        
        self.logger.info(f"Daemon listening on {self.socket_path}")
        
        # Main loop
        while self.running:
            try:
                server_socket.settimeout(1.0)  # Allow checking self.running
                client_socket, address = server_socket.accept()
                
                # Handle client in separate thread
                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, address),
                    daemon=True
                )
                client_thread.start()
                
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    self.logger.error(f"Error in main loop: {e}")
        
        # Cleanup
        server_socket.close()
        self.cleanup()
        self.logger.info("Daemon stopped")


def main():
    """Main entry point"""
    daemon = SolonDaemon()
    daemon.run()


if __name__ == '__main__':
    main()

