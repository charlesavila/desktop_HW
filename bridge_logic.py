"""Bridge model and fixed engineering constants for Bridge Builder."""

from dataclasses import dataclass, field
from bisect import bisect_right
from math import hypot
from typing import Literal, Mapping

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


@dataclass
class Joint:
    """A truss joint in feet; the supplied deck joints are fixed in place."""

    id: int
    x_ft: float
    y_ft: float
    fixed: bool = False


@dataclass(frozen=True)
class Support:
    """A fixed bridge support attached to a joint."""

    joint_id: int
    kind: Literal["pin", "roller"]


@dataclass
class Member:
    """A straight axial member connecting two joint IDs."""

    id: int
    joint_a: int
    joint_b: int


@dataclass
class VehicleState:
    """Vehicle state reserved for the Test mode implementation."""

    vehicle_name: str = "Car"
    front_axle_x_ft: float = 0.0
    driving: bool = False


@dataclass(frozen=True)
class MemberResult:
    """Solved axial state and capacity data for one member."""

    member_id: int
    force_lb: float
    length_ft: float
    force_type: Literal["tension", "compression", "zero"]
    capacity_lb: float
    utilization: float


@dataclass(frozen=True)
class SolveResult:
    """Outcome of a truss solve, including a user-readable failure reason."""

    stable: bool
    reason: str
    reactions_lb: dict[int, tuple[float, float]]
    member_results: dict[int, MemberResult]
    applied_loads_lb: dict[int, tuple[float, float]]
    condition_number: float | None = None


@dataclass
class BridgeModel:
    """Editable truss design with mandatory deck joints and supports."""

    joints: dict[int, Joint] = field(default_factory=dict)
    members: dict[int, Member] = field(default_factory=dict)
    supports: tuple[Support, Support] = field(
        default_factory=lambda: (Support(0, "pin"), Support(6, "roller"))
    )
    vehicle_state: VehicleState = field(default_factory=VehicleState)
    _next_joint_id: int = field(default=0, init=False, repr=False)
    _next_member_id: int = field(default=0, init=False, repr=False)

    def __post_init__(self) -> None:
        if not self.joints:
            for x_ft in DECK_JOINTS_FT:
                joint_id = self._next_joint_id
                self.joints[joint_id] = Joint(joint_id, float(x_ft), 0.0, fixed=True)
                self._next_joint_id += 1

    @property
    def joint_count(self) -> int:
        return len(self.joints)

    @property
    def member_count(self) -> int:
        return len(self.members)

    @property
    def cost_usd(self) -> float:
        joint_cost = sum(not joint.fixed for joint in self.joints.values()) * JOINT_COST_USD
        member_cost = sum(self.member_length_ft(member) for member in self.members.values())
        return joint_cost + member_cost * MEMBER_COST_PER_FT_USD

    def add_joint(self, x_ft: float, y_ft: float) -> Joint:
        """Add a non-fixed joint at the provided grid coordinates."""
        joint = Joint(self._next_joint_id, float(x_ft), float(y_ft))
        self.joints[joint.id] = joint
        self._next_joint_id += 1
        return joint

    def add_member(self, joint_a: int, joint_b: int) -> Member:
        """Connect two distinct existing joints, rejecting duplicate members."""
        if joint_a == joint_b:
            raise ValueError("Choose two different joints for a member.")
        if joint_a not in self.joints or joint_b not in self.joints:
            raise ValueError("Both member endpoints must be existing joints.")
        endpoints = frozenset((joint_a, joint_b))
        if any(frozenset((m.joint_a, m.joint_b)) == endpoints for m in self.members.values()):
            raise ValueError("Those joints are already connected.")
        member = Member(self._next_member_id, joint_a, joint_b)
        self.members[member.id] = member
        self._next_member_id += 1
        return member

    def member_length_ft(self, member: Member) -> float:
        a = self.joints[member.joint_a]
        b = self.joints[member.joint_b]
        return hypot(b.x_ft - a.x_ft, b.y_ft - a.y_ft)

    def remove_member(self, member_id: int) -> None:
        self.members.pop(member_id)

    def remove_joint(self, joint_id: int) -> None:
        joint = self.joints[joint_id]
        if joint.fixed or any(
            joint_id in (member.joint_a, member.joint_b)
            for member in self.members.values()
        ):
            raise ValueError("Required deck joints and connected joints cannot be deleted.")
        del self.joints[joint_id]

    def clear_design(self) -> None:
        """Remove all user-added joints and members while keeping the deck."""
        self.members.clear()
        self.joints = {
            joint_id: joint for joint_id, joint in self.joints.items() if joint.fixed
        }
        self._next_joint_id = max(self.joints, default=-1) + 1
        self._next_member_id = 0


VEHICLES = {
    "Car": Vehicle("Car", (Axle(0.0, 2_000.0), Axle(10.0, 2_000.0))),
    "Loaded dump truck": Vehicle(
        "Loaded dump truck",
        (Axle(0.0, 8_000.0), Axle(14.0, 16_000.0), Axle(18.0, 16_000.0)),
    ),
    "Semi (AASHTO HS20 design truck)": Vehicle(
        "Semi (AASHTO HS20 design truck)",
        (Axle(0.0, 8_000.0), Axle(14.0, 32_000.0), Axle(30.0, 32_000.0)),
    ),
    "Fire engine": Vehicle(
        "Fire engine",
        (Axle(0.0, 8_000.0), Axle(10.0, 16_000.0), Axle(14.0, 16_000.0)),
    ),
}


def distribute_vehicle_loads(
    model: BridgeModel,
    vehicle: Vehicle | str,
    front_axle_x_ft: float,
) -> dict[int, float]:
    """Return signed vertical nodal loads for a vehicle position.

    Loads are negative in the global y direction. Axles between deck joints
    are linearly interpolated. Axles beyond either support use linear
    extrapolation over the nearest deck panel, preserving their total load and
    moment about the supports.
    """
    if isinstance(vehicle, str):
        try:
            vehicle = VEHICLES[vehicle]
        except KeyError as error:
            raise ValueError(f"Unknown vehicle: {vehicle}") from error

    deck_by_x = {
        joint.x_ft: joint.id
        for joint in model.joints.values()
        if joint.fixed and abs(joint.y_ft) < 1e-9
    }
    deck_x = sorted(deck_by_x)
    if len(deck_x) < 2:
        raise ValueError("At least two fixed deck joints are required to distribute axle loads.")

    loads: dict[int, float] = {}
    for axle in vehicle.axles:
        axle_x = front_axle_x_ft + axle.offset_ft
        right_index = bisect_right(deck_x, axle_x)
        left_index = min(max(right_index - 1, 0), len(deck_x) - 2)
        right_index = left_index + 1
        x_left, x_right = deck_x[left_index], deck_x[right_index]
        right_weight = (axle_x - x_left) / (x_right - x_left)
        left_weight = 1.0 - right_weight
        left_id, right_id = deck_by_x[x_left], deck_by_x[x_right]
        loads[left_id] = loads.get(left_id, 0.0) - axle.load_lb * left_weight
        loads[right_id] = loads.get(right_id, 0.0) - axle.load_lb * right_weight
    return loads


def member_direction_cosines(model: BridgeModel, member: Member) -> tuple[float, float]:
    """Return the unit direction from member.joint_a to member.joint_b."""
    joint_a = model.joints[member.joint_a]
    joint_b = model.joints[member.joint_b]
    dx = joint_b.x_ft - joint_a.x_ft
    dy = joint_b.y_ft - joint_a.y_ft
    length = hypot(dx, dy)
    if length <= 1e-12:
        raise ValueError(f"Member {member.id} has zero length.")
    return dx / length, dy / length


def solve_bridge(
    model: BridgeModel,
    joint_loads_lb: Mapping[int, float] | None = None,
    *,
    condition_limit: float = 1e12,
) -> SolveResult:
    """Solve a determinate plane truss using method-of-joints equilibrium.

    ``joint_loads_lb`` maps joint IDs to signed vertical loads (down is
    negative). A failed count, geometry, conditioning, or linear solve returns
    an unstable result instead of exposing misleading force values.
    """
    loads = dict(joint_loads_lb or {})
    applied = {joint_id: (0.0, float(loads.get(joint_id, 0.0))) for joint_id in model.joints}

    def unstable(reason: str, condition: float | None = None) -> SolveResult:
        return SolveResult(False, reason, {}, {}, applied, condition)

    if any(joint_id not in model.joints for joint_id in loads):
        return unstable("Applied load references a missing joint.")

    pins = [support for support in model.supports if support.kind == "pin"]
    rollers = [support for support in model.supports if support.kind == "roller"]
    if len(pins) != 1 or len(rollers) != 1:
        return unstable("The truss needs one pin and one roller support.")
    if pins[0].joint_id not in model.joints or rollers[0].joint_id not in model.joints:
        return unstable("A support references a missing joint.")

    unknown_count = len(model.members) + 3
    equation_count = 2 * len(model.joints)
    if unknown_count != equation_count:
        return unstable(
            f"Unstable truss: members + 3 must equal 2 × joints "
            f"({len(model.members)} + 3 ≠ 2 × {len(model.joints)})."
        )

    joint_ids = list(model.joints)
    row_for = {joint_id: (2 * index, 2 * index + 1) for index, joint_id in enumerate(joint_ids)}
    member_ids = list(model.members)
    column_for = {member_id: index for index, member_id in enumerate(member_ids)}
    pin_x_column = len(member_ids)
    pin_y_column = pin_x_column + 1
    roller_y_column = pin_x_column + 2
    matrix = np.zeros((equation_count, unknown_count), dtype=float)
    rhs = np.zeros(equation_count, dtype=float)

    for joint_id, (fx_row, fy_row) in row_for.items():
        rhs[fx_row] = -applied[joint_id][0]
        rhs[fy_row] = -applied[joint_id][1]

    for member_id, member in model.members.items():
        joint_a = model.joints[member.joint_a]
        joint_b = model.joints[member.joint_b]
        try:
            cx, cy = member_direction_cosines(model, member)
        except ValueError as error:
            return unstable(str(error))
        column = column_for[member_id]
        ax_row, ay_row = row_for[member.joint_a]
        bx_row, by_row = row_for[member.joint_b]
        matrix[ax_row, column] = cx
        matrix[ay_row, column] = cy
        matrix[bx_row, column] = -cx
        matrix[by_row, column] = -cy

    pin_fx_row, pin_fy_row = row_for[pins[0].joint_id]
    roller_fx_row, roller_fy_row = row_for[rollers[0].joint_id]
    matrix[pin_fx_row, pin_x_column] = 1.0
    matrix[pin_fy_row, pin_y_column] = 1.0
    matrix[roller_fy_row, roller_y_column] = 1.0

    try:
        condition_number = float(np.linalg.cond(matrix))
    except np.linalg.LinAlgError:
        return unstable("Unstable truss: the equilibrium matrix could not be checked.")
    if not np.isfinite(condition_number) or condition_number > condition_limit:
        return unstable("Unstable truss: the equilibrium matrix is nearly singular.", condition_number)

    try:
        solution = np.linalg.solve(matrix, rhs)
    except np.linalg.LinAlgError:
        return unstable("Unstable truss: the equilibrium equations could not be solved.", condition_number)

    member_results: dict[int, MemberResult] = {}
    for member_id, member in model.members.items():
        force = float(solution[column_for[member_id]])
        if force > 1e-9:
            force_type: Literal["tension", "compression", "zero"] = "tension"
            capacity = TENSION_CAPACITY_LB
        elif force < -1e-9:
            force_type = "compression"
            capacity = COMPRESSION_CAPACITY_LB
        else:
            force_type = "zero"
            capacity = TENSION_CAPACITY_LB
        member_results[member_id] = MemberResult(
            member_id=member_id,
            force_lb=force,
            length_ft=model.member_length_ft(member),
            force_type=force_type,
            capacity_lb=capacity,
            utilization=abs(force) / capacity,
        )

    reactions = {
        pins[0].joint_id: (float(solution[pin_x_column]), float(solution[pin_y_column])),
        rollers[0].joint_id: (0.0, float(solution[roller_y_column])),
    }
    return SolveResult(True, "Stable", reactions, member_results, applied, condition_number)

