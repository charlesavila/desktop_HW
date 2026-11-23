"""Fixed engineering constants for Bridge Builder.

The calculation and model functions will be added in later implementation
stages. This module keeps the assignment's fixed values separate from the UI.
"""

from dataclasses import dataclass

import numpy as np


SPAN_FT = 60.0
DECK_SPACING_FT = 10.0
GRID_SPACING_FT = 1.0
DECK_JOINTS_FT = tuple(np.arange(0.0, SPAN_FT + DECK_SPACING_FT, DECK_SPACING_FT))

SUPPORT_TYPES = {
    "left": "pin",
    "right": "roller",
}

TENSION_CAPACITY_LB = 90_000.0
COMPRESSION_CAPACITY_LB = 75_000.0
JOINT_COST_USD = 500.0
MEMBER_COST_PER_FT_USD = 100.0


@dataclass(frozen=True)
class Axle:
    """A vehicle axle load and its longitudinal offset from the front axle."""

    offset_ft: float
    load_lb: float


@dataclass(frozen=True)
class Vehicle:
    """Fixed vehicle data used by the bridge challenge."""

    name: str
    axles: tuple[Axle, ...]


VEHICLES = {
    "Car": Vehicle("Car", (Axle(0.0, 2_000.0), Axle(10.0, 2_000.0))),
    "Loaded dump truck": Vehicle(
        "Loaded dump truck",
        (Axle(0.0, 8_000.0), Axle(14.0, 16_000.0), Axle(18.0, 16_000.0)),
    ),
    "Semi (AASHTO HS20 design truck)": Vehicle(
        "Semi (AASHTO HS20 design truck)",
        (Axle(0.0, 8_000.0), Axle(14.0, 32_000.0), Axle(28.0, 32_000.0)),
    ),
    "Fire engine": Vehicle(
        "Fire engine",
        (Axle(0.0, 8_000.0), Axle(10.0, 16_000.0), Axle(14.0, 16_000.0)),
    ),
}

