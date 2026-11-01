"""Watch the trained model's plan play out in the real game.

    python export_plan.py                # opens the game and flies the general strategist's plan
    python export_plan.py economist      # same, for another doctrine (see doctrines.py)
    python export_plan.py --live         # same, but on jdwkim0505.com instead of ../index.html
    python export_plan.py --link         # just print the link (no autoplay)
    python export_plan.py --js           # print the plan as JSON
    python export_plan.py --all-js       # print every trained strategist, to paste over AI_PLANS in index.html

The game loads the plan into the Barrage planner, shows it for a moment, then launches it.
"""
import base64
import json
import os
import sys
import webbrowser

from stable_baselines3 import PPO

from doctrines import DOCTRINES
from env import BarrageEnv
from plans import decode, decode_sites, describe
from sim import simulate

LIVE = "https://jdwkim0505.com/drone-command/"


def plan_list(action):
    out = []
    for s in decode(action):
        d = dict(type=s["type"], count=s["count"], delay=s["delay"], route=[[round(x), round(y)] for x, y in s["route"]])
        if s["site"]:
            d["site"] = 1
        if s["alt"]:
            d["alt"] = [round(v) for v in s["alt"]]
        out.append(d)
    return out


def plan_json(action):
    return json.dumps(plan_list(action), separators=(",", ":"))


def best_action(doctrine, strike_seed=0):
    """The strategist's plan for one recon picture (the game bakes in the plan for strike 0)."""
    model = PPO.load(f"models/{doctrine}")
    obs = BarrageEnv().reset(options=dict(strike_seed=strike_seed))[0]
    return model.predict(obs, deterministic=True)[0]


def sites_json(action):
    st = decode_sites(action)
    r = lambda p: [round(p[0]), round(p[1])]
    return dict(trucks=[r(p) for p in st["trucks"]], ship=r(st["ship"]), mother=r(st["mother"]))


def all_js():
    """Every trained strategist with its plan and its average result over 50 simulated strikes."""
    out = {}
    for d, (_, name, blurb) in DOCTRINES.items():
        if not os.path.exists(f"models/{d}.zip"):
            continue
        action = best_action(d)
        # the same fixed plan flown against 50 different defense layouts, like replaying it in the game
        rs = [simulate(decode(action), 10_000 + s, sites=decode_sites(action)) for s in range(50)]
        avg = lambda k: sum(r[k] for r in rs) / len(rs)
        out[d] = dict(name=name, blurb=blurb, plan=plan_list(action), sites=sites_json(action), stats=dict(
            objectives=round(avg("objectives_destroyed"), 2), cost=round(avg("cost_usd")),
            enemy=round(avg("enemy_spend")), launched=round(avg("launched")), lost=round(avg("intercepted"), 1),
            finish=round(sum(max(r["kill_times"].values(), default=0) for r in rs) / len(rs), 1)))
    return json.dumps(out, separators=(",", ":"))


def plan_link(action, live=False, play=True):
    payload = json.dumps(dict(salvos=plan_list(action), sites=sites_json(action)), separators=(",", ":"))
    code = base64.urlsafe_b64encode(payload.encode()).decode().rstrip("=")
    here = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "index.html"))
    base = LIVE if live else "file://" + here
    return f"{base}?plan={code}" + ("&play" if play else "")


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    if "--all-js" in sys.argv:
        print(all_js())
        sys.exit()
    names = [a for a in sys.argv[1:] if not a.startswith("--")]
    action = best_action(names[0] if names else "general")
    if "--js" in sys.argv:
        print(plan_json(action))
        sys.exit()
    print(describe(action))
    link = plan_link(action, live="--live" in sys.argv, play="--link" not in sys.argv)
    if "--link" in sys.argv:
        print("\n" + link)
    else:
        print("\nOpening the game...")
        webbrowser.open(link)
