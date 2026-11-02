"""Genetic algorithm baseline: no neural network, just evolution.

Start with random plans, score each one in the simulator, keep the best, breed and mutate
them, repeat. Whatever score this reaches is the bar the neural network has to beat.

    python optimize.py
"""
import random
import sys

from doctrines import general as reward
from plans import ALL_FIELDS, N, SLOTS, decode, decode_sites, describe, random_action
from sim import simulate

POP, GENERATIONS, SEEDS, ELITE = 40, 30, 3, 8


def fitness(action, seeds):
    # dice rolls vary, so average a few strikes per plan
    return sum(reward(simulate(decode(action), s, sites=decode_sites(action))) for s in seeds) / len(seeds)


def mutate(a, rng, rate=0.15):
    a = list(a)
    for i in range(len(a)):
        if rng.random() < rate:
            a[i] = rng.randrange(ALL_FIELDS[i])
    return a


def crossover(a, b, rng):
    # swap whole salvos so a good salvo stays intact
    return [x for i in range(SLOTS) for x in (a if rng.random() < 0.5 else b)[i * N:(i + 1) * N]] + list((a if rng.random() < 0.5 else b)[SLOTS * N:])


def main(seed=0):
    rng = random.Random(seed)
    pop = [random_action(rng) for _ in range(POP)]
    best, best_fit = None, float("-inf")
    for gen in range(GENERATIONS):
        seeds = [rng.randrange(1 << 30) for _ in range(SEEDS)]
        scored = sorted(((fitness(a, seeds), a) for a in pop), key=lambda p: -p[0])
        if scored[0][0] > best_fit:
            best_fit, best = scored[0]
        print(f"gen {gen:2d}  best {scored[0][0]:6.1f}  mean {sum(f for f, _ in scored) / POP:6.1f}", flush=True)
        elite = [a for _, a in scored[:ELITE]]
        pop = elite + [mutate(crossover(rng.choice(elite), rng.choice(elite), rng), rng) for _ in range(POP - ELITE)]
    # re-test the winner on fresh dice so the number is honest
    final = [simulate(decode(best), 10_000 + s, sites=decode_sites(best)) for s in range(50)]
    print("\nbest plan:\n" + describe(best))
    print(f"\nover 50 fresh strikes: reward {sum(reward(r) for r in final) / 50:.1f}, "
          f"objectives destroyed {sum(r['objectives_destroyed'] for r in final) / 50:.2f} of 5")
    return best


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 0)
