# Quickstart

Five minutes from opening the page to your first strike. The full controls list is in the [README](README.md), and the in-page **?** button shows it too.

## 0. Open it

Download `index.html` and open it in a desktop browser (Chrome, Edge, Firefox or Safari). There's nothing to install.

The map starts with two squads: **group 1** (6 drones, selected) and **group 2** (4 drones, on patrol). Four red targets are wandering around. The camera feed of the first selected drone is in the top-left.

## 1. Select and move

1. **Drag a box** around some drones to select them. Selected drones get a green ring.
2. **Right-click** the ground to move them there.
3. Hold **Shift** and right-click a few more spots to queue a route. Green lines show the queued path.
4. Press **X** to stop.

Tip: click away from the group and they keep their formation. Click inside the group and they pull together.

## 2. Save a squad

1. With drones selected, press **Alt+3** to save them as group 3.
2. Click empty ground to deselect, then press **3** to get them back.
3. Press **3** twice quickly to jump the map to them.

## 3. Watch the camera feed

1. Select a group. The feed shows the first drone's view.
2. Press **Tab** to step through each drone's camera.
3. Hold **Q / E** to pan the camera, and **Z / C** to tilt it. The camera keeps pointing that way while the drone flies.
4. Yellow brackets mark targets in view. Yellow arrows on the edge point to targets that are out of frame. Green markers are friendly drones.

## 4. Stalk a target

1. Select a few drones, press **S**, then click a target.
2. They shadow it at about 55m. The feed locks onto the tank with blue **TRACK** brackets.

## 5. Hover over a target

1. Press **H**, then click a target.
2. The drones park directly above it. When they're overhead, the feed switches to a top-down **NADIR VIEW**.

## 6. Strike

1. **Right-click a target** to send every selected drone at it.
2. Each drone is used up on impact and has the **Kill chance** (top bar, default 60%) to destroy it. Drones still in flight stop once the target is dead.
3. Watch the feed of a diving drone: red **LOCK** brackets, then **SIGNAL LOST** on impact.
4. Or press **A** and click the ground to attack-move. The drones fly there and strike anything they pass.

## 7. Build your own scenario

- **D** spawns a drone at the cursor, and the **Spawn** button adds four.
- **T** places a target at the cursor.
- **Del** removes the selected drones.
- Change the **Kill chance** slider to see how many drones a kill costs.

## 8. Fly into jamming

The red circle on the map is a jamming zone. Drones inside it lose their link to you.

1. Send a squad to a spot inside the circle. As each drone crosses the edge, its feed switches to **LINK LOST** and the failsafe flies it back out.
2. Now right-click the target inside the circle. The drones keep diving after the link drops and strike blind. The feed shows **NO FEED · RESULT UNKNOWN**, so you only learn the outcome from the map.
3. Orders sent to a drone inside the zone never arrive. The top bar tells you how many missed it.
4. Press **J** to drop a new zone at the cursor, or **J** inside one to remove it.

## 9. Manage batteries

Every drone carries about 60 seconds of charge. The bar under each drone shows what's left, turning orange and then red.

1. Send a squad far from the launch pad and watch the bars drain.
2. When a drone only has enough charge to get home, it calls **BINGO** and turns back by itself. Give it a new order and it obeys, but if the battery hits zero the drone is lost.
3. Press **B** to send the selection home early. On the pad, each drone swaps packs in 3 seconds and waits there fully charged.

## 10. Bring in sea drones

The blue area along the bottom of the sandbox map is sea. Group **3** holds two sea drones at the sea dock.

1. Press **3** and right-click somewhere out at sea. Sea drones are slower than air drones and stay on the water. Order them inland and they stop at the shoreline.
2. Press **V** with the cursor over water to place an enemy patrol boat. Its gun shoots at anything that comes close, so attack from more than one side at once.
3. Right-click the boat with the sea drones selected. Each sea drone hits 85% of the time for 3 damage, enough to sink most things in one blow.
4. Press **N** over water to add more sea drones. Mix them into a group with air drones and send everyone at the same target from the sky and the sea at once.

## 11. Try Base Assault

Click **Menu**, then **Base Assault**.

1. Your 8 drones start on the launch pad in the bottom left. The base is up and to the right, and the mission card shows the three objectives and the clock.
2. Stay out of the dashed red rings around the two **air defense** sites, or drones start getting shot down. Taking those out first makes everything else cheaper.
3. The **command post** sits inside the jammer's zone. Strikes still land blind, or you can destroy the **jammer** tower first to clear the zone.
4. Three red **interceptor drones** guard the base. Any of your drones inside an interceptor's dotted ring gets chased and rammed. Right-click an interceptor to strike it with your squad. It comes straight at you, so head-on strikes connect.
5. Press **D** to launch 4 more drones from your reserve of 16. The pad is also where your drones swap batteries, so cycle squads home with **B** instead of letting them run dry.
6. Destroy the command post, radar and fuel depot before the clock runs out. Fewer drones used earns more stars.

## 12. Try Coastal Strike

Click **Menu**, then **Coastal Strike**. This one mixes air and sea.

1. Group **1** is 6 air drones at the launch pad. Group **2** is 3 sea drones at the sea dock.
2. The **frigate** has 4 HP, air defense, and a gun for close range. One sea-drone hit does 3 damage, so pairing sea drones with an air strike sinks it fast.
3. The **missile battery** sits right on the beach, so sea drones can hit it from the water and stay away from the air defense ring inland.
4. The **radar** is inland, under air defense and an interceptor. Only air drones can reach it.
5. Watch out for the two **patrol boats**. They shoot at drones that come close.
6. **D** launches 4 more air drones, and **N** launches 2 more sea drones.

## 13. Try Barrage

Click **Menu**, then **Barrage**. No micro here: you plan the whole strike, launch it, and watch.

1. Press **1** for Shaheds, **2** for decoys, **3** for cruise missiles or **4** for sea drones.
2. Click waypoints from the launch site to route around defenses, then right-click the target. Backspace removes the last waypoint, and Esc cancels.
3. In the panel, set each salvo's size and launch time (T+0s, T+5s, …) within the 80-point budget.
4. Some ideas: send decoys first so the SAMs waste missiles on them. Cruise missiles on the radar blind the SAMs. Route Shaheds around the GPS jamming zone so they don't drift off course. Sea drones go for the port.
5. Press **Space** to launch, and use 1×, 2× or 4× to speed up time. Each Shahed salvo has one **Redirect** over satellite if a target is already destroyed.
6. The end card shows what killed your munitions and the cost exchange. **Retry** keeps your plan so you can tweak it.

## Cheat sheet

| Key | Does |
| --- | --- |
| Right-click | Move / strike a target |
| Shift | Queue the order |
| A · S · H · P | Attack-move · Stalk · Hover · Patrol (then click) |
| X · G | Stop · Hold |
| B | Return to pad, swap battery |
| N · V | Sea drone · enemy patrol boat (over water) |
| J | Place or remove a jamming zone |
| Alt+# · # | Save group · recall group |
| Tab | Next camera |
| Q/E · Z/C | Pan · tilt camera |
| D · T · I · Del | Spawn drone · place target · place interceptor · remove |
