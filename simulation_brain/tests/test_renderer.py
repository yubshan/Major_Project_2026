import pytest

from simulation_brain.controller import SimulationController
from simulation_brain.visual_state import VisualSessionState


def test_animation_is_visual_only_and_interpolates_pose():
    controller = SimulationController("open-room", seed=2)
    original_robot = controller.robot
    original_heading = controller.heading
    visual = VisualSessionState.from_controller(controller)
    visual.begin_transition((24, 25), 90, duration=1.0)
    visual.advance(0.5)
    pose = visual.interpolated_pose()
    assert pose.row == pytest.approx(24.5)
    assert pose.col == pytest.approx(25.0)
    assert pose.heading == pytest.approx(45.0)
    assert controller.robot == original_robot
    assert controller.heading == original_heading


def test_visual_controls_toggle_and_clamp_speed():
    controller = SimulationController("open-room", seed=2)
    visual = VisualSessionState.from_controller(controller)
    visual.toggle_view()
    assert visual.view_mode == "truth"
    visual.show_sensors = False
    visual.show_path = False
    visual.edit_obstacles = True
    assert controller.robot == controller.scenario.start
    for _ in range(10):
        visual.adjust_speed(1)
    assert visual.speed == 2.0
    for _ in range(10):
        visual.adjust_speed(-1)
    assert visual.speed == 0.25
    visual.paused = True
    visual.reset_for(controller)
    assert visual.paused is False
    assert visual.visited == {controller.robot}


@pytest.mark.parametrize(
    ("heading", "expected"),
    ((0, (1.0, 0.0)), (90, (0.0, -1.0)), (180, (-1.0, 0.0)), (270, (0.0, 1.0))),
)
def test_rover_heading_vectors(heading, expected, monkeypatch):
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    monkeypatch.setenv("SDL_AUDIODRIVER", "dummy")
    pytest.importorskip("pygame")
    from simulation_brain.renderer import SimulationRenderer

    actual = SimulationRenderer.rover_heading_vector(heading)
    assert actual == pytest.approx(expected, abs=1e-7)


def test_pygame_renderer_smoke(monkeypatch):
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    monkeypatch.setenv("SDL_AUDIODRIVER", "dummy")
    pytest.importorskip("pygame")
    from simulation_brain.renderer import SimulationRenderer

    controller = SimulationController("open-room", seed=2)
    controller.step()
    renderer = SimulationRenderer(controller, window_size=(1100, 720))
    visual = VisualSessionState.from_controller(controller)
    renderer.draw(visual)
    assert renderer.action_at(renderer.button_rects["pause"].center) == "pause"
    assert renderer.action_at(renderer.button_rects["edit"].center) == "edit"
    assert renderer.action_at(renderer.button_rects["dynamic"].center) == "dynamic"
    assert renderer.map_cell_at(renderer._cell_center(10, 12)) == (10, 12)
    assert renderer.map_cell_at((0, 0)) is None
    assert len(renderer.behavior_tree_rows()) == 6
    assert renderer.rl_policy_status().startswith("NOT TRAINED")
    renderer.close()


def test_perception_view_hides_truth_and_victim(monkeypatch):
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    monkeypatch.setenv("SDL_AUDIODRIVER", "dummy")
    pytest.importorskip("pygame")
    from simulation_brain.renderer import SimulationRenderer

    controller = SimulationController("maze", seed=7)
    visual = VisualSessionState.from_controller(controller)
    renderer = SimulationRenderer(controller, window_size=(800, 600))
    assert renderer.display_grid(visual) is controller.occupancy.data
    assert renderer.victim_visible(visual) is False
    visual.toggle_view()
    assert renderer.display_grid(visual) is controller.ground_truth
    assert renderer.victim_visible(visual) is True
    renderer.draw(visual)
    renderer.close()


def test_visual_cli_accepts_presentation_speed():
    from simulation_brain.__main__ import build_parser, resolve_runtime_defaults

    args = build_parser().parse_args([
        "--mode", "visual", "--speed", "1.0",
        "--moving-obstacles", "3", "--obstacle-interval", "6",
        "--presentation",
    ])
    assert args.speed == 1.0
    assert args.moving_obstacles == 3
    assert args.obstacle_interval == 6
    assert args.presentation is True
    assert resolve_runtime_defaults(args) == (4, 3)


def test_presentation_defaults_and_explicit_seed_override():
    from simulation_brain.__main__ import build_parser, resolve_runtime_defaults

    presentation = build_parser().parse_args(["--presentation"])
    assert presentation.scenario == "two-bedroom-house"
    assert resolve_runtime_defaults(presentation) == (4, 0)
    explicit = build_parser().parse_args(["--presentation", "--seed", "12"])
    assert resolve_runtime_defaults(explicit) == (12, 0)
    normal = build_parser().parse_args([])
    assert resolve_runtime_defaults(normal) == (7, 2)


def test_presentation_mode_starts_paused_with_intro():
    controller = SimulationController("two-bedroom-house", seed=7)
    visual = VisualSessionState.from_controller(controller, presentation_mode=True)
    assert visual.paused is True
    assert visual.show_intro is True
    visual.reset_for(controller)
    assert visual.show_intro is True


def test_behavior_tree_rows_highlight_real_active_branch(monkeypatch):
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    monkeypatch.setenv("SDL_AUDIODRIVER", "dummy")
    pytest.importorskip("pygame")
    from simulation_brain.renderer import SimulationRenderer

    controller = SimulationController("two-bedroom-house", seed=4)
    renderer = SimulationRenderer(controller, window_size=(800, 600))
    behaviors = (
        "SafetyGate", "EmergencyStop", "VictimConfirmation",
        "NavigateToTarget", "RLExplore", "Idle",
    )
    for behavior in behaviors:
        controller.blackboard.set("decision/state", {"active_behavior": behavior})
        rows = renderer.behavior_tree_rows()
        assert sum(active for _, _, active in rows) == 1
        assert rows[behaviors.index(behavior)][2] is True
    controller.blackboard.set("decision/state", {"active_behavior": "RLExplore"})
    rows = renderer.behavior_tree_rows()
    assert rows[0][1] == "CLEAR"
    assert rows[1][1] == "CLEAR"
    assert rows[4][1] == "HEURISTIC FALLBACK"
    controller._policy = object()
    assert renderer.rl_policy_status() == "TRAINED PPO LOADED"
    assert renderer.behavior_tree_rows()[4][1] == "PPO RUNNING"
    controller._policy = None
    controller.policy_load_error = "legacy observation shape"
    assert renderer.rl_policy_status().startswith("CHECKPOINT REJECTED")
    controller.policy_load_error = None
    visual = VisualSessionState.from_controller(controller, presentation_mode=True)
    robot_before = controller.robot
    grid_before = controller.occupancy.data.copy()
    visual.show_intro = False
    renderer.draw(visual)
    assert set(renderer.button_rects) == {"pause", "step", "reset", "view", "guide", "rl"}
    visual.show_rl_glimpse = True
    renderer.draw(visual)
    assert controller.robot == robot_before
    assert (controller.occupancy.data == grid_before).all()
    renderer.close()
