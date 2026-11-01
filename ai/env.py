"""Gymnasium environment: the neural network writes a whole plan, the simulator scores it.

Each episode is a single step. The network sees the battlefield (observation), outputs one
plan (action), the strike plays out in sim.py, and the reward says how well it went.
"""
import random

import gymnasium as gym
import numpy as np

from plans import FIELDS, SLOTS, decode
from sim import BUDGET, KINDS, build_city, plan_cost, simulate

from doctrines import DOCTRINES, general as reward   # noqa: F401  (reward kept for old scripts)


def observe():
    """What the network sees: every enemy unit as (kind id, x, y, hp, ammo), scaled to about -1..1.

    Mobile units (short-range SAMs, mobile gun groups, interceptor teams) are left out: they move
    every strike, so the network has to plan for defenses it can't see.
    """
    kinds = list(KINDS)
    feats = []
    # only the fixed sites known from imagery: mobile units move every strike and may not be located
    for t in build_city(random.Random(0)):
        if t.mobile:
            continue
        feats += [kinds.index(t.kind) / len(kinds), t.x / 1000, t.y / 1000, t.hp / 4, (t.ammo or 0) / 8]
    feats.append(BUDGET / 4000)
    return np.array(feats, dtype=np.float32)


class BarrageEnv(gym.Env):
    def __init__(self, seed=None, doctrine="general"):
        super().__init__()
        self.reward_fn = DOCTRINES[doctrine][0]
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
        return self._obs, float(self.reward_fn(result)), True, False, info
