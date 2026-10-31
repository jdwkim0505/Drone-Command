# Drone Command: Swarm Command prototype

A browser prototype of StarCraft 2-style unit control applied to a swarm of kamikaze drones. Open `index.html` in any modern browser. There's no build step and nothing to install.

New here? Start with the [Quickstart](QUICKSTART.md).

## Modes

- **Sandbox:** free play. Spawn air and sea drones, place targets, enemy boats and jamming zones, and try anything. The south edge of the map is sea, with a dock for sea drones.
- **Base Assault:** a timed challenge. Destroy an enemy base's command post (3 hits), radar and fuel depot (2 hits) within 5 minutes. Two air-defense sites shoot down drones inside their dashed range rings, a jammer tower blankets the command post, and three interceptor drones patrol or hold station. An interceptor chases any drone that enters its dotted detection ring and rams it (80% kill), then returns home if the chase drags it too far. You can strike interceptors too, and head-on works best since they fly straight at you. You start with 8 drones and can launch 16 more from the pad with **D**, 4 at a time. Fewer drones used earns more stars.

- **Coastal Strike:** air and sea together. Sink a frigate (4 HP) and destroy a coastal missile battery (2 hits) and a radar within 6 minutes. The frigate carries air defense and guns, two patrol boats screen it, and air defense plus an interceptor cover the shore. You start with 6 air drones and 3 sea drones. **D** launches 4 more air drones (10 in reserve) and **N** launches 2 more sea drones (4 in reserve).
- **Barrage:** a plan-then-launch siege mode with no micro. You get an 80-point budget to route salvos of one-way attack munitions into a defended coastal city with five objectives. Once launched, they fly their program.
  - **Munitions:** Shahed-style drones (2 pts, slow, 1 damage), decoys (1 pt, no warhead), cruise missiles (8 pts, fast and low, 3 damage) and sea drones (5 pts, water only, 3 damage).
  - **Defenses:** two SAM sites with 8 missiles each, a radar that cues them (without it they see less, especially low cruise missiles), gun teams, interceptor drones, GPS jamming that makes Shaheds and decoys drift off course, a patrol boat, and a frigate with its own missiles and gun.
  - **Planning:** press 1–4 (or click a munition), click waypoints from the launch site, then right-click the target. In the panel you can set each salvo's size and launch time, then press **Space** to launch.
  - **In flight:** you can only watch at 1×, 2× or 4× speed, except that each Shahed salvo can be redirected once over its satellite link.
  - **The AI's plan:** the **Load the AI's plan** button fills the planner with the best plan found by the neural network in [`ai/`](ai/README.md).
  - **Results:** the end card shows what got through, what shot your munitions down, and the cost exchange (your munitions against the enemy's interceptor spend). **Retry** keeps your plan so you can refine it.

The **Menu** button in the top bar switches modes.

## Controls

| Input | Action |
| --- | --- |
| Click / drag | Select one drone / box select (Shift adds) |
| Double-click, Ctrl+A, F2 | Select on screen / select all |
| Right-click | Move (Shift queues waypoints) |
| Right-click a target | Strike it with all selected drones |
| A, then click | Attack-move: strike targets on the way |
| S, then click a target | Stalk at a distance, camera locked on |
| H, then click a target | Hover directly overhead, top-down camera |
| P, then click | Patrol |
| X / G | Stop / Hold position |
| B | Return to the launch pad and swap batteries (sea drones refuel at the sea dock) |
| N | Place a sea drone at the cursor (over water); in missions, launch 2 from the sea dock |
| V | Place an enemy patrol boat at the cursor (over water) |
| D / T | Spawn a drone / place a target at the cursor |
| I | Place an enemy interceptor drone at the cursor |
| J | Place a jamming zone at the cursor (J inside one removes it) |
| Del | Remove selected drones |
| Alt+1–0, Shift+1–0, 1–0 | Bind, add to, recall control groups (tap twice to jump) |
| Tab | Cycle the camera feed through the selection |
| Q / E, Z / C (hold) | Pan / tilt the selected drone's camera |
| Arrows, middle-drag, wheel | Pan and zoom the map |

## How it works

- **Kamikaze strikes:** each drone is used up on impact and kills with the probability set by the Kill chance slider (60% by default). Drones that are left over stay in the group.
- **FPV feed:** a simulated camera for the selected drone. It has a stabilized gimbal, shows targets as 3D tanks seen from the drone's actual angle, shows friendly drones with IFF markers, puts edge arrows on targets that are out of frame, and switches to a top-down view while hovering.
- **Jamming zones:** red circles on the map cut the link between operator and drone. A drone that enters one shows LINK LOST on its feed and stops taking orders. If it was already diving on a target, it finishes the strike blind and the feed never shows the result. Otherwise its failsafe flies it back out to the edge, where the link comes back.
- **Battery:** each drone has about 60 seconds of flight on a full pack, shown as a bar under it, in the selection panel and on its feed. When a drone has just enough charge to make it home, it calls **BINGO** and flies back to the launch pad on its own unless it's already diving on a target. You can override that, but a drone that runs dry falls out of the sky. A drone parked on the pad stops draining and gets a fresh pack in 3 seconds. Press **B** to send the selection home early.
- **Sea drones:** explosive boats modeled on the uncrewed surface vessels Ukraine uses in the Black Sea. They only move on water and slide along the shoreline, so they can strike ships and targets right on the shore but nothing inland. They're slower than air drones (about two thirds the speed) but carry a much bigger warhead: an 85% hit chance and 3 damage per hit. They have three minutes of fuel and refuel at the sea dock. Air defense and interceptors can't touch them, but ship guns can. Their camera sits just above the waves.
- **Group movement:** clicking outside the group keeps its formation, clicking inside pulls the drones together, and drones push apart so they don't stack.
