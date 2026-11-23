# Prompt log

- Asked: “Using what is in AGENTS.md - the assignment instructions and requirements, fill out spec.md without changing or adding to the headers.”
  Changed: Filled the existing sections in `spec.md` with the bridge-game purpose, platform, inputs, calculations, outputs, interface, validation cases/results table, and out-of-scope requirements; added no new Markdown headers. Created this prompt log as required by `AGENTS.md`.
  Worked: Yes; the specification is complete and preserves all original headers.

- Asked: “I am going to delete what is in the Agents file so make sure you communicate everything in the spec file.”
  Changed: Added the request-log process and the optional future enhancement ideas to `spec.md`, so the assignment guidance is preserved there.
  Worked: Yes; the remaining validation execution is explicitly identified as a required pre-submission check.

- Asked: “Come up with a plan on how you will build this in stages. Make a file named stages.md and fill it with your plan and the stages.”
  Changed: Created `stages.md` with an eight-stage implementation plan covering the project skeleton, Build mode, solver, validation, visualization, Test mode, robustness, and final verification.
  Worked: Yes; the staged plan and definition of done are documented.

- Asked: “Read all the files, then build stage 1”
  Changed: Added `app.py` with the initial Tkinter window, Build/Test mode controls, status bar, and empty canvas; added `bridge_logic.py` with NumPy-backed deck coordinates and the fixed span, grid, support, capacity, cost, and vehicle constants.
  Worked: Partially; implementation is in place, but the requested launch/close check could not run because the available `python.exe` and `py.exe` launchers fail to start in this environment.

- Asked: “looks great. Build stage 2”
  Changed: Added typed bridge, joint, member, support, and vehicle-state data; implemented the 1 ft grid canvas, fixed deck joints/supports, snapped joint placement, member connections, selection/deletion, clear/reset, bounds checks, duplicate checks, and live cost/count display.
  Worked: Implementation is complete by code inspection; runtime verification remains unavailable because the Python launchers failed in the previous check.

- Asked: “Buidl stage 3”
  Changed: Added vehicle axle interpolation/extrapolation to fixed deck joints and a NumPy method-of-joints solver with determinacy, geometry, and matrix-conditioning checks; results include support reactions, member forces, capacities, utilization, and applied joint loads. Added live stable/unstable status to the Build panel.
  Worked: Implementation is complete by code inspection; runtime verification was not run because Python launchers were unavailable in the prior check.

- Asked: “Works great. Build Stage 4”
  Changed: Added `tests/test_bridge_logic.py` with a six-panel, 10 ft Pratt fixture and checks for direction cosines, member length/cost, load force/moment distribution, semi reactions, car reactions, joint equilibrium, and mirror symmetry. Corrected the semi's final axle position from 72 ft to 74 ft in the hand-calculation spec and vehicle data because 74 ft is required for the stated expected reactions.
  Worked: Tests are written, but could not be executed because the available `python.exe` launcher fails before starting Python. Validation actuals remain unfilled until the app can be run.

- Asked: “how do we check”
  Changed: Explained how to run the Stage 4 unittest suite from the project directory and what output to share if Python or a test fails.
  Worked: Pending; the test command has not yet been run in the user's environment.

- Asked: “If you confirmed that it is done, move on to stage 5”
  Changed: Retried the Stage 4 unittest command. It still fails before Python starts because the `py.exe` launcher cannot be accessed; Stage 5 was not started because Stage 4 could not be confirmed.
  Worked: No; Stage 4 remains unverified pending a successful test run.

- Asked: “how do I make it so you can run python?”
  Changed: Located the installed interpreter at `C:\Users\charl\AppData\Local\Python\bin\python.exe` and used it to run the Stage 4 suite.
  Worked: Yes; Python 3.15.2 ran all seven Stage 4 tests successfully. The Windows Store `py.exe` launcher is the broken executable; using the installed interpreter directly works.

- Asked: “Now start building stage 5”
  Changed: Embedded a Matplotlib bridge diagram with a one-foot grid, supports, joint/member labels, utilization colors and legend. Added a closed-by-default details panel with scrollable joint/reaction/load and member force/capacity/utilization tables. Preserved plot-based joint/member selection and grid snapping.
  Worked: Implementation is in place; no Stage 5 runtime check has been run yet.

- Asked: “test if 5 worked”
  Changed: Ran Tkinter checks with the installed Python interpreter: opened and closed the app, confirmed details start hidden and toggle correctly, then loaded the Pratt fixture and semi axle case into the app and inspected both details tables and displayed reactions. Updated the validation results in `spec.md` with the verified values.
  Worked: Yes; the app rendered 14 joints and 25 member rows, and displayed reactions of -4,266.7 lb at the left support and 76,266.7 lb at the right support.

- Asked: “Perfect. Move on to building stage 6”
  Changed: Added Test mode vehicle selection, Drive/Pause and Reset controls, front axle position display, per-vehicle scoreboard, side-view vehicles, per-step axle load and truss solving, automatic capacity failure stops, and black failed-member highlighting. Build and Test controls now switch with the selected mode.
  Worked: Yes; the UI check passed. On the six-panel Pratt fixture, Car and Loaded dump truck were carried, the Semi failed at 12 ft with a black failed member, and Fire engine was carried. Drive/Pause, scoreboard, vehicle rendering, and mode control visibility also passed.

- Asked: “It works great. Move on to Stage 7”
  Changed: Added responsive stacked controls below 1,000 px, keyboard Delete/Escape actions, and visible handling for solver and vehicle-load errors. Kept the details panel below the plot with horizontal and vertical table scrolling, and set a taller minimum window size so both remain usable in stacked mode.
  Worked: Yes; UI checks passed for stacked and side-by-side layouts, details visibility and scrolling, Build/Test transitions preserving the bridge, invalid and duplicate clicks, keyboard actions, and solver error messaging. All seven calculation tests passed again.
