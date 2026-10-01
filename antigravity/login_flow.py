from __future__ import annotations

import os
import time
import urllib.parse
import webbrowser
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import TYPE_CHECKING, Optional

from antigravity import constants
from antigravity.oauth import build_auth_url, exchange_code, save_new_account

if TYPE_CHECKING:
    from antigravity.store import AuthAccount

class CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        parsed_path = urllib.parse.urlparse(self.path)
        
        if parsed_path.path == '/auth/callback':
            query = urllib.parse.parse_qs(parsed_path.query)
            
            self.server.auth_code = query.get('code', [None])[0]
            self.server.auth_state = query.get('state', [None])[0]
            self.server.auth_error = query.get('error', [None])[0]
            
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            if self.server.auth_error:
                html = f"<html><body><h1>Authentication Failed</h1><p>Error: {self.server.auth_error}</p><p>You can close this window.</p></body></html>"
            elif self.server.auth_code:
                html = "<html><body><h1>Authentication Successful</h1><p>You can close this window and return to the terminal.</p></body></html>"
            else:
                html = "<html><body><h1>Authentication Failed</h1><p>No code provided.</p><p>You can close this window.</p></body></html>"
            
            self.wfile.write(html.encode('utf-8'))
            
            # Notify the server that we are done
            threading.Thread(target=self.server.shutdown).start()
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not Found")

    def log_message(self, format: str, *args: any) -> None:
        pass  # Suppress logging

class AuthServer(HTTPServer):
    def __init__(self, server_address: tuple[str, int], RequestHandlerClass: type) -> None:
        super().__init__(server_address, RequestHandlerClass)
        self.auth_code: Optional[str] = None
        self.auth_state: Optional[str] = None
        self.auth_error: Optional[str] = None

def add_account_cmd(auth_dir: str, *, browser_open: bool = True, timeout: int = 300) -> AuthAccount:
    """
    Initiate the OAuth login flow to add a new account.
    """
    os.makedirs(auth_dir, exist_ok=True)
    
    redirect_uri = f"http://127.0.0.1:{constants.CALLBACK_PORT}/auth/callback"
    auth_url, state = build_auth_url(redirect_uri=redirect_uri)
    
    try:
        server = AuthServer(('127.0.0.1', constants.CALLBACK_PORT), CallbackHandler)
    except OSError as e:
        raise RuntimeError(f"Could not start local server on port {constants.CALLBACK_PORT}. Is it in use? Error: {e}")
    
    print(f"Please authenticate in your browser.\nIf it doesn't open automatically, visit this URL:\n{auth_url}\n")
    
    if browser_open:
        try:
            webbrowser.open(auth_url)
        except Exception as e:
            print(f"Could not open browser automatically: {e}")
            
    # Run the server in a separate thread with a timeout
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    
    start_time = time.time()
    while server_thread.is_alive():
        server_thread.join(timeout=1.0)
        if time.time() - start_time > timeout:
            server.shutdown()
            server.server_close()
            raise RuntimeError(f"Timeout of {timeout}s exceeded while waiting for authentication callback.")
            
    server.server_close()
    
    if server.auth_error:
        raise RuntimeError(f"Authentication failed: {server.auth_error}")
        
    if not server.auth_code:
        raise RuntimeError("Authentication failed: No authorization code received.")
        
    if server.auth_state != state:
        raise RuntimeError("Authentication failed: State mismatch (possible CSRF attack).")
        
    token_resp = exchange_code(server.auth_code, redirect_uri=redirect_uri)
    account = save_new_account(token_resp, auth_dir)
    
    print(f"Successfully added account: {account.email}")
    return account
