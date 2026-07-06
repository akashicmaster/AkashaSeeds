"""
Access Control Policy Module

[FUTURE ROADMAP REALIZED & CONCEPT LAYER READY]
This module currently acts as a backward-compatible bridge for legacy RBAC.
The core capability-based authorization is managed by IdentityManager 
(`lib/akasha/identisch.py`).

[CONCEPT LAYER UPDATE]
Policy mappings have been expanded to include Concept commands (Note, Script)
and advanced network telemetry.
"""

class AkashaRole:
    """
    Defines the core roles within the AkashicTree ecosystem.
    Determines the level of interaction allowed with the semantic network.
    """
    ADMIN = "admin"      # Full system access (CLI / Master Node / Global Cortex)
    CELL = "cell"        # Read/Write access to personal networks (Registered User)
    LEAF = "leaf"        # Read-only access (Guest / Viewer / Public API)

# Mapping of roles to permitted abstract actions/methods.
POLICY_MAP = {
    AkashaRole.ADMIN: [
        # Core & Legacy
        "write", "read", "drop", "list", "affix", "set", "help", 
        "initialize", "admin_stats", "calibrate", "sys.restore", "sys.backup",
        "dive.look", "dive.out", "explore", "dream", "link.create", "link.list", 
        "sys.telemetry", "sys.ping", "sys.status", "sys.status.full", "sys.history", "auth.login",
        "sys.shell.exec", "sys.service.up", "sys.service.down", "sys.service.ls",
        
        # Concept: Note
        "note.new", "note.container", "note.add", "note.remove", "note.toc", "note.metrics",
        
        # Concept: Script
        "script.new", "script.add", "script.ls", "script.run", "sys.run",
        
        # Contexa & Network
        "contexa.fetch", "jataka.dream", "jataka.calibrate", "jataka.echoes",
        "network.radar", "network.tree", "file.scan", "kw.verify", "kw.sync",
        "sys.encapsulate", "sys.decapsulate",
        
        # Sets & Meta & Clients
        "meta.set", "meta.add", "set.create", "set.add", "set.remove", "set.list", 
        "set.op", "set.map", "client.ls", "client.add", "client.rm",
        "alias", "alias.list", "alias.find"
    ],
    
    AkashaRole.CELL:  [
        # Core
        "write", "read", "list", "affix", "set", "help", "initialize", "calibrate",
        "dive.look", "dive.out", "explore", "dream", "auth.login",
        
        # Concept: Note & Script (Cells can create their own documents)
        "note.new", "note.container", "note.add", "note.remove", "note.toc", "note.metrics",
        "script.new", "script.add", "script.ls", "script.run",
        
        # Contexa & Network (Limited)
        "contexa.fetch", "jataka.dream", "network.radar", "network.tree",
        "meta.set", "meta.add", "set.create", "set.add", "set.list",
        "alias", "alias.list"
    ],
    
    AkashaRole.LEAF:  [
        # Core Read-Only
        "read", "list", "help", "auth.login", "sys.ping",
        "dive.look", "dive.out", "explore",
        
        # Concept Read-Only
        "note.toc", "note.metrics", "script.ls", "network.tree", "set.list", "alias.list"
    ]
}

def is_authorized(role: str, method: str) -> bool:
    """
    Evaluates if a given role is authorized to perform the requested method.
    Returns True if the method is explicitly listed in the policy map for the role.
    """
    allowed_methods = POLICY_MAP.get(role, [])
    return method in allowed_methods

def get_allowed_methods(role: str):
    """
    Returns the list of all methods permitted for a specific role.
    Used for generating help menus or dynamic UI filtering.
    """
    return POLICY_MAP.get(role, [])
