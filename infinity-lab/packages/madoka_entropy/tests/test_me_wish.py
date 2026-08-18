"""The karmic calculus: a wish nets ``(k-1)x > 0`` and the ledger is immutable.

These are the per-event building blocks behind the global invariant: every wish
exports ``x`` units of local order at a strictly larger global cost ``k*x``, so
the net total change is ``(k-1)*x > 0``. Also covers soul-gem purity decay and
the incubator's positive-surplus-only harvest.
"""

from __future__ import annotations

import pytest

from madoka_entropy.core.entropy import EntropyLedger, wish_deltas
from madoka_entropy.core.incubator import Incubator
from madoka_entropy.core.magical_girl import MagicalGirl, make_girls


def test_wish_net_total_change_is_positive() -> None:
    d_global, d_local = wish_deltas(local_order=1.0, karmic_multiplier=1.8)
    assert d_local == pytest.approx(-1.0)
    assert d_global == pytest.approx(1.8)
    assert d_global + d_local > 0.0  # net entropy rises: (k-1)x


@pytest.mark.parametrize("x", [0.4, 1.0, 1.6, 5.0])
@pytest.mark.parametrize("k", [1.05, 1.8, 3.0])
def test_wish_net_equals_k_minus_one_times_x(x: float, k: float) -> None:
    d_global, d_local = wish_deltas(local_order=x, karmic_multiplier=k)
    assert d_global + d_local == pytest.approx((k - 1.0) * x)
    assert d_global + d_local > 0.0


def test_multiplier_must_exceed_one() -> None:
    with pytest.raises(ValueError):
        wish_deltas(1.0, 1.0)


def test_order_must_be_positive() -> None:
    with pytest.raises(ValueError):
        wish_deltas(0.0, 1.8)


def test_ledger_is_immutable_copy_on_change() -> None:
    a = EntropyLedger(100.0, 50.0, 0.0)
    b = a.with_changes(d_global=5.0)
    assert a.global_entropy == 100.0   # original untouched
    assert b.global_entropy == 105.0
    assert a.total_entropy == 150.0


def test_cast_decays_purity_and_imposes_order() -> None:
    g = MagicalGirl("Sayaka", purity=1.0, local_entropy=20.0)
    g2 = g.cast(local_order=2.0, decay_per_order=0.1)
    assert g2.purity == pytest.approx(0.8)
    assert g2.local_entropy == pytest.approx(18.0)
    assert g.purity == 1.0  # original untouched (immutable)


def test_purity_clamped_at_zero() -> None:
    g = MagicalGirl("Kyoko", purity=0.05, local_entropy=5.0)
    g2 = g.cast(local_order=10.0, decay_per_order=1.0)
    assert g2.purity == 0.0


def test_make_girls_start_pure() -> None:
    girls = make_girls(("Madoka", "Homura"), base_local_entropy=20.0)
    assert len(girls) == 2
    assert all(g.purity == 1.0 and not g.is_witch for g in girls)


def test_incubator_harvests_only_positive_surplus() -> None:
    inc = Incubator(harvest_fraction=0.5)
    assert inc.harvest_from_wish(1.8, -1.0) == pytest.approx(0.4)
    assert inc.harvest_from_wish(0.0, 0.0) == 0.0
    assert inc.harvest_from_witch(10.0) == pytest.approx(5.0)
    assert inc.harvest_from_witch(-3.0) == 0.0


def test_incubator_rejects_bad_fraction() -> None:
    with pytest.raises(ValueError):
        Incubator(harvest_fraction=1.5)
