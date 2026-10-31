"""Headless Barrage simulator.

A Python port of the Barrage mode rules in ../index.html, with no graphics. It runs one
whole strike from launch to the last impact and returns what happened:

    from sim import simulate
    result = simulate(plan, seed=0)

A plan is a list of salvos. Each salvo is a dict:

    {"type": "shahed",            # shahed | decoy | cruise | usv
     "count": 6,
     "delay": 0,                  # seconds after launch before the first one leaves
     "route": [(x, y), ..., (tx, ty)]}   # waypoints, the last point is where it strikes

The map is the fixed Barrage map from the game: same city, same defenses. The only
randomness is the dice rolls (hits, intercepts, GPS drift), driven by `seed`, so the same
plan and seed always give the same result.
"""
import math
import random

# ---------- rules (kept in step with index.html) ----------
DT = 0.1                  # simulation step in seconds; the game uses its frame time (~0.016)
MAX_TIME = 240.0          # safety cap on a single strike
BUDGET = 80

MUNITIONS = {
    "shahed": dict(cost=2, usd=50e3, speed=55, damage=1, blast=12, gap=0.7, slow=True, low=False, sea=False, drift=1.0),
    "decoy": dict(cost=1, usd=10e3, speed=60, damage=0, blast=0, gap=0.5, slow=True, low=False, sea=False, drift=1.0),
    "cruise": dict(cost=8, usd=1.5e6, speed=210, damage=3, blast=16, gap=1.2, slow=False, low=True, sea=False, drift=0.15),
    "usv": dict(cost=5, usd=250e3, speed=62, damage=3, blast=18, gap=1.0, slow=False, low=False, sea=True, drift=0.0),
}
TYPES = list(MUNITIONS)

# target sizes (half length, half width) used for blast checks, and hit points
KINDS = {
    "plant": dict(hp=3, hl=14, hw=10), "substation": dict(hp=2, hl=9, hw=9), "fuel": dict(hp=2, hl=11, hw=7),
    "port": dict(hp=2, hl=16, hw=6), "cp": dict(hp=3, hl=13, hw=9), "radar": dict(hp=1, hl=6, hw=6),
    "sam": dict(hp=2, hl=7, hw=7, range=250), "gun": dict(hp=1, hl=4, hw=4, range=90),
    "interceptor": dict(hp=1, hl=6, hw=6, detect=150, leash=300),
    "frigate": dict(hp=4, hl=22, hw=5.5, range=170, gun=110, speed=9),
    "boat": dict(hp=1, hl=8, hw=2.6, gun=120, speed=28),
}
OBJECTIVES = ["plant", "substation", "fuel", "port", "cp"]

SAM_RELOAD, SAM_SPEED = 1.2, 300.0
SAM_PK_SLOW, SAM_PK_LOW = 0.85, 0.7
GUN_RELOAD, GUN_PK = 0.5, 0.06
SHIP_GUN_RELOAD = 1.2
DRONE_SPEED = 95.0
INT_SPEED, INT_PK, INT_RELOAD = DRONE_SPEED * 1.35, 0.65, 1.5
SAM_USD, SHIP_SAM_USD, INTERCEPTOR_USD = 3e6, 1.2e6, 20e3

PAD = (-880.0, -40.0)     # air launch site
DOCK = (-860.0, 380.0)    # sea launch site
JAM = (120.0, -40.0, 140.0)  # GPS jamming zone: x, y, radius
COAST = (170.0, 1.1)


def coast_y(x):
    y0, ph = COAST
    return y0 + 45 * math.sin(x / 210 + ph) + 20 * math.sin(x / 83 + 2 * ph)


def to_water(x, y):
    """Sea drones aim at the nearest water just off the shore, like the game's planner does."""
    return x, max(y, coast_y(x) + 12)


def wrap(a):
    return math.atan2(math.sin(a), math.cos(a))


def plan_cost(plan):
    return sum(s["count"] * MUNITIONS[s["type"]]["cost"] for s in plan)


class Target:
    __slots__ = ("kind", "x", "y", "hp", "dead", "ammo", "cd", "cd2", "home", "wp", "to_wp", "dir",
                 "vx", "vy", "ang", "prey")

    def __init__(self, kind, x, y, rng):
        self.kind, self.x, self.y = kind, float(x), float(y)
        self.hp, self.dead = KINDS[kind]["hp"], False
        self.ammo, self.cd, self.cd2 = None, 0.0, 0.0
        self.home, self.wp, self.to_wp, self.dir = (self.x, self.y), None, False, -math.pi / 2
        self.vx = self.vy = 0.0
        self.ang = rng.random() * 6.3
        self.prey = None


class Munition:
    __slots__ = ("type", "m", "salvo", "x", "y", "heading", "route", "i", "ex", "ey", "engaged", "dead")

    def __init__(self, mtype, salvo, x, y, route):
        self.type, self.m, self.salvo = mtype, MUNITIONS[mtype], salvo
        self.x, self.y, self.heading = x, y, 0.0
        self.route, self.i = route, 0
        self.ex = self.ey = 0.0      # GPS error walked in by jamming
        self.engaged = 0             # SAM missiles in flight toward it
        self.dead = False


def build_city(rng):
    """The defended city from setupBarrage() in index.html."""
    t = []
    add = lambda kind, x, y: t.append(Target(kind, x, y, rng)) or t[-1]
    add("plant", 620, -120)
    add("substation", 360, 40)
    add("fuel", 720, 30)
    add("port", 500, coast_y(500) - 10)
    add("cp", 560, -330)
    add("radar", 430, -200)
    add("sam", 300, -60).ammo = 8
    add("sam", 640, -250).ammo = 8
    for x, y in [(160, -130), (230, 70), (520, 20), (450, -330)]:
        add("gun", x, y)
    add("interceptor", 260, -220)
    add("interceptor", 560, -40)
    fr = add("frigate", 480, 400)
    fr.ammo, fr.wp, fr.dir = 6, (640, 380), 0.0
    b = add("boat", 200, 320)
    b.wp = (40, 300)
    return t


def simulate(plan, seed=0, budget=BUDGET):
    """Run one strike. Salvos past the budget are trimmed, in order."""
    rng = random.Random(seed)
    # trim to budget
    salvos, left = [], budget
    for s in plan:
        c = MUNITIONS[s["type"]]["cost"]
        n = min(int(s["count"]), left // c)
        if n > 0:
            salvos.append(dict(s, count=n, fired=0, hits=0, lost=0))
            left -= n * c
    targets = build_city(rng)
    munitions, missiles = [], []
    stats = dict(intercepted=0, impacts=0, sam_shots=0, enemy_spend=0.0, lost_to={})
    clock = 0.0

    def down(m, by):
        m.dead = True
        m.salvo["lost"] += 1
        stats["intercepted"] += 1
        stats["lost_to"][by] = stats["lost_to"].get(by, 0) + 1

    def fire(s):
        k = s["fired"]
        start = DOCK if MUNITIONS[s["type"]]["sea"] else PAD
        off = (1 if k % 2 else -1) * math.ceil(k / 2) * 6
        pts = [(float(x), float(y)) for x, y in s["route"]]
        if MUNITIONS[s["type"]]["sea"]:
            pts = [to_water(x, y) for x, y in pts]
        route = [p if i == len(pts) - 1 else (p[0], p[1] + off) for i, p in enumerate(pts)]
        munitions.append(Munition(s["type"], s, start[0], start[1] + off, route))
        s["fired"] += 1

    def impact(m):
        m.dead = True
        if not m.m["damage"]:
            return
        ex, ey = m.x + (rng.random() - 0.5) * 10, m.y + (rng.random() - 0.5) * 10
        best, bd = None, float("inf")
        for t in targets:
            if t.dead:
                continue
            k = KINDS[t.kind]
            d = math.hypot(t.x - ex, t.y - ey) - max(k["hl"], k["hw"])
            if d < m.m["blast"] and d < bd:
                best, bd = t, d
        if best is None:
            return
        best.hp = max(0, best.hp - m.m["damage"])
        stats["impacts"] += 1
        m.salvo["hits"] += 1
        if best.hp <= 0:
            best.dead = True

    def nearest(t, pool, r):
        best, bd = None, r
        for m in pool:
            d = math.hypot(m.x - t.x, m.y - t.y)
            if d < bd:
                best, bd = m, d
        return best

    while clock < MAX_TIME:
        clock += DT
        dt = DT
        for s in salvos:
            while s["fired"] < s["count"] and clock >= s["delay"] + s["fired"] * MUNITIONS[s["type"]]["gap"]:
                fire(s)

        # munitions fly their program
        jx, jy, jr = JAM
        for m in munitions:
            if m.dead:
                continue
            M = m.m
            if M["drift"] and math.hypot(m.x - jx, m.y - jy) < jr:
                m.ex = max(-70, min(70, m.ex + (rng.random() - 0.5) * 160 * dt * M["drift"]))
                m.ey = max(-70, min(70, m.ey + (rng.random() - 0.5) * 160 * dt * M["drift"]))
            px, py = m.route[m.i]
            gx, gy = px + m.ex, py + m.ey
            dx, dy = gx - m.x, gy - m.y
            dist, step = math.hypot(dx, dy), M["speed"] * dt
            want = math.atan2(dy, dx)
            m.heading += wrap(want - m.heading) * min(1.0, dt * (3 if M["slow"] else 6))
            if dist <= step + 2:
                m.x, m.y = gx, gy
                if m.i == len(m.route) - 1:
                    impact(m)
                else:
                    m.i += 1
                continue
            m.x += math.cos(m.heading) * step
            m.y += math.sin(m.heading) * step
            if M["sea"]:
                shore = coast_y(m.x) + 4
                if m.y < shore:
                    m.y = shore

        # SAM missiles in flight
        for ms in missiles:
            m = ms["target"]
            if not m.dead:
                ms["tx"], ms["ty"] = m.x, m.y
            dx, dy = ms["tx"] - ms["x"], ms["ty"] - ms["y"]
            dist, step = math.hypot(dx, dy), SAM_SPEED * dt
            if dist > step + 4:
                ms["x"] += dx / dist * step
                ms["y"] += dy / dist * step
                continue
            ms["done"] = True
            m.engaged -= 1
            if not m.dead and rng.random() < (SAM_PK_LOW if m.m["low"] else SAM_PK_SLOW):
                down(m, "SAMs")
        missiles = [ms for ms in missiles if not ms.get("done")]

        # defenses
        live = [m for m in munitions if not m.dead]
        air = [m for m in live if not m.m["sea"]]
        radar = any(t.kind == "radar" and not t.dead for t in targets)
        for t in targets:
            if t.dead:
                continue
            k = KINDS[t.kind]
            if t.kind in ("frigate", "boat"):
                g = t.wp if t.to_wp else t.home
                dx, dy = g[0] - t.x, g[1] - t.y
                if math.hypot(dx, dy) < 8:
                    t.to_wp = not t.to_wp
                else:
                    t.dir += wrap(math.atan2(dy, dx) - t.dir) * min(1.0, dt * 0.8)
                    t.x += math.cos(t.dir) * k["speed"] * dt
                    t.y += math.sin(t.dir) * k["speed"] * dt
                t.cd2 -= dt
                if t.cd2 <= 0:
                    m = nearest(t, [q for q in live if not q.dead and (q.m["sea"] or q.m["slow"])], k["gun"])
                    if m:
                        t.cd2 = SHIP_GUN_RELOAD
                        if rng.random() < (0.3 if m.m["sea"] else 0.2):
                            down(m, "ships")
                if not t.ammo:
                    continue
            if t.kind in ("sam", "frigate"):
                t.cd -= dt
                if t.cd > 0 or not t.ammo:
                    continue
                r, best, bd = k["range"], None, float("inf")
                for m in air:
                    if m.dead or m.engaged:
                        continue
                    eff = r * ((0.7 if radar else 0.4) if m.m["low"] else (1.0 if radar else 0.6))
                    d = math.hypot(m.x - t.x, m.y - t.y)
                    if d < eff and d < bd:
                        best, bd = m, d
                if best is None:
                    continue
                t.cd = SAM_RELOAD
                t.ammo -= 1
                best.engaged += 1
                stats["sam_shots"] += 1
                stats["enemy_spend"] += SAM_USD if t.kind == "sam" else SHIP_SAM_USD
                missiles.append(dict(x=t.x, y=t.y, tx=best.x, ty=best.y, target=best))
            elif t.kind == "gun":
                t.cd -= dt
                if t.cd > 0:
                    continue
                m = nearest(t, [q for q in air if not q.dead], k["range"])
                if m:
                    t.cd = GUN_RELOAD
                    if rng.random() < (GUN_PK * 0.3 if m.m["low"] else GUN_PK):
                        down(m, "guns")
            elif t.kind == "interceptor":
                t.cd -= dt
                if t.prey and (t.prey.dead or math.hypot(t.prey.x - t.home[0], t.prey.y - t.home[1]) > k["leash"]):
                    t.prey = None
                if t.prey is None:
                    pool = [m for m in air if not m.dead and m.m["slow"]
                            and math.hypot(m.x - t.home[0], m.y - t.home[1]) < k["leash"]]
                    t.prey = nearest(t, pool, k["detect"])
                if t.prey:
                    gx, gy, sp = t.prey.x, t.prey.y, INT_SPEED
                else:
                    t.ang += dt * 0.7
                    gx, gy, sp = t.home[0] + math.cos(t.ang) * 45, t.home[1] + math.sin(t.ang) * 45, DRONE_SPEED * 0.6
                dx, dy = gx - t.x, gy - t.y
                dist = math.hypot(dx, dy) or 0.01
                t.vx += (dx / dist * sp - t.vx) * 6 * dt
                t.vy += (dy / dist * sp - t.vy) * 6 * dt
                t.x += t.vx * dt
                t.y += t.vy * dt
                if t.prey and dist < 8 and t.cd <= 0:
                    t.cd = INT_RELOAD
                    stats["enemy_spend"] += INTERCEPTOR_USD
                    if rng.random() < INT_PK:
                        down(t.prey, "interceptor drones")
                        t.prey = None

        munitions = [m for m in munitions if not m.dead]
        if not munitions and not missiles and all(s["fired"] >= s["count"] for s in salvos):
            break

    destroyed = [k for k in OBJECTIVES if not any(t.kind == k and not t.dead for t in targets)]
    return dict(
        objectives_destroyed=len(destroyed),
        destroyed=destroyed,
        radar_destroyed=not any(t.kind == "radar" and not t.dead for t in targets),
        objective_hp_left=sum(t.hp for t in targets if t.kind in OBJECTIVES and not t.dead),
        hits=stats["impacts"],
        intercepted=stats["intercepted"],
        lost_to=stats["lost_to"],
        launched=sum(s["count"] for s in salvos),
        cost_pts=plan_cost(salvos),
        cost_usd=sum(s["count"] * MUNITIONS[s["type"]]["usd"] for s in salvos),
        enemy_spend=stats["enemy_spend"],
        sam_shots=stats["sam_shots"],
        time=round(clock, 1),
    )


if __name__ == "__main__":
    import time
    # the same sample plan used to test the game: decoys, cruise on the radar, two Shahed waves, USVs on the port
    city = {t.kind: (t.x, t.y) for t in build_city(random.Random(0))}
    plan = [
        dict(type="decoy", count=6, delay=0, route=[(0, -300), (330, -80)]),
        dict(type="cruise", count=2, delay=0, route=[(-200, 120), city["radar"]]),
        dict(type="shahed", count=6, delay=5, route=[(-100, -380), (400, -420), city["cp"]]),
        dict(type="shahed", count=6, delay=5, route=[(-100, -380), (700, -330), city["plant"]]),
        dict(type="usv", count=2, delay=0, route=[(300, 300), city["port"]]),
    ]
    t0 = time.time()
    runs = [simulate(plan, seed) for seed in range(50)]
    print(f"{(time.time() - t0) / 50 * 1000:.1f} ms per strike")
    print("avg objectives destroyed:", sum(r["objectives_destroyed"] for r in runs) / 50)
    print("example:", runs[0])
