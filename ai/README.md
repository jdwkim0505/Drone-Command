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
| `env.py` | Gymnasium environment. One episode = one plan = one strike. **`reward()` lives here**: it's the main thing to experiment with. |
| `optimize.py` | Genetic algorithm baseline. No neural network: random plans that evolve. The score to beat. |
| `train.py` | Trains the neural network with PPO (Stable-Baselines3) and saves `models/barrage_policy.zip`. |

## Run it

```bash
python sim.py            # sanity check + speed
python optimize.py       # baseline, ~1 minute
python train.py          # neural network, ~60k strikes; a few minutes on 4 cores
python train.py 300000   # train longer
tensorboard --logdir runs   # watch the reward curve (in another terminal)
```

## How it fits together

1. The network sees the battlefield (`observe()` in `env.py`: every enemy unit's type, position, HP and ammo).
2. It outputs 25 integers, which `plans.decode()` turns into up to 5 salvos.
3. `sim.simulate()` plays the strike out with random dice rolls.
4. `reward()` scores it, and PPO nudges the network's ~211k weights toward plans that scored well.

## Ideas for next steps

- **Tune the reward.** Should cost matter more? Should destroying the radar count? The AI optimizes exactly what you reward.
- **Randomize the map** (stage 2): jitter defense positions and SAM ammo each episode in `build_city()`, so it has to learn strategy instead of memorizing one answer. This is where the network should start beating the genetic algorithm.
- **More route options** in `plans.route()`, or let the network place waypoints directly.
- **Load the AI's plan into the game:** export the best plan as JSON and add an import button to the Barrage planner.

The simulator mirrors the rules in `../index.html`. If you change balance numbers in the game, change them in `sim.py` too.
