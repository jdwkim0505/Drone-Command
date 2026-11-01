"""Turns the numbers a neural network (or the genetic algorithm) outputs into a Barrage plan.

The network gets the same choices a player has in the planner (everything except God view):

A plan has up to SLOTS salvos. Each salvo is 7 small integers:

    [type, target, route, count, delay, backup, site]
     type    0 = empty slot, 1 = shahed, 2 = decoy, 3 = cruise, 4 = usv, 5 = tomahawk
     target  which point on the map to strike (see AIM_POINTS)
     route   which of 6 corridors to fly (see route())
     count   0..7  ->  1..8 units (a unit is 8 Shaheds or decoys, 2 missiles or 1 sea drone)
     delay   0..7  ->  launch at T+0, 5, ... 35 seconds
     backup  0 = automatic (nearest surviving objective), 1.. = divert to that AIM_POINT if the
             target falls before the salvo arrives
     site    Shaheds and decoys: 0 = truck site A, 1 = truck site B (ignored for other types)

After the salvos come 4 more integers that place the launch sites, like dragging them in the
planner: truck site A, truck site B, the missile ship and the mothership, each picking one of
4 positions that all respect the game's standoff rules (see SITE_OPTIONS).

So a whole plan is SLOTS * 7 + 4 integers: exactly the shape of a MultiDiscrete action in Gymnasium.
"""
import random
from sim import DOCK, SHIP, TRUCKS, build_city, coast_y, MUNITIONS, TYPES

SLOTS = 8
AIM_ORDER = ["plant", "substation", "fuel", "port", "cp", "radar", "coastal_radar", "sam_west", "sam_east"]
ROUTES = ["straight", "north arc", "over the sea", "dogleg", "far south", "east hook"]
FIELDS = [len(TYPES) + 1, len(AIM_ORDER), len(ROUTES), 8, 8, len(AIM_ORDER) + 1, 2]   # choices for each number in a salvo
N = len(FIELDS)

# launch site positions the network can pick from; every one is legal under the planner's standoff rules
SITE_OPTIONS = {
    "truck_a": [TRUCKS[0], (-600.0, -60.0), (-700.0, -250.0), (-500.0, -200.0)],
    "truck_b": [TRUCKS[1], (-450.0, -430.0), (-300.0, -480.0), (-900.0, -300.0)],
    "ship": [SHIP, (-300.0, 700.0), (200.0, 950.0), (-1200.0, 900.0)],
    "mother": [DOCK, (-100.0, 560.0), (250.0, 840.0), (-900.0, 700.0)],
}
SITE_FIELDS = [len(v) for v in SITE_OPTIONS.values()]
ALL_FIELDS = FIELDS * SLOTS + SITE_FIELDS


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
    """Waypoints for corridor r toward the target at (tx, ty)."""
    if mtype == "usv":
        sea = max(300, coast_y(tx) + 60)
        return [[(tx, sea)],                                  # straight up from the south
                [(tx - 160, 460), (tx, sea)],                 # swing in from the south-west
                [(-300, 300), (tx, sea)],                     # hug the coast
                [(-200, 480), (tx + 120, 420)],               # come in from the south-east
                [(tx - 300, 800), (tx, 600), (tx, sea)],      # far out to sea, then straight north
                [(tx + 450, 600), (tx + 250, sea)],           # loop round and come in from the east
                ][r] + [(tx, ty)]
    return [
        [],                                        # 0: straight in
        [(-100, -430), (tx, -460)],                # 1: wide northern arc, dives in from the north
        [(-300, 250), (tx - 80, 250)],             # 2: low over the sea, comes in from the south
        [(-150, -280)],                            # 3: dogleg through the north-west
        [(-300, 520), (tx, 420)],                  # 4: far south over open water, then north
        [(-100, -520), (tx + 350, -420), (tx + 300, ty)],   # 5: hooks round and comes in from the east
    ][r] + [(tx, ty)]


def decode(action):
    """Integer action vector -> plan (list of salvo dicts) for sim.simulate()."""
    plan = []
    for i in range(SLOTS):
        typ, tgt, rte, cnt, dly, alt, site = (int(v) for v in action[i * N:(i + 1) * N])
        if typ == 0:
            continue
        mtype = TYPES[typ - 1]
        tx, ty = AIM_POINTS[tgt]
        plan.append(dict(type=mtype, count=(cnt + 1) * MUNITIONS[mtype]["unit"], delay=dly * 5, route=route(mtype, rte, tx, ty),
                         target=AIM_ORDER[tgt], corridor=rte,
                         alt=AIM_POINTS[alt - 1] if alt else None, backup=AIM_ORDER[alt - 1] if alt else "auto",
                         site=site if MUNITIONS[mtype]["slow"] else 0))
    return plan


def decode_sites(action):
    """The 4 trailing integers -> launch site positions for sim.simulate(..., sites=...)."""
    a, b, ship, mother = (int(v) for v in action[SLOTS * N:SLOTS * N + 4]) if len(action) > SLOTS * N else (0, 0, 0, 0)
    o = SITE_OPTIONS
    return dict(trucks=[o["truck_a"][a], o["truck_b"][b]], ship=o["ship"][ship], mother=o["mother"][mother])


def describe(action):
    """Human-readable summary of a plan."""
    lines = []
    for s in decode(action):
        site = f" from truck {'AB'[s['site']]}" if MUNITIONS[s['type']]['slow'] else ""
        lines.append(f"{s['count']}x {s['type']:<6} -> {s['target']:<13} via {ROUTES[s['corridor']]:<12} at T+{s['delay']}s"
                     f"{site}  (backup: {s['backup']})")
    st = decode_sites(action)
    lines.append(f"sites: trucks {st['trucks'][0]} {st['trucks'][1]}, ship {st['ship']}, mothership {st['mother']}")
    return "\n".join(lines)


def random_action(rng=random):
    return [rng.randrange(n) for n in ALL_FIELDS]
