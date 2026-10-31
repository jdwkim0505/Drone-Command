"""Gymnasium environment: the neural network writes a whole plan, the simulator scores it.

Each episode is a single step. The network sees the battlefield (observation), outputs one
plan (action), the strike plays out in sim.py, and the reward says how well it went.
"""
import random

import gymnasium as gym
import numpy as np

from plans import FIELDS, SLOTS, decode
from sim import BUDGET, KINDS, OBJECTIVES, build_city, plan_cost, simulate

TOTAL_OBJECTIVE_HP = sum(KINDS[k]["hp"] for k in OBJECTIVES)


def reward(result):
    """What the AI is trying to maximize. This is the main thing to experiment with.

    Right now: big points per objective destroyed, a little for any damage on objectives
    (so it gets credit for progress before it can destroy things), a bonus for killing the
    radar, and a small penalty for spending budget.
    """
    damage = TOTAL_OBJECTIVE_HP - result["objective_hp_left"]
    return (10 * result["objectives_destroyed"]
            + 2 * damage
            + 3 * result["radar_destroyed"]
            - 0.001 * result["cost_pts"])


def observe():
    """What the network sees: every enemy unit as (kind id, x, y, hp, ammo), scaled to about -1..1.

    On the fixed map this never changes, but it's the hook for later stages where defenses
    move or vary from game to game.
    """
    kinds = list(KINDS)
    feats = []
    for t in build_city(random.Random(0)):
        feats += [kinds.index(t.kind) / len(kinds), t.x / 1000, t.y / 1000, t.hp / 4, (t.ammo or 0) / 8]
    feats.append(BUDGET / 4000)
    return np.array(feats, dtype=np.float32)


class BarrageEnv(gym.Env):
    def __init__(self, seed=None):
        super().__init__()
        self.action_space = gym.spaces.MultiDiscrete(FIELDS * SLOTS)
        obs = observe()
        self.observation_space = gym.spaces.Box(-2, 2, shape=obs.shape, dtype=np.float32)
        self._obs = obs
        self._rng = random.Random(seed)
        self.last = None

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        if seed is not None:
            self._rng.seed(seed)
        return self._obs, {}

    def step(self, action):
        plan = decode(action)
        result = simulate(plan, seed=self._rng.randrange(1 << 30))
        self.last = result
        info = dict(result, over_budget=max(0, plan_cost(plan) - BUDGET))
        return self._obs, float(reward(result)), True, False, info
