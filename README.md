# Drone Command: Swarm Command prototype

A browser prototype of StarCraft 2-style unit control applied to a swarm of kamikaze drones. Open `index.html` in any modern browser. There's no build step and nothing to install.

New here? Start with the [Quickstart](QUICKSTART.md).

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
| D / T | Spawn a drone / place a target at the cursor |
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
- **Group movement:** clicking outside the group keeps its formation, clicking inside pulls the drones together, and drones push apart so they don't stack.
