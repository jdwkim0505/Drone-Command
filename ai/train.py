"""Train the neural network strategist with PPO.

    python train.py                 # ~60k strikes, a few minutes on a laptop
    python train.py 300000          # train longer
    tensorboard --logdir runs       # watch the reward curve while it trains

Saves models/barrage_policy.zip when done.
"""
import os
import sys

import importlib.util

import numpy as np
from stable_baselines3 import PPO
from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3.common.vec_env import SubprocVecEnv

from env import BarrageEnv, reward
from plans import decode, describe
from sim import simulate


def evaluate(model, n=50):
    obs = BarrageEnv().reset()[0]
    action, _ = model.predict(obs, deterministic=True)   # its single best guess
    results = [simulate(decode(action), 10_000 + s) for s in range(n)]
    return action, results


def main(steps):
    envs = make_vec_env(BarrageEnv, n_envs=os.cpu_count() or 1, vec_env_cls=SubprocVecEnv)
    model = PPO(
        "MlpPolicy", envs,
        n_steps=256,              # strikes per env before each update
        batch_size=256,
        learning_rate=3e-4,
        ent_coef=0.01,            # keeps it exploring instead of locking in early
        policy_kwargs=dict(net_arch=[256, 256]),
        # reward curves go to runs/ when tensorboard is installed (pip install tensorboard)
        tensorboard_log="runs" if importlib.util.find_spec("tensorboard") else None, verbose=1,
    )
    print(f"network has {sum(p.numel() for p in model.policy.parameters()):,} weights")
    model.learn(total_timesteps=steps)
    os.makedirs("models", exist_ok=True)
    model.save("models/barrage_policy")
    action, results = evaluate(model)
    print("\nlearned plan:\n" + describe(action))
    print(f"\nover 50 fresh strikes: reward {np.mean([reward(r) for r in results]):.1f}, "
          f"objectives destroyed {np.mean([r['objectives_destroyed'] for r in results]):.2f} of 5")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 60_000)
