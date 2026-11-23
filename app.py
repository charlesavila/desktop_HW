"""Tkinter entry point for Bridge Builder: 60 ft Truss Challenge."""

from math import hypot
import tkinter as tk
from tkinter import ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.patches import Circle, Rectangle
from matplotlib.ticker import MultipleLocator

from bridge_logic import (
    BridgeModel,
    SolveResult,
    SPAN_FT,
    VEHICLES,
    distribute_vehicle_loads,
    solve_bridge,
)


ANIMATION_DELAY_MS = 80
ANIMATION_STEP_FT = 1.0


class BridgeBuilderApp:
    """Bridge design window with drawing, solver feedback, and detail tables."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Bridge Builder: 60 ft Truss Challenge")
        self.root.minsize(640, 840)

        self.model = BridgeModel()
        self.mode = tk.StringVar(value="Build")
        self.status = tk.StringVar(value="Click an empty grid point to place a joint.")
        self.cost_display = tk.StringVar()
        self.count_display = tk.StringVar()
        self.stability_display = tk.StringVar()
        self.selected_joint: int | None = None
        self.selection: tuple[str, int] | None = None
        self.geometry: tuple[float, float, float] = (0.0, 0.0, 1.0)
        self.current_joint_loads: dict[int, float] = {}
        self.solve_result = solve_bridge(self.model)
        self.details_visible = False
        self.details_message = tk.StringVar(value="")
        self.vehicle_name = tk.StringVar(value="Car")
        self.vehicle_position_display = tk.StringVar(value="Front axle: 0.0 ft")
        self.vehicle_statuses = {name: "Not tested" for name in VEHICLES}
        self.failed_member_id: int | None = None
        self.animation_after_id: str | None = None

        self._build_layout()
        self.mode.trace_add("write", self._on_mode_changed)
        self._refresh_scoreboard()
        self._update_summary()
        self._draw()
        self.root.bind("<Delete>", self._on_delete_key)
        self.root.bind("<Escape>", self._clear_selection)
        self.root.bind("<Configure>", self._on_root_configure, add="+")
        self._stacked_layout: bool | None = None
        self._set_responsive_layout(self.root.winfo_width())

    def _build_layout(self) -> None:
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(0, weight=1)

        controls = ttk.Frame(self.root, padding=12)
        self.controls_frame = controls
        controls.grid(row=0, column=0, sticky="ns")

        ttk.Label(controls, text="Bridge Builder", font=("TkDefaultFont", 15, "bold")).pack(
            anchor="w", pady=(0, 12)
        )
        ttk.Label(controls, text="Mode").pack(anchor="w")
        mode_row = ttk.Frame(controls)
        mode_row.pack(anchor="w", pady=(4, 12))
        ttk.Radiobutton(mode_row, text="Build", value="Build", variable=self.mode).pack(
            side="left"
        )
        ttk.Radiobutton(mode_row, text="Test", value="Test", variable=self.mode).pack(
            side="left", padx=(8, 0)
        )

        ttk.Separator(controls).pack(fill="x", pady=8)
        ttk.Label(controls, text=f"Span: {SPAN_FT:g} ft").pack(anchor="w", pady=2)
        ttk.Label(controls, textvariable=self.count_display).pack(anchor="w", pady=2)
        ttk.Label(controls, textvariable=self.cost_display, font=("TkDefaultFont", 11, "bold")).pack(
            anchor="w", pady=(2, 10)
        )
        ttk.Label(controls, textvariable=self.stability_display).pack(anchor="w", pady=(0, 8))

        self.build_tools_frame = ttk.Frame(controls)
        self.build_tools_frame.pack(fill="x", pady=(4, 0))
        ttk.Label(self.build_tools_frame, text="Build tools", font=("TkDefaultFont", 10, "bold")).pack(
            anchor="w", pady=(0, 4)
        )
        ttk.Button(self.build_tools_frame, text="Delete selected", command=self._delete_selected).pack(
            fill="x", pady=3
        )
        ttk.Button(self.build_tools_frame, text="Clear / Reset", command=self._clear_design).pack(
            fill="x", pady=3
        )
        ttk.Label(
            self.build_tools_frame,
            text="Click empty grid to add a joint.\nClick two joints to connect them.\nSelect a member or joint, then delete.",
            justify="left",
            wraplength=190,
        ).pack(anchor="w", pady=(8, 0))

        self.test_tools_frame = ttk.Frame(controls)
        ttk.Label(self.test_tools_frame, text="Vehicle", font=("TkDefaultFont", 10, "bold")).pack(
            anchor="w", pady=(0, 4)
        )
        self.vehicle_picker = ttk.Combobox(
            self.test_tools_frame,
            textvariable=self.vehicle_name,
            values=tuple(VEHICLES),
            state="readonly",
            width=29,
        )
        self.vehicle_picker.pack(fill="x", pady=(0, 6))
        self.vehicle_picker.bind("<<ComboboxSelected>>", self._on_vehicle_selected)
        self.drive_button = ttk.Button(
            self.test_tools_frame, text="Drive", command=self._toggle_drive
        )
        self.drive_button.pack(fill="x", pady=3)
        ttk.Button(self.test_tools_frame, text="Reset vehicle", command=self._reset_vehicle).pack(
            fill="x", pady=3
        )
        ttk.Label(
            self.test_tools_frame,
            textvariable=self.vehicle_position_display,
            anchor="w",
        ).pack(fill="x", pady=(4, 8))
        ttk.Label(
            self.test_tools_frame,
            text="Scoreboard",
            font=("TkDefaultFont", 10, "bold"),
        ).pack(anchor="w", pady=(0, 3))
        self.score_tree = ttk.Treeview(
            self.test_tools_frame,
            columns=("vehicle", "result"),
            show="headings",
            height=4,
        )
        self.score_tree.heading("vehicle", text="Vehicle")
        self.score_tree.heading("result", text="Result")
        self.score_tree.column("vehicle", width=150, stretch=True)
        self.score_tree.column("result", width=80, stretch=False, anchor="center")
        self.score_tree.pack(fill="x")

        self.details_button = ttk.Button(
            controls, text="Show details", command=self._toggle_details
        )
        self.details_button.pack(fill="x", pady=(12, 3))

        canvas_area = ttk.Frame(self.root, padding=(0, 12, 12, 12))
        self.canvas_area = canvas_area
        canvas_area.grid(row=0, column=1, sticky="nsew")
        canvas_area.columnconfigure(0, weight=1)
        canvas_area.rowconfigure(0, weight=1)

        self.figure = Figure(figsize=(8, 5), dpi=100, facecolor="#fbfcfe")
        self.axes = self.figure.add_subplot(111)
        self.figure_canvas = FigureCanvasTkAgg(self.figure, master=canvas_area)
        self.figure_widget = self.figure_canvas.get_tk_widget()
        self.figure_widget.configure(background="#fbfcfe", cursor="crosshair")
        self.figure_widget.grid(row=0, column=0, sticky="nsew")
        self.figure_canvas.mpl_connect("button_press_event", self._on_plot_click)
        self.figure_widget.bind("<Configure>", lambda _event: self._draw())

        self.details_frame = ttk.Frame(canvas_area, padding=(0, 8, 0, 0))
        self.details_frame.columnconfigure(0, weight=1)
        self.details_frame.rowconfigure(1, weight=1)
        self.details_status = ttk.Label(
            self.details_frame, textvariable=self.details_message, anchor="w"
        )
        self.details_status.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        self.tables = ttk.Panedwindow(self.details_frame, orient="horizontal")
        self.tables.grid(row=1, column=0, sticky="nsew")
        self.joint_tree = self._make_tree(
            self.tables,
            "Joint details",
            (
                ("joint", "Joint", 55),
                ("x", "X (ft)", 65),
                ("y", "Y (ft)", 65),
                ("load", "Applied Y (lb)", 105),
                ("rx", "Reaction X (lb)", 110),
                ("ry", "Reaction Y (lb)", 110),
            ),
        )
        self.member_tree = self._make_tree(
            self.tables,
            "Member details",
            (
                ("member", "Member", 65),
                ("ends", "Joints", 85),
                ("length", "Length (ft)", 90),
                ("force", "Force (lb)", 100),
                ("type", "Type", 90),
                ("capacity", "Capacity (lb)", 105),
                ("utilization", "Utilization", 90),
            ),
        )

        status_bar = ttk.Label(
            self.root,
            textvariable=self.status,
            anchor="w",
            padding=(12, 7),
            relief="sunken",
        )
        self.status_bar = status_bar
        status_bar.grid(row=1, column=0, columnspan=2, sticky="ew")

    def _make_tree(
        self,
        notebook: ttk.Panedwindow,
        title: str,
        columns: tuple[tuple[str, str, int], ...],
    ) -> ttk.Treeview:
        panel = ttk.Frame(notebook, padding=4)
        panel.columnconfigure(0, weight=1)
        panel.rowconfigure(1, weight=1)
        ttk.Label(panel, text=title, font=("TkDefaultFont", 9, "bold")).grid(
            row=0, column=0, sticky="w", pady=(0, 3)
        )
        column_ids = [item[0] for item in columns]
        tree = ttk.Treeview(panel, columns=column_ids, show="headings", height=5)
        for key, heading, width in columns:
            tree.heading(key, text=heading)
            tree.column(key, width=width, minwidth=48, stretch=False, anchor="center")
        y_scroll = ttk.Scrollbar(panel, orient="vertical", command=tree.yview)
        x_scroll = ttk.Scrollbar(panel, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)
        tree.grid(row=1, column=0, sticky="nsew")
        y_scroll.grid(row=1, column=1, sticky="ns")
        x_scroll.grid(row=2, column=0, sticky="ew")
        notebook.add(panel, weight=1)
        return tree

    def _on_root_configure(self, event: tk.Event) -> None:
        if event.widget is self.root:
            self._set_responsive_layout(event.width)

    def _set_responsive_layout(self, width: int) -> None:
        stacked = width < 1000
        if stacked == self._stacked_layout:
            return
        self._stacked_layout = stacked
        if stacked:
            self.root.rowconfigure(0, weight=0)
            self.root.rowconfigure(1, weight=1)
            self.root.rowconfigure(2, weight=0)
            self.root.columnconfigure(0, weight=1)
            self.root.columnconfigure(1, weight=1)
            self.controls_frame.grid_configure(
                row=0, column=0, columnspan=2, sticky="ew"
            )
            self.canvas_area.grid_configure(
                row=1, column=0, columnspan=2, sticky="nsew"
            )
            self.status_bar.grid_configure(row=2, column=0, columnspan=2, sticky="ew")
        else:
            self.root.rowconfigure(0, weight=1)
            self.root.rowconfigure(1, weight=0)
            self.root.rowconfigure(2, weight=0)
            self.root.columnconfigure(0, weight=0)
            self.root.columnconfigure(1, weight=1)
            self.controls_frame.grid_configure(
                row=0, column=0, columnspan=1, sticky="ns"
            )
            self.canvas_area.grid_configure(
                row=0, column=1, columnspan=1, sticky="nsew"
            )
            self.status_bar.grid_configure(row=1, column=0, columnspan=2, sticky="ew")

    def _on_delete_key(self, _event: tk.Event | None = None) -> str:
        if self.mode.get() == "Build":
            self._delete_selected()
        return "break"

    def _clear_selection(self, _event: tk.Event | None = None) -> str:
        self.selection = None
        self.selected_joint = None
        self._draw()
        self.status.set("Selection cleared.")
        return "break"

    def _toggle_details(self) -> None:
        self.details_visible = not self.details_visible
        if self.details_visible:
            self.details_frame.grid(row=1, column=0, sticky="nsew")
            self.details_button.configure(text="Hide details")
            self._refresh_details()
        else:
            self.details_frame.grid_remove()
            self.details_button.configure(text="Show details")
        self._draw()

    def _member_color(self, member_id: int) -> str:
        if member_id == self.failed_member_id:
            return "#111111"
        if not self.solve_result.stable:
            return "#8c98a4"
        utilization = self.solve_result.member_results[member_id].utilization
        if utilization < 0.60:
            return "#2e8b57"
        if utilization < 0.85:
            return "#e3ad28"
        if utilization <= 1.0:
            return "#d64b45"
        return "#111111"

    def _draw(self) -> None:
        self.axes.clear()
        self.axes.set_facecolor("#fbfcfe")
        right_edge = SPAN_FT + 2.5
        if self.mode.get() == "Test":
            vehicle = VEHICLES[self.vehicle_name.get()]
            right_edge = SPAN_FT + max(axle.offset_ft for axle in vehicle.axles) + 4.0
        self.axes.set_xlim(-2.5, right_edge)
        self.axes.set_ylim(-2.5, 31.5)
        self.axes.set_aspect("equal", adjustable="box")
        self.axes.set_xlabel("Span (ft)")
        self.axes.set_ylabel("Height (ft)")
        self.axes.xaxis.set_major_locator(MultipleLocator(10))
        self.axes.xaxis.set_minor_locator(MultipleLocator(1))
        self.axes.yaxis.set_major_locator(MultipleLocator(5))
        self.axes.yaxis.set_minor_locator(MultipleLocator(1))
        self.axes.grid(which="major", color="#cbd5df", linewidth=0.8)
        self.axes.grid(which="minor", color="#e9eef3", linewidth=0.45)
        self.axes.set_axisbelow(True)

        # The roadway and pin/roller support symbols form the fixed site.
        self.axes.plot([0, SPAN_FT], [0, 0], color="#566573", linewidth=2.0, zorder=2)
        self.axes.scatter([0], [-0.9], marker="v", s=75, color="#dce5ee", edgecolor="#34495e", zorder=4)
        self.axes.scatter([SPAN_FT], [-0.9], marker="v", s=75, color="#dce5ee", edgecolor="#34495e", zorder=4)
        self.axes.scatter([SPAN_FT - 0.35, SPAN_FT + 0.35], [-1.45, -1.45], marker="o", s=18, color="white", edgecolor="#34495e", zorder=4)
        self.axes.text(0, -2.05, "Pin", ha="center", va="top", fontsize=8, color="#34495e")
        self.axes.text(SPAN_FT, -2.05, "Roller", ha="center", va="top", fontsize=8, color="#34495e")

        for member in self.model.members.values():
            a = self.model.joints[member.joint_a]
            b = self.model.joints[member.joint_b]
            selected = self.selection == ("member", member.id)
            color = "#e07a2d" if selected else self._member_color(member.id)
            width = 3.2 if selected else 2.6
            self.axes.plot([a.x_ft, b.x_ft], [a.y_ft, b.y_ft], color=color, linewidth=width, zorder=3)
            self.axes.text(
                (a.x_ft + b.x_ft) / 2,
                (a.y_ft + b.y_ft) / 2,
                f"M{member.id}",
                fontsize=6.5,
                color="#263746",
                ha="center",
                va="center",
                bbox={"facecolor": "#fbfcfe", "edgecolor": "none", "alpha": 0.72, "pad": 0.7},
                zorder=5,
            )

        for joint in self.model.joints.values():
            selected = self.selection == ("joint", joint.id) or self.selected_joint == joint.id
            face = "#e07a2d" if selected else ("#244a68" if joint.fixed else "white")
            edge = "#e07a2d" if selected else "#244a68"
            self.axes.scatter(
                [joint.x_ft], [joint.y_ft], s=54 if joint.fixed else 43,
                facecolor=face, edgecolor=edge, linewidth=1.5, zorder=6,
            )

        if self.mode.get() == "Test":
            self._draw_vehicle()

        legend_items = [
            Line2D([0], [0], color="#2e8b57", lw=3, label="< 0.60"),
            Line2D([0], [0], color="#e3ad28", lw=3, label="0.60–0.85"),
            Line2D([0], [0], color="#d64b45", lw=3, label="0.85–1.00"),
            Line2D([0], [0], color="#111111", lw=3, label="> 1.00"),
        ]
        self.axes.legend(
            handles=legend_items, title="Member utilization", loc="upper right",
            frameon=True, framealpha=0.93, fontsize=8, title_fontsize=8,
        )
        if not self.solve_result.stable:
            self.axes.text(
                0.5, 0.98, "Unstable truss", transform=self.axes.transAxes,
                ha="center", va="top", color="#9d3535", weight="bold",
                bbox={"facecolor": "white", "edgecolor": "#d8a0a0", "alpha": 0.92},
            )
        self.figure.tight_layout(pad=1.5)
        self.figure_canvas.draw()

        # Keep the existing grid-snap hit testing in display-pixel coordinates.
        canvas_height = max(self.figure_widget.winfo_height(), 1)
        x_left, y_bottom = self.axes.transData.transform((0.0, 0.0))
        x_one, _ = self.axes.transData.transform((1.0, 0.0))
        self.geometry = (x_left, canvas_height - y_bottom, x_one - x_left)

    def _draw_vehicle(self) -> None:
        vehicle = VEHICLES[self.vehicle_name.get()]
        front_x = self.model.vehicle_state.front_axle_x_ft
        axle_positions = [front_x + axle.offset_ft for axle in vehicle.axles]
        body_left = min(axle_positions) - 1.5
        body_right = max(axle_positions) + 1.5
        colors = {
            "Car": "#477ba8",
            "Loaded dump truck": "#b6813e",
            "Semi (AASHTO HS20 design truck)": "#516a85",
            "Fire engine": "#c9483c",
        }
        body_color = colors.get(vehicle.name, "#477ba8")
        self.axes.add_patch(
            Rectangle(
                (body_left, 1.25), body_right - body_left, 1.35,
                facecolor=body_color, edgecolor="#263746", linewidth=1.0, zorder=8,
            )
        )
        cab_width = min(3.0, max(1.8, (body_right - body_left) * 0.24))
        self.axes.add_patch(
            Rectangle(
                (body_right - cab_width, 2.6), cab_width, 1.05,
                facecolor="#d9e6ef", edgecolor="#263746", linewidth=1.0, zorder=8,
            )
        )
        self.axes.text(
            (body_left + body_right) / 2, 1.95, vehicle.name.split(" ")[0],
            ha="center", va="center", fontsize=7, color="white", weight="bold", zorder=9,
        )
        for axle_x in axle_positions:
            self.axes.add_patch(
                Circle((axle_x, 0.65), 0.58, facecolor="#20262d", edgecolor="white", linewidth=0.8, zorder=9)
            )
            self.axes.add_patch(
                Circle((axle_x, 0.65), 0.22, facecolor="#c8d1da", edgecolor="#20262d", linewidth=0.6, zorder=10)
            )

    def _refresh_details(self) -> None:
        for tree in (self.joint_tree, self.member_tree):
            tree.delete(*tree.get_children())
        if not self.solve_result.stable:
            self.details_message.set(self.solve_result.reason)
        else:
            self.details_message.set(
                f"{self.solve_result.reason}  ·  Condition number: {self.solve_result.condition_number:.3g}"
            )

        for joint_id, joint in self.model.joints.items():
            applied = self.solve_result.applied_loads_lb.get(joint_id, (0.0, 0.0))[1]
            reaction = self.solve_result.reactions_lb.get(joint_id)
            if reaction is None:
                rx = ry = "—"
            else:
                rx, ry = (f"{value:,.1f}" for value in reaction)
            if not self.solve_result.stable:
                rx = ry = "Unstable"
            self.joint_tree.insert(
                "", "end",
                values=(joint_id, f"{joint.x_ft:g}", f"{joint.y_ft:g}", f"{applied:,.1f}", rx, ry),
            )

        for member_id, member in self.model.members.items():
            result = self.solve_result.member_results.get(member_id)
            endpoints = f"{member.joint_a}–{member.joint_b}"
            if result is None:
                values = (member_id, endpoints, f"{self.model.member_length_ft(member):.2f}", "Unstable", "—", "—", "—")
            else:
                values = (
                    member_id,
                    endpoints,
                    f"{result.length_ft:.2f}",
                    f"{result.force_lb:,.1f}",
                    result.force_type,
                    f"{result.capacity_lb:,.0f}",
                    f"{result.utilization:.3f}",
                )
            self.member_tree.insert("", "end", values=values)

    def _refresh_scoreboard(self) -> None:
        for item in self.score_tree.get_children():
            self.score_tree.delete(item)
        for name, status in self.vehicle_statuses.items():
            self.score_tree.insert(
                "", "end", iid=f"vehicle:{name}", values=(name, status)
            )

    def _on_vehicle_selected(self, _event: tk.Event | None = None) -> None:
        self._pause_vehicle()
        self.model.vehicle_state.vehicle_name = self.vehicle_name.get()
        self.model.vehicle_state.front_axle_x_ft = 0.0
        self.vehicle_position_display.set("Front axle: 0.0 ft")
        self.current_joint_loads = {}
        self.failed_member_id = None
        self.status.set(f"{self.vehicle_name.get()} selected. Press Drive to begin.")
        self._update_summary()
        self._draw()

    def _apply_vehicle_position(self) -> None:
        state = self.model.vehicle_state
        vehicle = VEHICLES[state.vehicle_name]
        try:
            self.current_joint_loads = distribute_vehicle_loads(
                self.model, vehicle, state.front_axle_x_ft
            )
        except Exception as error:
            self.current_joint_loads = {}
            self.solve_result = SolveResult(
                False, f"Vehicle load error: {error}", {}, {}, {}
            )
            self.stability_display.set("Stability: Unstable truss")
            self.status.set(self.solve_result.reason)
            if self.details_visible:
                self._refresh_details()
            self._draw()
            return
        self.vehicle_position_display.set(
            f"Front axle: {state.front_axle_x_ft:.1f} ft"
        )
        self._update_summary()
        self._draw()

    def _over_capacity_member(self) -> int | None:
        if not self.solve_result.stable:
            return None
        failed = [
            member_id
            for member_id, result in self.solve_result.member_results.items()
            if result.utilization > 1.0
        ]
        return max(
            failed,
            key=lambda member_id: self.solve_result.member_results[member_id].utilization,
            default=None,
        )

    def _toggle_drive(self) -> None:
        state = self.model.vehicle_state
        if state.driving:
            self._pause_vehicle()
            self.status.set("Vehicle paused.")
            return
        if self.vehicle_statuses[state.vehicle_name] in ("Carried", "Failed"):
            self.status.set("Reset this vehicle before starting another run.")
            return

        self.failed_member_id = None
        self._apply_vehicle_position()
        if not self.solve_result.stable:
            self.status.set("Unstable truss. Add members before testing a vehicle.")
            return
        failed_member = self._over_capacity_member()
        if failed_member is not None:
            self._fail_vehicle(failed_member, "A member exceeded its capacity.")
            return

        state.driving = True
        self.drive_button.configure(text="Pause")
        self.status.set(f"Driving {state.vehicle_name} across the bridge.")
        self._schedule_animation()

    def _schedule_animation(self) -> None:
        if self.animation_after_id is None and self.model.vehicle_state.driving:
            self.animation_after_id = self.root.after(
                ANIMATION_DELAY_MS, self._animation_step
            )

    def _animation_step(self) -> None:
        self.animation_after_id = None
        state = self.model.vehicle_state
        if not state.driving:
            return

        state.front_axle_x_ft = min(
            SPAN_FT, state.front_axle_x_ft + ANIMATION_STEP_FT
        )
        self._apply_vehicle_position()
        if not self.solve_result.stable:
            self._fail_vehicle(None, "The truss became unstable during the test.")
            return
        failed_member = self._over_capacity_member()
        if failed_member is not None:
            self._fail_vehicle(failed_member, "A member exceeded its capacity.")
            return
        if state.front_axle_x_ft >= SPAN_FT:
            self._complete_vehicle()
            return
        self._schedule_animation()

    def _pause_vehicle(self) -> None:
        self.model.vehicle_state.driving = False
        if self.animation_after_id is not None:
            try:
                self.root.after_cancel(self.animation_after_id)
            except tk.TclError:
                pass
            self.animation_after_id = None
        if hasattr(self, "drive_button"):
            self.drive_button.configure(text="Drive")

    def _fail_vehicle(self, member_id: int | None, reason: str) -> None:
        self._pause_vehicle()
        self.failed_member_id = member_id
        name = self.model.vehicle_state.vehicle_name
        self.vehicle_statuses[name] = "Failed"
        self._refresh_scoreboard()
        self._draw()
        self.status.set(
            f"{name} failed: {reason}"
            + (f" Failed member: M{member_id}." if member_id is not None else "")
        )

    def _complete_vehicle(self) -> None:
        self._pause_vehicle()
        name = self.model.vehicle_state.vehicle_name
        self.vehicle_statuses[name] = "Carried"
        self._refresh_scoreboard()
        self.status.set(f"{name} carried across the bridge.")

    def _reset_vehicle(self) -> None:
        self._pause_vehicle()
        state = self.model.vehicle_state
        state.front_axle_x_ft = 0.0
        state.vehicle_name = self.vehicle_name.get()
        self.vehicle_statuses[state.vehicle_name] = "Not tested"
        self.current_joint_loads = {}
        self.failed_member_id = None
        self.vehicle_position_display.set("Front axle: 0.0 ft")
        self._refresh_scoreboard()
        self._update_summary()
        self._draw()
        self.status.set(f"{state.vehicle_name} reset to the start.")

    def _canvas_point(self, x_pixel: float, y_pixel: float) -> tuple[float, float]:
        x_left, y_deck, scale = self.geometry
        return (x_pixel - x_left) / scale, (y_deck - y_pixel) / scale

    def _find_joint_at(self, x_pixel: float, y_pixel: float) -> int | None:
        x_left, y_deck, scale = self.geometry
        closest: tuple[float, int] | None = None
        for joint in self.model.joints.values():
            x = x_left + joint.x_ft * scale
            y = y_deck - joint.y_ft * scale
            distance = hypot(x_pixel - x, y_pixel - y)
            if distance <= 10 and (closest is None or distance < closest[0]):
                closest = (distance, joint.id)
        return closest[1] if closest else None

    def _find_member_at(self, x_pixel: float, y_pixel: float) -> int | None:
        x_left, y_deck, scale = self.geometry
        closest: tuple[float, int] | None = None
        for member in self.model.members.values():
            a = self.model.joints[member.joint_a]
            b = self.model.joints[member.joint_b]
            ax, ay = x_left + a.x_ft * scale, y_deck - a.y_ft * scale
            bx, by = x_left + b.x_ft * scale, y_deck - b.y_ft * scale
            dx, dy = bx - ax, by - ay
            length_squared = dx * dx + dy * dy
            t = 0 if length_squared == 0 else max(
                0.0, min(1.0, ((x_pixel - ax) * dx + (y_pixel - ay) * dy) / length_squared)
            )
            distance = hypot(x_pixel - (ax + t * dx), y_pixel - (ay + t * dy))
            if distance <= 7 and (closest is None or distance < closest[0]):
                closest = (distance, member.id)
        return closest[1] if closest else None

    def _on_plot_click(self, event) -> None:
        if event.inaxes is not self.axes or event.xdata is None or event.ydata is None:
            return
        canvas_height = max(self.figure_widget.winfo_height(), 1)
        self._handle_design_click(event.x, canvas_height - event.y)

    def _on_canvas_click(self, event: tk.Event) -> None:
        """Compatibility entry point for Tk mouse events."""
        self._handle_design_click(event.x, event.y)

    def _handle_design_click(self, x_pixel: float, y_pixel: float) -> None:
        if self.mode.get() != "Build":
            self.status.set("Build mode is active; Test mode will be added in a later stage.")
            return

        joint_id = self._find_joint_at(x_pixel, y_pixel)
        if joint_id is not None:
            self.selection = ("joint", joint_id)
            if self.selected_joint is None:
                self.selected_joint = joint_id
                joint = self.model.joints[joint_id]
                self.status.set(
                    f"Joint {joint_id} at ({joint.x_ft:g}, {joint.y_ft:g}) ft selected; click another joint to connect."
                )
            elif self.selected_joint == joint_id:
                self.selected_joint = None
                self.selection = None
                self.status.set("Joint selection cleared. Select a first joint or place a new one.")
            else:
                try:
                    member = self.model.add_member(self.selected_joint, joint_id)
                    self.status.set(f"Member {member.id} added. Select a joint to start another member.")
                    self.selected_joint = None
                    self.selection = ("member", member.id)
                    self._update_summary()
                except ValueError as error:
                    self.status.set(str(error))
                    self.selected_joint = None
            self._draw()
            return

        member_id = self._find_member_at(x_pixel, y_pixel)
        if member_id is not None:
            self.selection = ("member", member_id)
            self.selected_joint = None
            self.status.set(f"Member {member_id} selected. Use Delete selected to remove it.")
            self._draw()
            return

        x_ft, y_ft = self._canvas_point(x_pixel, y_pixel)
        if not (0 <= x_ft <= SPAN_FT and 0 <= y_ft <= 30):
            self.status.set("Place joints inside the bridge area: x = 0–60 ft and y = 0–30 ft.")
            self.selected_joint = None
            self.selection = None
            self._draw()
            return

        snapped_x = round(x_ft)
        snapped_y = round(y_ft)
        duplicate = next(
            (j for j in self.model.joints.values() if j.x_ft == snapped_x and j.y_ft == snapped_y),
            None,
        )
        if duplicate is not None:
            self.status.set("That grid point already has a joint.")
            return

        joint = self.model.add_joint(snapped_x, snapped_y)
        self.selection = ("joint", joint.id)
        self.selected_joint = None
        self.status.set(
            f"Joint {joint.id} placed at ({snapped_x}, {snapped_y}) ft. Click two joints to connect them."
        )
        self._update_summary()
        self._draw()

    def _delete_selected(self) -> None:
        if self.selection is None:
            self.status.set("Select a member or joint on the canvas first.")
            return
        kind, item_id = self.selection
        try:
            if kind == "member":
                self.model.remove_member(item_id)
                self.status.set(f"Member {item_id} deleted.")
            else:
                self.model.remove_joint(item_id)
                self.status.set(f"Joint {item_id} deleted.")
            self.selection = None
            self.selected_joint = None
        except ValueError as error:
            self.status.set(str(error))
        self._update_summary()
        self._draw()

    def _clear_design(self) -> None:
        self.model.clear_design()
        self.selection = None
        self.selected_joint = None
        self.failed_member_id = None
        self.current_joint_loads = {}
        self.model.vehicle_state.front_axle_x_ft = 0.0
        self.status.set("Design cleared. Required deck joints and supports remain in place.")
        self._update_summary()
        self._draw()

    def _update_summary(self) -> None:
        self.count_display.set(
            f"Joints: {self.model.joint_count}    Members: {self.model.member_count}"
        )
        self.cost_display.set(f"Cost: ${self.model.cost_usd:,.0f}")
        try:
            self.solve_result = solve_bridge(self.model, self.current_joint_loads)
        except Exception as error:
            applied = {
                joint_id: (0.0, float(self.current_joint_loads.get(joint_id, 0.0)))
                for joint_id in self.model.joints
            }
            self.solve_result = SolveResult(
                False,
                f"Solver error: {type(error).__name__}: {error}",
                {},
                {},
                applied,
            )
        self.stability_display.set(
            "Stability: Stable" if self.solve_result.stable else "Stability: Unstable truss"
        )
        if self.solve_result.reason.startswith(("Solver error:", "Vehicle load error:")):
            self.status.set(self.solve_result.reason)
        if self.details_visible:
            self._refresh_details()

    def _on_mode_changed(self, *_args: object) -> None:
        if self.mode.get() == "Build":
            self._pause_vehicle()
            self.test_tools_frame.pack_forget()
            if not self.build_tools_frame.winfo_manager():
                self.build_tools_frame.pack(fill="x", pady=(4, 0))
            self.current_joint_loads = {}
            self.failed_member_id = None
            self._update_summary()
            self.status.set("Click an empty grid point to place a joint.")
        else:
            self.build_tools_frame.pack_forget()
            if not self.test_tools_frame.winfo_manager():
                self.test_tools_frame.pack(fill="x", pady=(4, 0))
            self.selected_joint = None
            self.model.vehicle_state.vehicle_name = self.vehicle_name.get()
            self._apply_vehicle_position()
            if self.solve_result.stable:
                self.status.set(f"{self.vehicle_name.get()} selected. Press Drive to begin.")
            else:
                self.status.set("Build a stable truss before testing a vehicle.")
        self._draw()


def main() -> None:
    root = tk.Tk()
    BridgeBuilderApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
