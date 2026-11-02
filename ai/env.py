"""Gymnasium environment: the neural network writes a whole plan, the simulator scores it.

Each episode is a single step. The network sees the battlefield (observation), outputs one
plan (action), the strike plays out in sim.py, and the reward says how well it went.
"""
import random

import gymnasium as gym
import numpy as np

from plans import ALL_FIELDS, decode, decode_sites
from sim import BUDGET, KINDS, build_city, plan_cost, simulate

from doctrines import DOCTRINES, general as reward   # noqa: F401  (reward kept for old scripts)


RECON_RATE = 0.5   # share of mobile units pre-strike reconnaissance finds, same as the game


def observe(seed):
    """What the network sees before the strike, exactly what a player sees without God view.

    Every enemy unit as (kind id, x, y, hp, ammo, located), scaled to about -1..1. Fixed sites are
    known from imagery. Mobile units (short-range SAMs, mobile gun groups, interceptor teams) move
    every strike, and recon only finds about half of them; the rest show up as zeros.
    """
    kinds = list(KINDS)
    recon = random.Random(seed ^ 0x5EED)
    feats = []
    for t in build_city(random.Random(seed)):   # same seed as simulate(), so same unit positions
        if t.mobile and recon.random() >= RECON_RATE:
            feats += [kinds.index(t.kind) / len(kinds), 0, 0, 0, 0, 0]
            continue
        feats += [kinds.index(t.kind) / len(kinds), t.x / 1000, t.y / 1000, t.hp / 4, (t.ammo or 0) / 16, 1]
    feats.append(BUDGET / 60000)
    return np.array(feats, dtype=np.float32)


class BarrageEnv(gym.Env):
    def __init__(self, seed=None, doctrine="general"):
        super().__init__()
        self.reward_fn = DOCTRINES[doctrine][0]
        self.action_space = gym.spaces.MultiDiscrete(ALL_FIELDS)
        obs = observe(0)
        self.observation_space = gym.spaces.Box(-2, 2, shape=obs.shape, dtype=np.float32)
        self._rng = random.Random(seed)
        self.strike_seed = 0
        self._obs = obs
        self.last = None

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        if seed is not None:
            self._rng.seed(seed)
        # a fresh strike: mobile defenses in new spots, a new recon picture
        self.strike_seed = (options or {}).get("strike_seed", self._rng.randrange(1 << 30))
        self._obs = observe(self.strike_seed)
        return self._obs, {}

    def step(self, action):
        plan = decode(action)
        result = simulate(plan, seed=self.strike_seed, sites=decode_sites(action))
        self.last = result
        info = dict(result, over_budget=max(0, plan_cost(plan) - BUDGET))
        return self._obs, float(self.reward_fn(result)), True, False, info
