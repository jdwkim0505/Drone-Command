# Barrage AI strategist

A neural network that learns to plan Barrage strikes by playing thousands of them against a
Python copy of the game.

## Setup

```bash
cd ai
python -m venv .venv && source .venv/bin/activate   # optional but tidy
pip install -r requirements.txt
```

## Files

| File | What it does |
| --- | --- |
| `sim.py` | Headless Barrage simulator: the fixed map from the game, same rules, no graphics. `simulate(plan, seed)` runs one strike in ~20 ms and returns what happened. Run it directly for a speed test. |
| `plans.py` | Turns 25 integers (5 salvos × type, target, route, count, delay) into a plan. This is the network's "vocabulary". |
| `doctrines.py` | **One reward function per strategist.** Same network, same simulator; only what it's rewarded for changes. Add your own here. |
| `env.py` | Gymnasium environment. One episode = one plan = one strike, scored by the chosen doctrine. |
| `optimize.py` | Genetic algorithm baseline. No neural network: random plans that evolve. The score to beat. |
| `train.py` | Trains a strategist with PPO (Stable-Baselines3) and saves `models/<doctrine>.zip`. |
| `export_plan.py` | Opens the real game in your browser with the model's plan loaded, and flies it. |

## Run it

```bash
python sim.py            # sanity check + speed
python optimize.py       # baseline, ~1 minute
python train.py                     # the general strategist, 100k strikes
python train.py 100000 economist    # another doctrine
python train.py 100000 all          # every doctrine, one after another (slow)
tensorboard --logdir runs           # watch the reward curves (in another terminal)
python export_plan.py blitz         # watch a strategist's plan play out in the game
```

`export_plan.py --all-js` prints every trained strategist with its plan and average results. Paste it over `AI_PLANS` in `../index.html` to update the **AI strategists** picker in the game's Barrage planner.

## The strategists

| Doctrine | Rewarded for |
| --- | --- |
| `general` | Objectives destroyed; cost barely matters |
| `economist` | Damage per dollar: every $1M costs about one objective's worth |
| `blitz` | Speed: each objective is worth more the sooner it falls |
| `attrition` | Cost exchange: defender dollars burned minus our dollars spent |
| `surgeon` | Precision: fewest munitions launched and lost |
| `decapitation` | Command post and radar destroyed, the sooner the better |

## How it fits together

1. The network sees the battlefield (`observe()` in `env.py`: every enemy unit's type, position, HP and ammo).
2. It outputs 25 integers, which `plans.decode()` turns into up to 5 salvos.
3. `sim.simulate()` plays the strike out with random dice rolls.
4. The doctrine's reward scores it, and PPO nudges the network's ~211k weights toward plans that scored well.

## Ideas for next steps

- **Invent a doctrine.** Write a new reward in `doctrines.py`, add it to `DOCTRINES`, train it. The AI optimizes exactly what you reward.
- **Randomize the map** (stage 2): jitter defense positions and SAM ammo each episode in `build_city()`, so it has to learn strategy instead of memorizing one answer. This is where the network should start beating the genetic algorithm.
- **More route options** in `plans.route()`, or let the network place waypoints directly.

The simulator mirrors the rules in `../index.html`. If you change balance numbers in the game, change them in `sim.py` too.
