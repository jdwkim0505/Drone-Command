"""Doctrines: one reward function per AI strategist.

Every strategist uses the same network shape, the same simulator and the same plan format.
The only thing that differs is what it gets rewarded for, and that alone is enough to make
them fight very differently. Train one with:

    python train.py 100000 economist

Each reward takes the result dict from sim.simulate() and returns a number to maximize.
"""
from sim import KINDS, OBJECTIVES

TOTAL_OBJECTIVE_HP = sum(KINDS[k]["hp"] for k in OBJECTIVES)


def _damage(r):
    return TOTAL_OBJECTIVE_HP - r["objective_hp_left"]


def general(r):
    """Destroy as much as possible. Cost barely matters."""
    return 10 * r["objectives_destroyed"] + 2 * _damage(r) + 3 * r["radar_destroyed"] - 0.00005 * r["cost_pts"]


def economist(r):
    """Results per dollar. Every $5M spent costs about as much as one objective is worth."""
    return 10 * r["objectives_destroyed"] + 2 * _damage(r) - 0.002 * r["cost_pts"]


def blitz(r):
    """Speed. Each objective is worth more the sooner it falls; one lost after 90 s earns nothing extra."""
    early = sum(max(0.0, 90 - t) / 9 for k, t in r["kill_times"].items() if k in OBJECTIVES)
    return 6 * r["objectives_destroyed"] + _damage(r) + early


def attrition(r):
    """Cost exchange. Make the defender burn expensive interceptors on cheap drones."""
    return (4 * r["objectives_destroyed"] + _damage(r)
            + 1.0 * r["enemy_spend"] / 1e6 - 3.0 * r["cost_usd"] / 1e6)


def surgeon(r):
    """Precision. Destroy targets with as few munitions as possible and lose as few as possible."""
    return 10 * r["objectives_destroyed"] + 2 * _damage(r) - 0.5 * r["launched"] - 1.0 * r["intercepted"]


def decapitation(r):
    """Blind and behead: the command post and radar matter most, and the sooner the better."""
    kt = r["kill_times"]
    score = 4 * r["objectives_destroyed"] + _damage(r)
    for k, w in (("cp", 20), ("radar", 12)):
        if k in kt:
            score += w + max(0.0, 60 - kt[k]) / 6
    return score


DOCTRINES = {
    "general": (general, "General", "Destroys the most, cost barely matters"),
    "economist": (economist, "Economist", "Most damage per dollar"),
    "blitz": (blitz, "Blitz", "Fastest destruction"),
    "attrition": (attrition, "Attrition", "Drains the defender's interceptor budget"),
    "surgeon": (surgeon, "Surgeon", "Fewest munitions, fewest losses"),
    "decapitation": (decapitation, "Decapitation", "Command post and radar first"),
}
