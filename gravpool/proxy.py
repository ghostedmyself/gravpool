
import os
import json
import socket
import tempfile
import subprocess
import time
import urllib.request
import urllib.error

class ProxySupervisor:
    def __init__(self, bin_path, auth_dirs, port=None):
        self.bin_path = bin_path
        self.auth_dirs = auth_dirs
        self.port = None
        self.running = False
        self.pid = None
        self.error = None
        self.process = None

        if not os.path.exists(self.bin_path):
            self.error = f"Binary not found: {self.bin_path}"
            return

        # Pick a free port (or use the caller-supplied one)
        if port:
            self.port = int(port)
        else:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.bind(('', 0))
                self.port = s.getsockname()[1]
                s.close()
            except Exception as e:
                self.error = f"Failed to bind port: {e}"
                return

        auth_dir = self.auth_dirs[0] if self.auth_dirs else "auth"

        config = {
            "server": {
                "host": "127.0.0.1",
                "port": self.port
            },
            "oauth": {
                "auth-dir": auth_dir
            },
            "access": {
                "api-keys": ["sk-local"]
            }
        }

        fd, self.cfg_path = tempfile.mkstemp(suffix=".json")
        with os.fdopen(fd, 'w') as f:
            json.dump(config, f)

        try:
            self.process = subprocess.Popen(
                [self.bin_path, "--config", self.cfg_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            self.pid = self.process.pid
        except Exception as e:
            self.error = f"Spawn failed: {e}"
            return

        # Wait for healthy
        start = time.time()
        healthy = False
        while time.time() - start < 15:
            if self.process.poll() is not None:
                self.error = "Process exited prematurely"
                return
            if self.healthy():
                healthy = True
                break
            time.sleep(0.5)

        if not healthy:
            self.error = "Timeout waiting for proxy to start"
            self.stop()
            return
            
        self.running = True

    def healthy(self):
        if self.process and self.process.poll() is not None:
            return False
        try:
            req = urllib.request.Request(f"http://127.0.0.1:{self.port}/v1/models")
            req.add_header("Authorization", "Bearer sk-local")
            with urllib.request.urlopen(req, timeout=1) as resp:
                return resp.status == 200
        except Exception:
            return False

    def models(self):
        if not self.running:
            return {"data": [], "error": "proxy not running"}
        try:
            req = urllib.request.Request(f"http://127.0.0.1:{self.port}/v1/models")
            req.add_header("Authorization", "Bearer sk-local")
            with urllib.request.urlopen(req, timeout=5) as resp:
                if resp.status == 200:
                    return json.loads(resp.read().decode('utf-8'))
        except Exception:
            pass
        return {"data": [], "error": "failed to fetch models"}

    def stop(self):
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.process.kill()
        if hasattr(self, 'cfg_path') and os.path.exists(self.cfg_path):
            os.remove(self.cfg_path)
        self.running = False
