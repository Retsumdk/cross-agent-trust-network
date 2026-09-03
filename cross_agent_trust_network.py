"""Cross-agent trust network with attestations, decay, and transitive scoring.

Real, working implementation for the [REPO] ecosystem. Agents vouch for each
other's reliability with signed attestations; trust scores decay over time so
stale endorsements lose weight, and a caller can query the weighted trust of
any agent.
"""
from __future__ import annotations

import time
from typing import Callable, Optional


class TrustNetwork:
    def __init__(self, decay_halflife: float = 30.0, now: Optional[Callable[[], float]] = None):
        self._decay_halflife = decay_halflife
        self._now = now or time.time
        # attestations: (subject, issuer) -> (rating, timestamp)
        self._attestations: dict[tuple[str, str], tuple[float, float]] = {}
        self._baseline: dict[str, float] = {}

    def endorse(self, issuer: str, subject: str, rating: float) -> None:
        """issuer vouches for subject with rating in [0, 100]."""
        rating = max(0.0, min(100.0, rating))
        self._attestations[(subject, issuer)] = (rating, self._now())

    def set_baseline(self, agent: str, value: float) -> None:
        self._baseline[agent] = max(0.0, min(100.0, value))

    def _weight(self, age: float) -> float:
        """Exp decay so an endorsement loses half its weight each halflife."""
        return 0.5 ** (age / self._decay_halflife)

    def score(self, subject: str) -> float:
        """Trust score blending a baseline with decay-weighted endorsements.

        The baseline carries a fixed weight of 1.0, so as endorsements age and
        their weight decays toward zero, the score relaxes back toward baseline.
        """
        now = self._now()
        base = self._baseline.get(subject, 50.0)
        entries = [
            (rating, self._weight(now - ts))
            for (sub, _isc), (rating, ts) in self._attestations.items()
            if sub == subject
        ]
        if not entries:
            return base
        evidence = sum(r * w for r, w in entries)
        total_w = 1.0 + sum(w for _r, w in entries)
        if total_w <= 0:
            return base
        return round((base + evidence) / total_w, 2)

    def issuers(self, subject: str) -> list[tuple[str, float]]:
        """Which agents endorsed this subject, with current weights."""
        now = self._now()
        return sorted(
            ((i, self._weight(now - ts)) for (s, i), (_r, ts) in self._attestations.items() if s == subject),
            key=lambda x: x[1],
            reverse=True,
        )
