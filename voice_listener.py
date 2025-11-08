#!/usr/bin/env python3
"""
Voice Listener - Optional voice recognition support
"""

import speech_recognition as sr
import socket
import json
import os
import threading

SOCKET_PATH = '/tmp/solon.sock'


class VoiceListener:
    def __init__(self, wake_word: str = "solon"):
        self.wake_word = wake_word.lower()
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.listening = False
        self.setup_microphone()
    
    def setup_microphone(self):
        """Setup microphone and adjust for ambient noise"""
        print("Adjusting microphone for ambient noise...")
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
        print("Microphone ready")
    
    def send_command(self, command: str) -> dict:
        """Send command to daemon"""
        if not os.path.exists(SOCKET_PATH):
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
            return json.loads(response.decode('utf-8'))
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def listen_once(self) -> str:
        """Listen for a single command"""
        try:
            with self.microphone as source:
                print("Listening...")
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
            
            print("Processing...")
            text = self.recognizer.recognize_google(audio)
            print(f"Heard: {text}")
            return text.lower()
        except sr.WaitTimeoutError:
            return ""
        except sr.UnknownValueError:
            print("Could not understand audio")
            return ""
        except sr.RequestError as e:
            print(f"Recognition service error: {e}")
            return ""
    
    def listen_continuous(self):
        """Listen continuously for wake word and commands"""
        print(f"Voice listener started. Say '{self.wake_word}' to activate.")
        self.listening = True
        
        while self.listening:
            try:
                text = self.listen_once()
                
                if not text:
                    continue
                
                # Check for wake word
                if self.wake_word in text:
                    # Extract command after wake word
                    command = text.replace(self.wake_word, '').strip()
                    if command:
                        print(f"Executing: {command}")
                        result = self.send_command(command)
                        if result.get('success'):
                            print("✓ Command executed")
                        else:
                            print(f"✗ Error: {result.get('error')}")
                else:
                    # Try to execute directly if no wake word
                    print(f"Executing: {text}")
                    result = self.send_command(text)
                    if result.get('success'):
                        print("✓ Command executed")
                    else:
                        print(f"✗ Error: {result.get('error')}")
            
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}")
        
        print("Voice listener stopped")
    
    def stop(self):
        """Stop listening"""
        self.listening = False


def main():
    """Main entry point"""
    import sys
    
    wake_word = sys.argv[1] if len(sys.argv) > 1 else "solon"
    
    listener = VoiceListener(wake_word=wake_word)
    
    try:
        listener.listen_continuous()
    except KeyboardInterrupt:
        listener.stop()
        print("\nStopped")


if __name__ == '__main__':
    main()

