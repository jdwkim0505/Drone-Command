"""Turns the numbers a neural network (or the genetic algorithm) outputs into a Barrage plan.

A plan has up to SLOTS salvos. Each salvo is 5 small integers:

    [type, target, route, count, delay]
     type    0 = empty slot, 1 = shahed, 2 = decoy, 3 = cruise, 4 = usv
     target  which point on the map to strike (see AIM_POINTS)
     route   which of 4 corridors to fly (see route())
     count   0..7  ->  1..8 units (a unit is 4 Shaheds or decoys, or 1 missile or sea drone)
     delay   0..3  ->  launch at T+0, 5, 10 or 15 seconds

So a whole plan is SLOTS * 5 integers: exactly the shape of a MultiDiscrete action in Gymnasium.
"""
import random
from sim import build_city, coast_y, MUNITIONS, TYPES

SLOTS = 5
FIELDS = [5, 8, 4, 8, 4]          # number of choices for each of the 5 numbers in a salvo
AIM_ORDER = ["plant", "substation", "fuel", "port", "cp", "radar", "sam_west", "sam_east"]


def _aim_points():
    pts, sams = {}, []
    for t in build_city(random.Random(0)):
        if t.kind == "sam":
            sams.append((t.x, t.y))
        elif t.kind in AIM_ORDER:
            pts[t.kind] = (t.x, t.y)
    sams.sort()
    pts["sam_west"], pts["sam_east"] = sams
    return [pts[k] for k in AIM_ORDER]


AIM_POINTS = _aim_points()


def route(mtype, r, tx, ty):
    """Waypoints for corridor r (0-3) toward the target at (tx, ty)."""
    if mtype == "usv":
        sea = max(300, coast_y(tx) + 60)
        return [[(tx, sea)], [(tx - 160, 460), (tx, sea)], [(-300, 300), (tx, sea)], [(-200, 480), (tx + 120, 420)]][r] + [(tx, ty)]
    return [
        [],                                    # 0: straight in
        [(-100, -430), (tx, -460)],            # 1: wide northern arc, dives in from the north
        [(-300, 250), (tx - 80, 250)],         # 2: low over the sea, comes in from the south
        [(-150, -280)],                        # 3: dogleg north of the GPS jamming zone
    ][r] + [(tx, ty)]


def decode(action):
    """Integer action vector -> plan (list of salvo dicts) for sim.simulate()."""
    plan = []
    for i in range(SLOTS):
        typ, tgt, rte, cnt, dly = (int(v) for v in action[i * 5:(i + 1) * 5])
        if typ == 0:
            continue
        mtype = TYPES[typ - 1]
        tx, ty = AIM_POINTS[tgt]
        plan.append(dict(type=mtype, count=(cnt + 1) * MUNITIONS[mtype]["unit"], delay=dly * 5, route=route(mtype, rte, tx, ty),
                         target=AIM_ORDER[tgt], corridor=rte))
    return plan


def describe(action):
    """Human-readable summary of a plan."""
    names = ["straight", "north arc", "over the sea", "dogleg"]
    lines = []
    for s in decode(action):
        lines.append(f"{s['count']}x {s['type']:<6} -> {s['target']:<10} via {names[s['corridor']]:<12} at T+{s['delay']}s")
    return "\n".join(lines) or "(empty plan)"


def random_action(rng=random):
    return [rng.randrange(n) for _ in range(SLOTS) for n in FIELDS]
