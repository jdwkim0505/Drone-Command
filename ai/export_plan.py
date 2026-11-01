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
from plans import decode, describe
from sim import simulate

LIVE = "https://jdwkim0505.com/drone-command/"


def plan_list(action):
    return [dict(type=s["type"], count=s["count"], delay=s["delay"],
                 route=[[round(x), round(y)] for x, y in s["route"]]) for s in decode(action)]


def plan_json(action):
    return json.dumps(plan_list(action), separators=(",", ":"))


def best_action(doctrine):
    model = PPO.load(f"models/{doctrine}")
    return model.predict(BarrageEnv().reset()[0], deterministic=True)[0]


def all_js():
    """Every trained strategist with its plan and its average result over 50 simulated strikes."""
    out = {}
    for d, (_, name, blurb) in DOCTRINES.items():
        if not os.path.exists(f"models/{d}.zip"):
            continue
        action = best_action(d)
        rs = [simulate(decode(action), 10_000 + s) for s in range(50)]
        avg = lambda k: sum(r[k] for r in rs) / len(rs)
        out[d] = dict(name=name, blurb=blurb, plan=plan_list(action), stats=dict(
            objectives=round(avg("objectives_destroyed"), 2), cost=round(avg("cost_usd")),
            enemy=round(avg("enemy_spend")), launched=round(avg("launched")), lost=round(avg("intercepted"), 1),
            finish=round(sum(max(r["kill_times"].values(), default=0) for r in rs) / len(rs), 1)))
    return json.dumps(out, separators=(",", ":"))


def plan_link(action, live=False, play=True):
    code = base64.urlsafe_b64encode(plan_json(action).encode()).decode().rstrip("=")
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
