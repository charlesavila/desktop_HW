"""Tkinter entry point for Bridge Builder: 60 ft Truss Challenge."""

import tkinter as tk
from tkinter import ttk

from bridge_logic import DECK_JOINTS_FT, SPAN_FT


class BridgeBuilderApp:
    """Initial application shell; drawing and interaction arrive in later stages."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Bridge Builder: 60 ft Truss Challenge")
        self.root.minsize(760, 480)

        self.mode = tk.StringVar(value="Build")
        self.status = tk.StringVar(value="Click a grid point to place a joint.")

        self._build_layout()

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
        ttk.Label(controls, text=f"Deck joints: {len(DECK_JOINTS_FT)}").pack(
            anchor="w", pady=2
        )
        ttk.Label(controls, text="Cost: $0").pack(anchor="w", pady=2)
        ttk.Label(controls, text="Joints: 7    Members: 0").pack(anchor="w", pady=2)

        canvas_area = ttk.Frame(self.root, padding=(0, 12, 12, 12))
        canvas_area.grid(row=0, column=1, sticky="nsew")
        canvas_area.columnconfigure(0, weight=1)
        canvas_area.rowconfigure(0, weight=1)

        self.canvas = tk.Canvas(
            canvas_area,
            background="#fbfcfe",
            highlightthickness=1,
            highlightbackground="#b8c2cc",
        )
        self.canvas.grid(row=0, column=0, sticky="nsew")

        status_bar = ttk.Label(
            self.root,
            textvariable=self.status,
            anchor="w",
            padding=(12, 7),
            relief="sunken",
        )
        status_bar.grid(row=1, column=0, columnspan=2, sticky="ew")


def main() -> None:
    root = tk.Tk()
    BridgeBuilderApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

