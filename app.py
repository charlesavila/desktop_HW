"""Tkinter entry point for Bridge Builder: 60 ft Truss Challenge."""

from math import hypot
import tkinter as tk
from tkinter import ttk

from bridge_logic import BridgeModel, SPAN_FT, solve_bridge


class BridgeBuilderApp:
    """Bridge design window with the Stage 2 Build mode workflow."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Bridge Builder: 60 ft Truss Challenge")
        self.root.minsize(760, 480)

        self.model = BridgeModel()
        self.mode = tk.StringVar(value="Build")
        self.status = tk.StringVar(value="Click an empty grid point to place a joint.")
        self.cost_display = tk.StringVar()
        self.count_display = tk.StringVar()
        self.stability_display = tk.StringVar()
        self.selected_joint: int | None = None
        self.selection: tuple[str, int] | None = None
        self.geometry: tuple[float, float, float] = (0.0, 0.0, 1.0)

        self._build_layout()
        self.mode.trace_add("write", self._on_mode_changed)
        self._update_summary()

    def _build_layout(self) -> None:
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(0, weight=1)

        controls = ttk.Frame(self.root, padding=12)
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

        ttk.Label(controls, text="Build tools", font=("TkDefaultFont", 10, "bold")).pack(
            anchor="w", pady=(4, 4)
        )
        ttk.Button(controls, text="Delete selected", command=self._delete_selected).pack(
            fill="x", pady=3
        )
        ttk.Button(controls, text="Clear / Reset", command=self._clear_design).pack(
            fill="x", pady=3
        )
        ttk.Label(
            controls,
            text="Click empty grid to add a joint.\nClick two joints to connect them.\nSelect a member or joint, then delete.",
            justify="left",
            wraplength=190,
        ).pack(anchor="w", pady=(12, 0))

        canvas_area = ttk.Frame(self.root, padding=(0, 12, 12, 12))
        canvas_area.grid(row=0, column=1, sticky="nsew")
        canvas_area.columnconfigure(0, weight=1)
        canvas_area.rowconfigure(0, weight=1)

        self.canvas = tk.Canvas(
            canvas_area,
            background="#fbfcfe",
            highlightthickness=1,
            highlightbackground="#b8c2cc",
            width=760,
            height=500,
            cursor="crosshair",
        )
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.canvas.bind("<Button-1>", self._on_canvas_click)
        self.canvas.bind("<Configure>", lambda _event: self._draw())

        status_bar = ttk.Label(
            self.root,
            textvariable=self.status,
            anchor="w",
            padding=(12, 7),
            relief="sunken",
        )
        status_bar.grid(row=1, column=0, columnspan=2, sticky="ew")

    def _draw(self) -> None:
        width = max(self.canvas.winfo_width(), 240)
        height = max(self.canvas.winfo_height(), 200)
        scale = min((width - 70) / SPAN_FT, (height - 90) / 30.0)
        x_left = (width - SPAN_FT * scale) / 2
        y_deck = (height + 30.0 * scale) / 2
        self.geometry = (x_left, y_deck, scale)
        self.canvas.delete("all")

        def point(x_ft: float, y_ft: float) -> tuple[float, float]:
            return x_left + x_ft * scale, y_deck - y_ft * scale

        # One-foot grid, with stronger reference lines every ten feet.
        for x_ft in range(61):
            x, top = point(float(x_ft), 30.0)
            _, bottom = point(float(x_ft), 0.0)
            major = x_ft % 10 == 0
            self.canvas.create_line(
                x, top, x, bottom,
                fill="#ccd5df" if major else "#edf1f5",
                width=1 if major else 1,
                tags=("grid",),
            )
            if major:
                self.canvas.create_text(x, y_deck + 19, text=str(x_ft), fill="#65717d", font=("TkDefaultFont", 8))

        for y_ft in range(31):
            left, y = point(0.0, float(y_ft))
            right, _ = point(SPAN_FT, float(y_ft))
            major = y_ft % 5 == 0
            self.canvas.create_line(
                left, y, right, y,
                fill="#ccd5df" if major else "#edf1f5",
                width=1,
                tags=("grid",),
            )
            if major:
                self.canvas.create_text(left - 20, y, text=str(y_ft), fill="#65717d", font=("TkDefaultFont", 8))

        # Draw members below joints so the connections terminate at joint centers.
        for member in self.model.members.values():
            a = self.model.joints[member.joint_a]
            b = self.model.joints[member.joint_b]
            ax, ay = point(a.x_ft, a.y_ft)
            bx, by = point(b.x_ft, b.y_ft)
            selected = self.selection == ("member", member.id)
            self.canvas.create_line(
                ax, ay, bx, by,
                fill="#e07a2d" if selected else "#34495e",
                width=4 if selected else 3,
                tags=("member", f"member:{member.id}"),
            )

        # Deck and supports are fixed parts of the site.
        left_x, deck_y = point(0.0, 0.0)
        right_x, _ = point(SPAN_FT, 0.0)
        self.canvas.create_line(left_x, deck_y + 1, right_x, deck_y + 1, fill="#566573", width=2)
        self.canvas.create_polygon(
            left_x - 10, deck_y + 22, left_x + 10, deck_y + 22, left_x, deck_y + 3,
            fill="#dce5ee", outline="#34495e", width=2,
        )
        self.canvas.create_line(left_x - 15, deck_y + 23, left_x + 15, deck_y + 23, fill="#34495e", width=2)
        self.canvas.create_polygon(
            right_x - 10, deck_y + 20, right_x + 10, deck_y + 20, right_x, deck_y + 3,
            fill="#dce5ee", outline="#34495e", width=2,
        )
        self.canvas.create_oval(right_x - 9, deck_y + 21, right_x - 3, deck_y + 27, fill="white", outline="#34495e")
        self.canvas.create_oval(right_x + 3, deck_y + 21, right_x + 9, deck_y + 27, fill="white", outline="#34495e")
        self.canvas.create_line(right_x - 15, deck_y + 28, right_x + 15, deck_y + 28, fill="#34495e", width=2)
        self.canvas.create_text(left_x, deck_y + 39, text="Pin", fill="#34495e", font=("TkDefaultFont", 8, "bold"))
        self.canvas.create_text(right_x, deck_y + 42, text="Roller", fill="#34495e", font=("TkDefaultFont", 8, "bold"))

        for joint in self.model.joints.values():
            x, y = point(joint.x_ft, joint.y_ft)
            selected = self.selection == ("joint", joint.id) or self.selected_joint == joint.id
            radius = 6 if joint.fixed else 5
            fill = "#e07a2d" if selected else ("#244a68" if joint.fixed else "#ffffff")
            outline = "#e07a2d" if selected else "#244a68"
            self.canvas.create_oval(
                x - radius, y - radius, x + radius, y + radius,
                fill=fill, outline=outline, width=2,
                tags=("joint", f"joint:{joint.id}"),
            )

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

    def _on_canvas_click(self, event: tk.Event) -> None:
        if self.mode.get() != "Build":
            self.status.set("Build mode is active; Test mode will be added in a later stage.")
            return

        joint_id = self._find_joint_at(event.x, event.y)
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

        member_id = self._find_member_at(event.x, event.y)
        if member_id is not None:
            self.selection = ("member", member_id)
            self.selected_joint = None
            self.status.set(f"Member {member_id} selected. Use Delete selected to remove it.")
            self._draw()
            return

        x_ft, y_ft = self._canvas_point(event.x, event.y)
        if not (0 <= x_ft <= SPAN_FT and 0 <= y_ft <= 30):
            self.status.set("Place joints inside the bridge area: x = 0–60 ft and y = 0–30 ft.")
            self.selected_joint = None
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
        self.status.set("Design cleared. Required deck joints and supports remain in place.")
        self._update_summary()
        self._draw()

    def _update_summary(self) -> None:
        self.count_display.set(
            f"Joints: {self.model.joint_count}    Members: {self.model.member_count}"
        )
        self.cost_display.set(f"Cost: ${self.model.cost_usd:,.0f}")
        result = solve_bridge(self.model)
        self.stability_display.set(
            "Stability: Stable" if result.stable else "Stability: Unstable truss"
        )

    def _on_mode_changed(self, *_args: object) -> None:
        if self.mode.get() == "Build":
            self.status.set("Click an empty grid point to place a joint.")
        else:
            self.selected_joint = None
            self.status.set("Test mode will be added in a later stage.")
            self._draw()


def main() -> None:
    root = tk.Tk()
    BridgeBuilderApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
