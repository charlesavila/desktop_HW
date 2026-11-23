# Bridge Builder Implementation Stages

## Plan and sequencing

Build the application from the calculation core outward. Each stage should
leave the project runnable with `python app.py`, and later stages should reuse
the tested data structures and solver rather than duplicating logic.

## Stage 1: Project skeleton and constants

- Create `app.py` as the Tkinter entry point.
- Create a separate calculation module for numpy-based bridge logic.
- Define the fixed 60 ft span, 10 ft deck spacing, 1 ft grid, support types,
  member capacities, cost rates, and the four vehicle load definitions.
- Create the initial window, mode controls, status area, and empty drawing
  canvas.
- Verify the program starts and closes cleanly.

## Stage 2: Bridge model and Build mode

- Represent joints, members, supports, and vehicle state with clear typed
  structures.
- Draw the bridge site, deck joints, pin, roller, grid, joints, and members.
- Implement 1 ft grid snapping and reject points outside the allowed drawing
  area.
- Add the click workflow: place a joint, select a first joint, connect to a
  second joint, and show a hint describing the next action.
- Prevent deletion or movement of the required deck joints and supports.
- Add reset/clear behavior and calculate live joint/member cost.

## Stage 3: Truss solver

- Assemble one method-of-joints linear system with two equilibrium equations
  per joint.
- Include the pin x/y reactions and roller y reaction as unknowns.
- Implement axle-load distribution to neighboring deck joints, including
  interpolation based on distance.
- Check the determinacy rule `members + 3 = 2 * joints`.
- Check for a nearly singular system before solving and show “Unstable truss”
  instead of misleading force values.
- Return reactions, member forces, capacities, and utilization in a reusable
  result object.

## Stage 4: Solver tests and validation calculations

- Add focused checks for direction cosines, member lengths, cost, load
  distribution, and equilibrium.
- Build the specified six-panel, 10 ft Pratt truss as a test fixture.
- Verify the semi-at front axle x = 44 ft reactions:
  left reaction `-4,266.7 lb` and right reaction `76,266.7 lb`.
- Verify the car load totals 4,000 lb.
- Verify a mirrored truss with a centered load has matching corresponding
  forces and symmetric reactions.
- Record checked expected and actual values in the Validation results table in
  `spec.md` once the application can run.

## Stage 5: Drawing, details, and visual feedback

- Embed the matplotlib bridge diagram in the Tkinter window.
- Add member labels/colors and a legend for utilization levels: green,
  yellow, red, and black.
- Add the closed-by-default details panel.
- Show joint coordinates, applied loads, reactions, member lengths, forces,
  force type, capacities, and utilization in tables.
- Display stability, cost, joint count, and member count clearly.

## Stage 6: Test mode and vehicles

- Hide drawing tools in Test mode.
- Add the vehicle dropdown, drive/pause control, reset control, position
  display, and scoreboard.
- Draw each vehicle as a side-view body with wheels and animate its front axle
  across the bridge.
- Recompute axle distribution and member forces on each animation step.
- Color members by utilization, stop the vehicle when a member exceeds its
  capacity, turn the failed member black, and record carried/failed status.
- Test all four vehicles and ensure the specified Pratt bridge carries the car
  and dump truck and fails under the semi.

## Stage 7: Integrated UX and robustness

- Make Build/Test transitions preserve the current design and reset only
  vehicle-specific state when appropriate.
- Handle invalid clicks, duplicate members, zero-length members, unstable
  designs, and solver failures with visible messages.
- Confirm the details panel does not obscure the drawing and narrow windows
  stack controls and allow table scrolling.
- Check that all required controls are keyboard- and mouse-usable.

## Stage 8: Final verification and documentation

- Run the focused solver tests and launch the app with `python app.py`.
- Manually build the required Pratt truss and confirm at least one validation
  case in the running app.
- Complete the expected-versus-actual validation table in `spec.md`.
- Test the four-vehicle scoreboard and failure behavior.
- Review `spec.md`, `stages.md`, and `prompts.md` for consistency with the
  finished implementation.
- Record the final request outcome in `prompts.md`.

## Definition of done

The project is complete when the app starts with `python app.py`, supports
both required modes, solves stable trusses and reports unstable ones,
animates and stops vehicles according to capacity, displays the required
details and scoreboard, and has checked validation results documented in
`spec.md`.
