"""
OperatorConcept — tactician terminal.
Stateless: carries no concept_id of its own; validates access rights on argument atoms only.
Part of the Homonoia game world (see homonoia.py).
"""
import time
from typing import Any, Dict

from lib.akasha.concepts.base import BaseConcept


class OperatorConcept(BaseConcept):
    """Tactician (operator) model. Stateless: carries no concept_id or INDEX_SET."""

    CONCEPT_PREFIX = "operator"
    # Stateless — CONTEXT_KEY_ACTIVE remains None (BaseConcept default)

    CONCEPT_METHODS = {
        "clash": {"op": "op_clash"},
    }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _get_author_and_scopes(self):
        author_id = getattr(self.session, "client_id", "system")
        return author_id, [f"owner:user_{author_id}", f"view:user_{author_id}"]

    def _require_access(self, atom_id: str, label: str = "Atom") -> None:
        if not atom_id:
            raise ValueError(f"{label} id is required.")
        if not self.cortex.check_access(atom_id, self.allowed_scopes):
            raise RuntimeError(f"{label} not accessible: {atom_id[:12]}")

    def _evaluate_tactics(self, jcl: Dict[str, Any]) -> int:
        """Evaluate tactics JCL and return a power score."""
        return jcl.get("complexity_score", 60)

    # ------------------------------------------------------------------
    # Operators
    # ------------------------------------------------------------------

    def op_clash(self, attacker_soma_id: str, defender_id: str,
                 tactics_jcl: Dict[str, Any], mode: str) -> Dict[str, Any]:
        """
        Run a Soma combat resolution.
        mode: "simulation" (training — no damage) or "real" (live combat)
        Stateless: does not call _require_concept.
        """
        self._require_access(attacker_soma_id, "Attacker Soma")
        author_id, scopes = self._get_author_and_scopes()

        attack_power = self._evaluate_tactics(tactics_jcl)
        success = attack_power > 50

        result_payload: Dict[str, Any] = {
            "tactics_used": tactics_jcl.get("name", "Unknown"),
            "power": attack_power,
            "success": success,
            "mode": mode,
        }

        if mode == "simulation":
            # Savepoint principle: simulations are also persisted as events in Cortex
            sim_id = self.cortex.put_chunk(
                content=f"[ Simulation Result: Success={success} ]",
                meta={
                    "type": "event", "event_type": "simulation",
                    "attacker": attacker_soma_id, "success": success,
                    "timestamp": time.time(),
                },
                author=author_id, scopes=scopes,
            )
            self.cortex.put_link(attacker_soma_id, sim_id, "sys:simulated", author=author_id)
            result_payload["note"] = "Simulation complete. Event logged. No damage taken."
            result_payload["simulation_id"] = sim_id

        elif mode == "real":
            event_id = self.cortex.put_chunk(
                content=f"[ Combat Result: Success={success} ]",
                meta={
                    "type": "event", "event_type": "combat_result",
                    "attacker": attacker_soma_id, "success": success,
                    "timestamp": time.time(),
                },
                author=author_id, scopes=scopes,
            )
            self.cortex.put_link(attacker_soma_id, event_id, "sys:involved_in", author=author_id)
            if not success:
                self.cortex.put_link(attacker_soma_id, event_id,
                                     "sys:state_change:damaged", author=author_id)
                result_payload["note"] = "Real combat failed. Soma damaged. Repair required."
            result_payload["event_id"] = event_id

        else:
            raise ValueError(f"Invalid clash mode '{mode}'. Use 'simulation' or 'real'.")

        return result_payload
