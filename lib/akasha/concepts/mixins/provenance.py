"""
ProvenanceMixin.
Shared provenance and source-credibility utilities for Akasha Concept Models.

Provides:
    - Latest event-sourced source eval lookup
    - Effective source credibility and independence (with eval override)
    - Weighted source credibility
    - Algorithm confidence calculation
    - Inferred confidence formula
    - Full provenance payload builder
    - Provenance trace helper

Expected host class attributes:
    self._meta(key)
    self._members(subset)
    self._summary(key)
    self._clamp01(value, default=0.0)
    self._require_access(atom_id, label)
"""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

PROVENANCE_FORMULA = (
    "extraction_conf × inference_conf × Σ(source_i.credibility_effective × weight_i / Σweight_i)"
)


class ProvenanceMixin:
    """Reusable provenance and credibility helpers for concept models."""

    SOURCE_EVAL_SUBSET: str = "source_evals"

    # ------------------------------------------------------------------
    # Source eval lookup
    # ------------------------------------------------------------------

    def _latest_eval_for_source(self, source_id: str) -> Optional[Dict[str, Any]]:
        """Return the most recent source eval atom for *source_id*, or None."""
        best: Optional[Dict[str, Any]] = None
        best_time = -1.0
        for eval_id in self._members(self.SOURCE_EVAL_SUBSET):
            meta = self._meta(eval_id)
            if meta.get("source_id") != source_id:
                continue
            created = float(meta.get("created_at", 0.0))
            if created >= best_time:
                best_time = created
                best = {"id": eval_id, "meta": meta, "created_at": created}
        return best

    # ------------------------------------------------------------------
    # Effective source metrics
    # ------------------------------------------------------------------

    def _effective_source_credibility(self, source_id: str) -> float:
        """Latest eval credibility override, falling back to source meta."""
        base = self._clamp01(self._meta(source_id).get("credibility", 0.5), 0.5)
        latest = self._latest_eval_for_source(source_id)
        if latest:
            updates = latest["meta"].get("updates") or {}
            if "credibility" in updates:
                return self._clamp01(updates["credibility"], base)
        return base

    def _effective_source_independence(self, source_id: str) -> float:
        """Latest eval independence override, falling back to source meta."""
        base = self._clamp01(self._meta(source_id).get("independence", 0.5), 0.5)
        latest = self._latest_eval_for_source(source_id)
        if latest:
            updates = latest["meta"].get("updates") or {}
            if "independence" in updates:
                return self._clamp01(updates["independence"], base)
        return base

    def _source_snapshot(self, source_id: str) -> Dict[str, Any]:
        """Source summary enriched with effective credibility and independence."""
        snap = self._summary(source_id)
        snap["effective"] = {
            "credibility":  self._effective_source_credibility(source_id),
            "independence": self._effective_source_independence(source_id),
        }
        return snap

    # ------------------------------------------------------------------
    # Weighted credibility
    # ------------------------------------------------------------------

    def _weighted_source_credibility(
        self,
        inputs: List[Dict[str, Any]],
        normalize: bool = True,
    ) -> float:
        """
        Weighted average source credibility across *inputs*.

        inputs: list of ``{"source_id": "...", "weight": 1.0, ...}``
        normalize=True divides each weight by the total (prevents result > 1.0).
        """
        for inp in inputs:
            if not inp.get("source_id"):
                raise ValueError("Each input must have a source_id.")
            if float(inp.get("weight", 1.0)) < 0:
                raise ValueError("Input weights must be >= 0.")
        total_weight = sum(float(inp.get("weight", 1.0)) for inp in inputs)
        if total_weight <= 0:
            return 0.0
        total = 0.0
        for inp in inputs:
            self._require_access(inp["source_id"], "Input source")
            weight = float(inp.get("weight", 1.0))
            cred = self._effective_source_credibility(inp["source_id"])
            total += cred * (weight / total_weight if normalize else weight)
        return round(self._clamp01(total), 4)

    # ------------------------------------------------------------------
    # Algorithm confidence
    # ------------------------------------------------------------------

    def _algorithm_confidence(
        self,
        confidence: Any,
        method: str,
        llm_trust: float = 1.0,
    ) -> float:
        """Effective algorithm confidence = clamp01(confidence) × clamp01(llm_trust)."""
        return self._clamp01(self._clamp01(confidence) * self._clamp01(llm_trust))

    # ------------------------------------------------------------------
    # Inferred confidence
    # ------------------------------------------------------------------

    def _inferred_confidence(
        self,
        inputs: List[Dict[str, Any]],
        extraction_confidence: float,
        extraction_method: str,
        extraction_llm_trust: float,
        inference_confidence: float,
        inference_method: str,
        inference_llm_trust: float,
    ) -> Dict[str, Any]:
        """Return the confidence breakdown dict for an inferred assertion."""
        eff_extraction = self._algorithm_confidence(
            extraction_confidence, extraction_method, extraction_llm_trust,
        )
        eff_inference = self._algorithm_confidence(
            inference_confidence, inference_method, inference_llm_trust,
        )
        source_weighted = self._weighted_source_credibility(inputs)
        overall = round(eff_extraction * eff_inference * source_weighted, 4)
        return {
            "extraction_confidence":       round(eff_extraction, 4),
            "inference_confidence":        round(eff_inference, 4),
            "source_weighted_credibility": source_weighted,
            "overall_confidence":          overall,
            "formula":                     PROVENANCE_FORMULA,
        }

    # ------------------------------------------------------------------
    # Full provenance builder
    # ------------------------------------------------------------------

    def _build_provenance(
        self,
        inputs: List[Dict[str, Any]],
        extraction_method: str,
        extraction_confidence: float,
        extraction_model: str,
        extraction_llm_trust: float,
        inference_method: str,
        inference_confidence: float,
        inference_model: str,
        inference_llm_trust: float,
        steps: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Build a complete provenance payload for an inferred assertion."""
        eff_extraction = self._algorithm_confidence(
            extraction_confidence, extraction_method, extraction_llm_trust,
        )
        eff_inference = self._algorithm_confidence(
            inference_confidence, inference_method, inference_llm_trust,
        )
        total_weight = sum(float(inp.get("weight", 1.0)) for inp in inputs)
        expanded: List[Dict[str, Any]] = []
        source_weighted = 0.0
        for inp in inputs:
            sid = inp.get("source_id", "")
            weight = float(inp.get("weight", 1.0))
            norm_w = weight / total_weight if total_weight > 0 else 0.0
            cred_eff = self._effective_source_credibility(sid)
            indep_eff = self._effective_source_independence(sid)
            source_weighted += cred_eff * norm_w
            expanded.append({
                "source_id":              sid,
                "weight":                 weight,
                "weight_norm":            round(norm_w, 4),
                "credibility_effective":  round(cred_eff, 4),
                "independence_effective": round(indep_eff, 4),
                "role":                   inp.get("role", "input"),
            })
        source_weighted = round(self._clamp01(source_weighted), 4)
        overall_confidence = round(eff_extraction * eff_inference * source_weighted, 4)
        return {
            "extraction_algorithm": {
                "method":     extraction_method,
                "model":      extraction_model or None,
                "llm_trust":  extraction_llm_trust,
                "confidence": round(eff_extraction, 4),
            },
            "inference_algorithm": {
                "method":     inference_method,
                "model":      inference_model or None,
                "llm_trust":  inference_llm_trust,
                "confidence": round(eff_inference, 4),
            },
            "inputs":                      expanded,
            "steps":                       steps or [],
            "source_weighted_credibility": source_weighted,
            "overall_confidence":          overall_confidence,
            "formula":                     PROVENANCE_FORMULA,
            "curated_at":                  time.time(),
        }

    # ------------------------------------------------------------------
    # Source trace
    # ------------------------------------------------------------------

    def _trace_sources_from_provenance(
        self, provenance: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Return a source snapshot for each input recorded in *provenance*."""
        result: List[Dict[str, Any]] = []
        for inp in provenance.get("inputs", []):
            sid = inp.get("source_id", "")
            if sid:
                result.append(self._source_snapshot(sid))
        return result
