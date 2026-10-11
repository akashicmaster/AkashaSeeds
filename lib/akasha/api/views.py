"""
The CLI view descriptors the heart itself emits (group 4, 4.14).

The shell's renderer draws a result by its `_view` token (`api/shell/renderer.py`); a Concept Model
builds those descriptors with the application's `TextViewConcept` factories. The heart builds ONE
kind — the link-traversal tree of `graph.tree` — and used to borrow the application's class for it,
by prefix. These two factories produce the identical shape, so the renderer sees no difference and
the heart reaches no Concept Model.
"""
from typing import Any, Dict, List, Optional

TREE = "tree"


def node(label: str, sublabel: str = "",
         children: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """A tree node: {label, sublabel?, children?}."""
    n: Dict[str, Any] = {"label": label}
    if sublabel:
        n["sublabel"] = sublabel
    if children:
        n["children"] = children
    return n


def tree(title: str, root: str, children: List[Dict[str, Any]]) -> Dict[str, Any]:
    """A tree view: {_view: tree, title, root, children}."""
    return {"_view": TREE, "title": title, "root": root, "children": children}
