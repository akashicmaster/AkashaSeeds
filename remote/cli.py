"""
Remote CLI Shell Engine (Pro Edition).
Provides a local REPL environment that executes commands on a remote Akasha Gateway.
Seamlessly bridges the local file system (for pipes and redirection) with the 
remote semantic memory (Cortex) via JSON-RPC 2.0.

[SYNAPTIC LINKAGE]
All commands are tunneled via 'sys.cli_exec' to ensure parity between
local execution and remote execution environments.
"""
import sys
import os
import re
import json
import argparse
from typing import List, Optional, Any

# Ensure project root is in path for modules
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from remote.connector import AkashaRemoteConnector
from api.env_detector import env, Colors
from api.shell.input import InputBuffer

def safe_split(text: str, delimiter: str, maxsplit: int = -1) -> List[str]:
    """Handles splitting command pipelines while respecting quoted sections."""
    result, current = [], []
    in_quote, q_char, splits = False, None, 0
    for c in text:
        if maxsplit != -1 and splits >= maxsplit:
            current.append(c)
            continue
        if c in ['"', "'"]:
            if not in_quote: 
                in_quote, q_char = True, c
            elif q_char == c: 
                in_quote, q_char = False, None
        if c == delimiter and not in_quote:
            result.append("".join(current))
            current = []
            splits += 1
        else:
            current.append(c)
    result.append("".join(current))
    return result

def process_triple_quotes(text: str) -> str:
    """Converts multiline string literals into single-line escaped strings for RPC."""
    def replacer(match):
        content = match.group(1)
        escaped = content.replace('\\', '\\\\').replace('"', '\\"')
        return f'"{escaped}"'
    text = re.sub(r'"""(.*?)"""', replacer, text, flags=re.DOTALL)
    text = re.sub(r"'''(.*?)'''", replacer, text, flags=re.DOTALL)
    return text

def execute_remote_pipeline(full_cmd: str, connector: AkashaRemoteConnector, is_script: bool = False):
    """
    Executes a pipe-delimited command sequence on the remote Gateway.
    Bridging local file I/O with remote execution logic.
    """
    full_cmd = process_triple_quotes(full_cmd)
    
    # 1. Output Redirection (Local File)
    out_file = None
    parts = safe_split(full_cmd, ">", maxsplit=1)
    if len(parts) > 1:
        full_cmd, out_file = parts[0].strip(), parts[1].strip()
        
    # 2. Input Redirection (Local File)
    stdin_data = None
    parts = safe_split(full_cmd, "<", maxsplit=1)
    if len(parts) > 1:
        full_cmd, f_path = parts[0].strip(), parts[1].strip()
        try:
            with open(f_path, "r", encoding="utf-8") as f:
                try: 
                    stdin_data = json.load(f)
                except json.JSONDecodeError: 
                    f.seek(0)
                    stdin_data = f.read()
        except Exception as e:
            print(f"{Colors.FAIL}[!] Local File Read Error '{f_path}': {e}{Colors.ENDC}")
            return

    commands = [c.strip() for c in safe_split(full_cmd, "|")]
    current_pipe_data = stdin_data
    
    # 3. Pipeline Execution
    for cmd_str in commands:
        if not cmd_str: continue
        
        # Dispatch to the Mother Node's Gateway via sys.cli_exec
        res = connector.execute_cli_command(cmd_str, stdin_data=current_pipe_data)
        
        # Check for remote execution errors
        if isinstance(res, dict) and "error" in res:
            err = res['error']
            msg = err.get('message', str(err)) if isinstance(err, dict) else str(err)
            print(f"{Colors.FAIL}[Remote Error] {msg}{Colors.ENDC}")
            return
            
        current_pipe_data = res
        
    # 4. Result Output
    if current_pipe_data is not None:
        if out_file:
            try:
                with open(out_file, "w", encoding="utf-8") as f:
                    if isinstance(current_pipe_data, str): f.write(current_pipe_data)
                    else: json.dump(current_pipe_data, f, indent=2, ensure_ascii=False)
                if not is_script: print(f"{Colors.GREEN}[+] Output written to: {out_file}{Colors.ENDC}")
            except Exception as e:
                print(f"{Colors.FAIL}[!] Local File Write Error: {e}{Colors.ENDC}")
        else:
            if isinstance(current_pipe_data, str):
                print(current_pipe_data if current_pipe_data.startswith("\n") else f"\n{current_pipe_data}")
            else:
                print(json.dumps(current_pipe_data, indent=2, ensure_ascii=False))

def run_remote_cli():
    """Main REPL loop for the Remote Connector."""
    parser = argparse.ArgumentParser(description="Akasha Remote CLI")
    parser.add_argument("--url", type=str, required=True, help="RPC Gateway URL")
    parser.add_argument("--user", type=str, default="admin", help="User ID")
    args = parser.parse_args()

    print(f"\n{Colors.CYAN}[*] Linking to Remote Gateway: {args.url}{Colors.ENDC}")
    connector = AkashaRemoteConnector(args.url)
    
    # Ping
    if "error" in connector.send_rpc("sys.ping", {}):
        print(f"{Colors.FAIL}[!] Endpoint unreachable.{Colors.RESET}")
        return

    # Auth
    for attempts in range(3, 0, -1):
        pwd = env.secure_input(f"\n{Colors.WARNING}[Security] Passphrase for '{args.user}' [{attempts} left]:{Colors.ENDC}")
        res = connector.authenticate(args.user, pwd)
        if "error" not in res:
            print(f"{Colors.GREEN}[+] Session established.{Colors.ENDC}")
            break
        print(f"{Colors.FAIL} [!] Access Denied.{Colors.ENDC}")
    else:
        sys.exit(1)

    # REPL
    buf = InputBuffer()
    while True:
        try:
            prompt = f"{Colors.BOLD}{'...> ' if buf.in_multiline else f'remote@{args.user}> '}{Colors.ENDC}"
            line = input(prompt)
            if not buf.push(line):
                continue

            full_cmd = buf.flush()
            if not full_cmd: continue
            if full_cmd.lower() in ["exit", "quit"]: break
            
            # Script batching
            if full_cmd.startswith("run "):
                path = full_cmd.split(" ", 1)[1].strip()
                if os.path.exists(path):
                    with open(path, "r") as f:
                        for s_line in f:
                            if s_line.strip(): execute_remote_pipeline(s_line.strip(), connector, True)
                continue

            execute_remote_pipeline(full_cmd, connector)
        except (KeyboardInterrupt, EOFError): break

if __name__ == "__main__":
    run_remote_cli()
