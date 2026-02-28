"""
OrbVeil — Satellite conjunction assessment for Python.

Open-source library for screening conjunctions, parsing CDMs,
and computing collision probability. Built for operators who
need transparency in safety-critical decisions.
"""

from __future__ import annotations

__version__ = "0.1.0-dev"

from orbveil.core.tle import TLE, parse_tle
from orbveil.core.propagation import propagate, propagate_batch, StateVector
from orbveil.core.screening import screen, screen_catalog, filter_stale_tles, ConjunctionEvent
from orbveil.core.probability import compute_pc, PcMethod, PcResult
from orbveil.core.risk import RiskAssessment, RiskCategory, assess_risk, classify_events
from orbveil.core.formations import FormationGroup, detect_formations, is_formation_pair, filter_formation_events
from orbveil.data.cdm import CDM, CDMObject
from orbveil.data.spacetrack import SpaceTrackClient

__all__ = [
    "__version__",
    # TLE parsing
    "TLE",
    "parse_tle",
    # Propagation
    "propagate",
    "propagate_batch",
    "StateVector",
    # Conjunction screening
    "screen",
    "screen_catalog",
    "filter_stale_tles",
    "ConjunctionEvent",
    # Collision probability
    "compute_pc",
    "PcMethod",
    "PcResult",
    # Risk assessment
    "RiskAssessment",
    "RiskCategory",
    "assess_risk",
    "classify_events",
    # Formation detection
    "FormationGroup",
    "detect_formations",
    "is_formation_pair",
    "filter_formation_events",
    # Data
    "CDM",
    "CDMObject",
    "SpaceTrackClient",
]
