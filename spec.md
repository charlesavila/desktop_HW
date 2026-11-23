# Your App's Name

Bridge Builder: 60 ft Truss Challenge

## Purpose
This Tkinter engineering game lets students design a pin-jointed truss across a
60 ft gap and test it with increasingly heavy vehicles. It combines an
easy-to-use drawing tool with a method-of-joints solver so the player can find
the least-cost bridge that carries every vehicle.

## Platform

- Python desktop app using Tkinter, started with `python app.py`
- Calculations with numpy, kept in their own module, separate from
  the window code
- Diagrams drawn with matplotlib, embedded in the window
- Added features: Build/Test modes, 1 ft grid joint/member drawing, live
  stability checking, animated vehicles, capacity-based member colors,
  failure stopping, cost scoreboard, and an expandable validation details
  panel.
- Project process: after each request, record what was asked, what changed,
  and whether it worked in `prompts.md`.

## Inputs
- Build/Test mode selector (buttons).
- In Build mode, click empty grid locations to place joints at integer
  coordinates from x = 0 to 60 ft and y = 0 to 30 ft; click two joints to add
  a member. The fixed deck joints at (0, 0), (10, 0), ..., (60, 0) are
  provided, and the pin at x = 0 and roller at x = 60 cannot be moved or
  deleted.
- Clear/reset button (button), plus a selectable joint/member for deletion
  (button) except for the required supports.
- In Test mode, choose Car, Loaded dump truck, Semi (AASHTO HS20 design
  truck), or Fire engine from a dropdown, then use Drive/Pause and Reset
  buttons. The vehicle's front axle position is shown in feet and advances
  across the 0--60 ft deck.
- A Details toggle opens the force/reaction tables; it is closed initially.
  The player does not edit loads, capacities, costs, or the grid spacing.

## Calculations
- A member between joints i and j has length
  `L = sqrt((xj-xi)^2 + (yj-yi)^2)` ft, and costs `$100 L`. Each non-fixed
  joint costs $500; total cost is the sum of those two terms.
- For each joint, use unknown member axial forces (positive in tension) and
  support reactions. For member i-j, its direction cosines are
  `cx = (xj-xi)/L` and `cy = (yj-yi)/L`. Assemble the method-of-joints
  equations `sum(Fx) = 0` and `sum(Fy) = 0` as one linear system
  `A u = b`, where `u` contains member forces and the pin's x/y and roller's
  y reaction, all in lb. Applied axle loads are downward and are distributed
  linearly to the two deck joints surrounding the axle: the nearer joint gets
  the larger share.
- A design is stable only when `number_of_members + 3 = 2 *
  number_of_joints` and the coefficient matrix is not nearly singular
  (condition check/tolerance). Otherwise show “Unstable truss” instead of
  force numbers.
- Tension capacity is 90,000 lb and compression capacity is 75,000 lb.
  For a member force F, utilization is `F/90,000` when F >= 0 and
  `abs(F)/75,000` when F < 0. During testing, green is below 0.60,
  yellow is 0.60--0.85, red is 0.85--1.00, and black is over capacity.
- A vehicle is stopped when any member utilization exceeds 1.00. A vehicle
  counts as carried only if it reaches the far support without a failure.

## Outputs
- The main matplotlib bridge diagram shows the 60 ft site, 10 ft grid,
  joints, pin/roller supports, members, and the vehicle with wheels.
- The current cost is displayed in dollars, along with joint count, member
  count, stability status, and a scoreboard marking each vehicle as not
  tested, carried, or failed.
- While driving, members change green/yellow/red/black according to their
  utilization and the animation shows the vehicle moving from left to right.
  A black member and a clear failure message stop the vehicle.
- The Details panel provides a joint table (coordinates, applied load, and
  reactions) and a member table (end joints, length in ft, force in lb,
  tension/compression, capacity, and utilization). Stable designs show
  numeric values; unstable designs show the instability message.

## Look and feel
- Use a clean engineering-workbench layout: controls and status on the left,
  a large light-background bridge canvas in the center, and the optional
  details panel below or beside it. The initial screen opens in Build mode
  with the required six-panel deck, supports, empty member set, cost, and a
  short hint such as “Click a grid point to place a joint.”
- The Build hint changes after the first joint selection to explain that the
  next click will connect a member; Test mode hides drawing controls and
  replaces them with vehicle controls.
- Use readable labels, a legend for member colors, and buttons large enough
  for classroom use. The desktop layout is primary; on a narrow phone-sized
  window, stack the controls above the canvas and allow the details table to
  scroll horizontally rather than attempting to support touch drawing.

## Validation
- Case 1 (hand calculation): use the required six-panel, 10 ft tall Pratt
  truss, then place the semi's front axle at x = 44 ft. The axle locations
  are x = 44, 58, and 74 ft with loads 8,000, 32,000, and 32,000 lb.
  Taking moments about the left support gives
  `R_B = (8,000*44 + 32,000*58 + 32,000*74)/60 =
  76,266.7 lb`; vertical equilibrium gives `R_A = -4,266.7 lb`.
  The app's reaction table must match these values within 1 lb. Use the
  method-of-sections force values in the app's member table for the top chord,
  bottom chord, and diagonal in panel x = 20--30 and report them below.
- Case 2 (reference load data): select Car. Its two 2,000 lb axles at 0 and
  10 ft total 4,000 lb, so the reaction sum must be 4,000 lb and the
  scoreboard must report Car carried by a sound bridge.
- Case 3 (property check): mirror a symmetric truss and apply a centered
  axle load. Mirrored joints must have equal-and-opposite horizontal
  coordinates, equal corresponding member utilization, and equal support
  reactions within numerical tolerance.

**Validation results**

| Case | Expected | Actual |
|---|---|---|
| Semi at front axle x = 44 ft | Left reaction -4,266.7 lb; right reaction 76,266.7 lb (hand calculation) | App details table: left -4,266.7 lb; right 76,266.7 lb |
| Car load total | 4,000 lb total vertical reaction (reference vehicle data) | Automated solver check: 4,000 lb total axle load and support reaction |
| Mirrored centered load | Corresponding utilization values and reactions symmetric (property check) | Automated check passed: 5,000 lb at each support; mirrored member utilization matches within 1e-8 |

At least one case must be confirmed by running the app, and the actual
column must be updated with the displayed values before submission. The
Pratt bridge should carry the car and dump truck and fail under the semi;
the fire-engine result is also recorded by the scoreboard.

## Out of scope
- No arbitrary span length, moving supports, non-grid joints, or editable
  axle loads/capacities/cost constants.
- No 3-D, dynamic vibration, fatigue, wind, seismic, material self-weight,
  buckling, deflection, or nonlinear analysis; members are ideal pin-jointed
  axial elements.
- No online leaderboard, accounts,file sharing, or phone-native app.
- The required validation design is a teaching model; it is not a
  construction-ready bridge design.
- Optional future enhancements, not required for the initial submission, are
  deflected-shape animation, buckling limits for long compression members,
  and a class leaderboard for the cheapest bridges.
