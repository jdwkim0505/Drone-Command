"""Train the neural network strategist with PPO.

    python train.py                     # the general strategist, ~100k strikes
    python train.py 300000              # train longer
    python train.py 100000 economist    # train another doctrine (see doctrines.py)
    python train.py 100000 all          # train every doctrine, one after another
    tensorboard --logdir runs           # watch the reward curve while it trains

Saves models/<doctrine>.zip when done.
"""
import os
import sys

import importlib.util

import numpy as np
from stable_baselines3 import PPO
from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3.common.vec_env import SubprocVecEnv

from doctrines import DOCTRINES
from env import BarrageEnv
from plans import decode, describe
from sim import simulate


def evaluate(model, n=50):
    obs = BarrageEnv().reset()[0]
    action, _ = model.predict(obs, deterministic=True)   # its single best guess
    results = [simulate(decode(action), 10_000 + s) for s in range(n)]
    return action, results


def main(steps, doctrine="general"):
    reward = DOCTRINES[doctrine][0]
    print(f"\n=== training {doctrine} ===")
    envs = make_vec_env(BarrageEnv, n_envs=os.cpu_count() or 1, vec_env_cls=SubprocVecEnv,
                        env_kwargs=dict(doctrine=doctrine))
    model = PPO(
        "MlpPolicy", envs,
        n_steps=256,              # strikes per env before each update
        batch_size=256,
        learning_rate=3e-4,
        ent_coef=0.01,            # keeps it exploring instead of locking in early
        policy_kwargs=dict(net_arch=[256, 256]),
        # reward curves go to runs/ when tensorboard is installed (pip install tensorboard)
        tensorboard_log=f"runs/{doctrine}" if importlib.util.find_spec("tensorboard") else None, verbose=1,
    )
    print(f"network has {sum(p.numel() for p in model.policy.parameters()):,} weights")
    model.learn(total_timesteps=steps)
    os.makedirs("models", exist_ok=True)
    model.save(f"models/{doctrine}")
    action, results = evaluate(model)
    print("\nlearned plan:\n" + describe(action))
    print(f"\nover 50 fresh strikes: reward {np.mean([reward(r) for r in results]):.1f}, "
          f"objectives destroyed {np.mean([r['objectives_destroyed'] for r in results]):.2f} of 5, "
          f"cost ${np.mean([r['cost_usd'] for r in results]) / 1e6:.2f}M, "
          f"defender spent ${np.mean([r['enemy_spend'] for r in results]) / 1e6:.1f}M, "
          f"{np.mean([r['launched'] for r in results]):.0f} launched, {np.mean([r['intercepted'] for r in results]):.1f} lost")


if __name__ == "__main__":
    steps = int(sys.argv[1]) if len(sys.argv) > 1 else 100_000
    which = sys.argv[2] if len(sys.argv) > 2 else "general"
    for d in (DOCTRINES if which == "all" else [which]):
        main(steps, d)
