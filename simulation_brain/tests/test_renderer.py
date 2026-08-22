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
    assert renderer.map_cell_at(renderer._cell_center(10, 12)) == (10, 12)
    assert renderer.map_cell_at((0, 0)) is None
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
    from simulation_brain.__main__ import build_parser

    args = build_parser().parse_args(["--mode", "visual", "--speed", "1.0"])
    assert args.speed == 1.0
