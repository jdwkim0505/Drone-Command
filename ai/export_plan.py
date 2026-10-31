"""Watch the trained model's plan play out in the real game.

    python export_plan.py            # opens the game in your browser and flies the AI's plan
    python export_plan.py --live     # same, but on jdwkim0505.com instead of ../index.html
    python export_plan.py --link     # just print the link (no autoplay)
    python export_plan.py --js       # print the plan as JSON, to paste over AI_PLAN in index.html

The game loads the plan into the Barrage planner, shows it for a moment, then launches it.
"""
import base64
import json
import os
import sys
import webbrowser

from stable_baselines3 import PPO

from env import BarrageEnv
from plans import decode, describe

LIVE = "https://jdwkim0505.com/drone-command/"


def plan_json(action):
    salvos = [dict(type=s["type"], count=s["count"], delay=s["delay"],
                   route=[[round(x), round(y)] for x, y in s["route"]]) for s in decode(action)]
    return json.dumps(salvos, separators=(",", ":"))


def plan_link(action, live=False, play=True):
    code = base64.urlsafe_b64encode(plan_json(action).encode()).decode().rstrip("=")
    here = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "index.html"))
    base = LIVE if live else "file://" + here
    return f"{base}?plan={code}" + ("&play" if play else "")


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    model = PPO.load("models/barrage_policy")
    action, _ = model.predict(BarrageEnv().reset()[0], deterministic=True)
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
