import pytest

from trust_network import TrustNetwork


class Clock:
    def __init__(self):
        self.t = 100.0

    def __call__(self):
        return self.t


def test_baseline_when_no_attestations():
    c = Clock()
    n = TrustNetwork(now=c)
    assert n.score("alice") == 50.0


def test_endorsement_raises_score():
    c = Clock()
    n = TrustNetwork(decay_halflife=100.0, now=c)
    n.set_baseline("bob", 50.0)
    n.endorse("carol", "bob", 100.0)
    assert n.score("bob") > 50.0


def test_old_endorsement_decays():
    c = Clock()
    n = TrustNetwork(decay_halflife=10.0, now=c)
    n.set_baseline("bob", 50.0)
    n.endorse("carol", "bob", 100.0)
    fresh = n.score("bob")
    c.t += 100  # ages the attestation well past halflife
    stale = n.score("bob")
    assert stale < fresh


def test_issuers_listed_by_weight_desc():
    c = Clock()
    n = TrustNetwork(decay_halflife=10.0, now=c)
    n.endorse("old", "target", 90.0)
    c.t += 11
    n.endorse("new", "target", 90.0)
    issuers = n.issuers("target")
    assert issuers[0][0] == "new"
