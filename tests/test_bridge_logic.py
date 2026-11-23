"""Focused calculation checks for the Stage 4 truss solver."""

import unittest

from bridge_logic import (
    Axle,
    BridgeModel,
    DECK_JOINTS_FT,
    Vehicle,
    distribute_vehicle_loads,
    member_direction_cosines,
    solve_bridge,
)


def make_six_panel_pratt() -> BridgeModel:
    """Build a symmetric, six-panel Pratt truss with a 10 ft truss height."""
    model = BridgeModel()
    bottom = {joint.x_ft: joint.id for joint in model.joints.values()}
    top = {
        x_ft: model.add_joint(x_ft, 10.0).id
        for x_ft in DECK_JOINTS_FT
    }

    for x_left, x_right in zip(DECK_JOINTS_FT, DECK_JOINTS_FT[1:]):
        model.add_member(bottom[x_left], bottom[x_right])
        model.add_member(top[x_left], top[x_right])
    for x_ft in DECK_JOINTS_FT:
        model.add_member(bottom[x_ft], top[x_ft])

    # Pratt diagonals slope down toward the center of the span.
    for panel in range(6):
        x_left = DECK_JOINTS_FT[panel]
        x_right = DECK_JOINTS_FT[panel + 1]
        if panel < 3:
            model.add_member(top[x_left], bottom[x_right])
        else:
            model.add_member(top[x_right], bottom[x_left])
    return model


def member_coordinate_key(model: BridgeModel, member_id: int):
    member = model.members[member_id]
    endpoints = (
        (model.joints[member.joint_a].x_ft, model.joints[member.joint_a].y_ft),
        (model.joints[member.joint_b].x_ft, model.joints[member.joint_b].y_ft),
    )
    return tuple(sorted(endpoints))


class BridgeLogicTests(unittest.TestCase):
    def test_direction_cosines_length_and_cost(self):
        model = BridgeModel()
        elevated = model.add_joint(3.0, 4.0)
        member = model.add_member(0, elevated.id)

        self.assertEqual(member_direction_cosines(model, member), (0.6, 0.8))
        self.assertEqual(model.member_length_ft(member), 5.0)
        self.assertEqual(model.cost_usd, 1_000.0)

    def test_vehicle_load_distribution_preserves_force_and_moment(self):
        model = make_six_panel_pratt()
        loads = distribute_vehicle_loads(
            model, "Semi (AASHTO HS20 design truck)", 44.0
        )
        total_load = -sum(loads.values())
        moment_about_left = -sum(
            model.joints[joint_id].x_ft * load for joint_id, load in loads.items()
        )

        self.assertAlmostEqual(total_load, 72_000.0, delta=1e-8)
        self.assertAlmostEqual(moment_about_left, 4_576_000.0, delta=1e-6)

    def test_semi_at_front_axle_44_ft_matches_hand_reactions(self):
        model = make_six_panel_pratt()
        loads = distribute_vehicle_loads(
            model, "Semi (AASHTO HS20 design truck)", 44.0
        )
        result = solve_bridge(model, loads)

        self.assertTrue(result.stable, result.reason)
        self.assertAlmostEqual(result.reactions_lb[0][1], -4_266.6667, delta=1.0)
        self.assertAlmostEqual(result.reactions_lb[6][1], 76_266.6667, delta=1.0)
        self.assertAlmostEqual(
            result.reactions_lb[0][1] + result.reactions_lb[6][1],
            72_000.0,
            delta=1e-6,
        )

    def test_car_load_and_reaction_sum(self):
        model = make_six_panel_pratt()
        loads = distribute_vehicle_loads(model, "Car", 0.0)
        result = solve_bridge(model, loads)

        self.assertAlmostEqual(-sum(loads.values()), 4_000.0, delta=1e-8)
        self.assertTrue(result.stable, result.reason)
        vertical_reactions = sum(reaction[1] for reaction in result.reactions_lb.values())
        self.assertAlmostEqual(vertical_reactions, 4_000.0, delta=1e-6)

    def test_method_of_joints_equilibrium_at_each_joint(self):
        model = make_six_panel_pratt()
        loads = distribute_vehicle_loads(
            model, "Semi (AASHTO HS20 design truck)", 44.0
        )
        result = solve_bridge(model, loads)
        self.assertTrue(result.stable, result.reason)

        residuals = {
            joint_id: [0.0, result.applied_loads_lb[joint_id][1]]
            for joint_id in model.joints
        }
        for member_id, member_result in result.member_results.items():
            member = model.members[member_id]
            cx, cy = member_direction_cosines(model, member)
            residuals[member.joint_a][0] += member_result.force_lb * cx
            residuals[member.joint_a][1] += member_result.force_lb * cy
            residuals[member.joint_b][0] -= member_result.force_lb * cx
            residuals[member.joint_b][1] -= member_result.force_lb * cy
        for joint_id, (reaction_x, reaction_y) in result.reactions_lb.items():
            residuals[joint_id][0] += reaction_x
            residuals[joint_id][1] += reaction_y

        for joint_id, (sum_x, sum_y) in residuals.items():
            with self.subTest(joint_id=joint_id):
                self.assertAlmostEqual(sum_x, 0.0, delta=1e-6)
                self.assertAlmostEqual(sum_y, 0.0, delta=1e-6)

    def test_centered_load_is_symmetric_on_mirrored_truss(self):
        model = make_six_panel_pratt()
        centered_load = Vehicle("Centered test axle", (Axle(0.0, 10_000.0),))
        loads = distribute_vehicle_loads(model, centered_load, 30.0)
        result = solve_bridge(model, loads)

        self.assertTrue(result.stable, result.reason)
        self.assertAlmostEqual(result.reactions_lb[0][1], 5_000.0, delta=1e-6)
        self.assertAlmostEqual(result.reactions_lb[6][1], 5_000.0, delta=1e-6)

        member_by_key = {
            member_coordinate_key(model, member_id): data
            for member_id, data in result.member_results.items()
        }
        for (a, b), data in member_by_key.items():
            # The span runs from 0 to 60, so reflect around x = 30 ft.
            mirrored_key = tuple(sorted(((60.0 - a[0], a[1]), (60.0 - b[0], b[1]))))
            self.assertIn(mirrored_key, member_by_key)
            self.assertAlmostEqual(
                data.utilization, member_by_key[mirrored_key].utilization, delta=1e-8
            )

    def test_pratt_fixture_is_determinate(self):
        model = make_six_panel_pratt()
        self.assertEqual(model.joint_count, 14)
        self.assertEqual(model.member_count, 25)
        self.assertTrue(solve_bridge(model).stable)


if __name__ == "__main__":
    unittest.main()
