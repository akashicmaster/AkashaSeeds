"""
Akasha Protocol Adapter.
Encapsulates both stdio (subprocess) and HTTP (network) communication,
providing a unified method interface for JSON-RPC/MCP payloads.

[IAM INTEGRATION UPDATE]
Now supports persistent Identity State. Automatically injects 'client_id' 
and 'token' into the params of every outgoing request to ensure proper 
Multidimensional Scope (Ownership/View) resolution at the Gateway.

Zero-dependency design (uses urllib instead of requests) ensures compatibility 
with edge devices and restricted environments (e.g., iOS, bare-metal IoT).
"""
import json
import subprocess
import sys
import os
import urllib.request
import urllib.error

class AkashaClient:
    def __init__(self, mode="stdio", endpoint=None, client_id="guest", token=None):
        self.mode = mode
        self.endpoint = endpoint
        self.proc = None
        
        # Identity State
        self.client_id = client_id
        self.token = token
        
        if mode == "stdio":
            self._start_stdio_process()

    def _start_stdio_process(self):
        """
        Initializes the backend api.main as a local subprocess.
        Ensures the environment is set up for module resolution.
        """
        root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        env = {**os.environ, "PYTHONPATH": root_dir}
        
        self.proc = subprocess.Popen(
            [sys.executable, "-u", "-m", "api.main", "--stdio"],
            stdin=subprocess.PIPE, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True, 
            bufsize=1, 
            env=env, 
            cwd=root_dir
        )

    def set_identity(self, client_id: str, token: str = None):
        """Updates the identity context for all future calls."""
        self.client_id = client_id
        self.token = token

    def call(self, method, params=None):
        """
        Sends a request in JSON-RPC format.
        Automatically injects identity context for IAM scope resolution.
        """
        if params is None:
            params = {}
            
        # [NEW] Automatically inject Identity Context into params
        # (Only if not explicitly overridden in the specific call)
        if "client_id" not in params:
            params["client_id"] = self.client_id
        if self.token and "token" not in params:
            params["token"] = self.token

        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": 1
        }

        if self.mode == "stdio":
            if not self.proc:
                return {"error": "Stdio process not initialized"}
            
            self.proc.stdin.write(json.dumps(payload) + "\n")
            self.proc.stdin.flush()
            
            line = self.proc.stdout.readline()
            try:
                return json.loads(line) if line else {"error": "No response from stdio"}
            except json.JSONDecodeError:
                return {"error": "Invalid JSON response from stdio", "raw": line}
        
        elif self.mode == "http":
            if not self.endpoint:
                return {"error": "HTTP endpoint not specified"}
            
            try:
                url = f"{self.endpoint.rstrip('/')}/rpc"
                data = json.dumps(payload).encode('utf-8')
                
                # In HTTP mode, we might also pass the token as a Bearer header in the future
                headers = {'Content-Type': 'application/json'}
                if self.token:
                    headers['Authorization'] = f"Bearer {self.token}"
                
                req = urllib.request.Request(url, data=data, headers=headers)
                
                with urllib.request.urlopen(req, timeout=10.0) as response:
                    return json.loads(response.read().decode('utf-8'))
                    
            except urllib.error.URLError as e:
                return {"error": f"HTTP Connection failed: {str(e)}"}
            except json.JSONDecodeError:
                return {"error": "Invalid JSON response from HTTP endpoint"}

    def close(self):
        """Terminates the local stdio process and releases resources."""
        if self.proc:
            try:
                self.proc.terminate()
                self.proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.proc.kill()
            self.proc = None
