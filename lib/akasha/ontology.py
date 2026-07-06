"""
Ontology Bootstrap Engine
Handles the automatic loading/registration of acquired concepts (JSON) and 
their topological links into the database upon startup.

[MULTIDIMENSIONAL SCOPE UPDATE]
All bootstrapped concepts are safely anchored into the Universal Scope 
('scope:sys:universal' and 'view:public') to ensure they serve as foundational 
knowledge available to all clients across the Akashic network.
"""
import os
import json

def bootstrap_ontology(composite_engine, root_path="."):
    """
    Scans and loads external JSON ontologies (from ontology/ dir) into the brain.
    Should be called once during system startup (e.g., in api/main.py).
    """
    print("[Ontology] Bootstrapping acquired conceptual frameworks...")
    loaded_concepts = 0
    loaded_links = 0
    ontology_dir = os.path.join(root_path, "ontology")
    
    if os.path.exists(ontology_dir):
        for filename in os.listdir(ontology_dir):
            if filename.endswith(".json"):
                filepath = os.path.join(ontology_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if isinstance(data, dict):
                            # 1. First Pass: Inject all concepts (Nodes)
                            for key, value in data.items():
                                if key != "__links__":
                                    if _inject_concept(composite_engine, key, str(value)):
                                        loaded_concepts += 1
                            
                            # 2. Second Pass: Inject topological links with intentionality weights
                            if "__links__" in data and isinstance(data["__links__"], list):
                                for link in data["__links__"]:
                                    src = link.get("src")
                                    dst = link.get("dst")
                                    rel = link.get("rel", "sys:associated_with")
                                    w = float(link.get("w", 1.0))
                                    
                                    src_id = composite_engine.resolve_alias(src)
                                    dst_id = composite_engine.resolve_alias(dst)
                                    
                                    if src_id and dst_id:
                                        # Use the Composite Layer to ensure any hooks or syncs are triggered
                                        composite_engine.put_link(
                                            src=src_id, 
                                            dst=dst_id, 
                                            rel=rel, 
                                            w=w, 
                                            author="system.ontology"
                                        )
                                        loaded_links += 1
                except Exception as e:
                    print(f"[Ontology] Error loading {filename}: {e}")
                    
    if loaded_concepts > 0 or loaded_links > 0:
        print(f"[Ontology] Awakened {loaded_concepts} concepts and wove {loaded_links} synapses.")

def _inject_concept(composite, alias: str, desc: str) -> bool:
    """
    Helper to inject a concept hub if it doesn't already exist.
    Anchors the foundational concept securely into the universal public scope.
    """
    if not composite.resolve_alias(alias):
        content = f"[ Concept Hub: {alias} ]\n{desc}"
        
        # [SECURITY] Fundamental ontology knowledge belongs to the universe
        universal_scopes = ["scope:sys:universal", "view:public"]
        
        tid = composite.put_chunk(
            content=content, 
            author="system.ontology",
            scopes=universal_scopes # Inject into multidimensional IAM
        )
        composite.set_alias(tid, alias)
        return True
    return False
