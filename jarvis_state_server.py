#!/usr/bin/env python3
# jarvis_state_server.py
# Run this alongside jarvis_clap.py
# Jarvis writes state to /tmp/jarvis_state
# This server exposes it at localhost:7777/state for the HUD

from http.server import HTTPServer, BaseHTTPRequestHandler
import json, os, threading

STATE_FILE = '/tmp/jarvis_state'

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/state':
            try:
                with open(STATE_FILE) as f:
                    state = f.read().strip()
            except:
                state = 'idle'
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'state': state}).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, *args):
        pass  # silent

def write_state(state):
    with open(STATE_FILE, 'w') as f:
        f.write(state)

def run():
    write_state('idle')
    server = HTTPServer(('localhost', 7777), Handler)
    print('[HUD] State server running on localhost:7777')
    server.serve_forever()

if __name__ == '__main__':
    run()
