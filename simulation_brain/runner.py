"""Visual and headless simulation runners."""

from __future__ import annotations

import json

from simulation_brain.controller import SimulationController


def run_headless(
    scenario: str, seed: int, episodes: int, max_steps: int | None = None,
    model_path: str | None = None,
    moving_obstacle_count: int = 0,
    moving_obstacle_interval: int = 10,
) -> list[dict]:
    results = []
    for episode in range(episodes):
        controller = SimulationController(
            scenario=scenario, seed=seed + episode, model_path=model_path,
            moving_obstacle_count=moving_obstacle_count,
            moving_obstacle_interval=moving_obstacle_interval,
        )
        metrics = controller.run(max_steps=max_steps)
        metrics.update({"episode": episode, "seed": seed + episode, "scenario": scenario})
        results.append(metrics)
        print(json.dumps(metrics, sort_keys=True))
    return results


def run_visual(
    scenario: str,
    seed: int,
    model_path: str | None = None,
    speed: float = 0.5,
    moving_obstacle_count: int = 2,
    moving_obstacle_interval: int = 10,
    presentation: bool = False,
) -> dict:
    from simulation_brain.renderer import SimulationRenderer
    from simulation_brain.visual_state import VisualSessionState

    controller = SimulationController(
        scenario=scenario, seed=seed, model_path=model_path,
        moving_obstacle_count=moving_obstacle_count,
        moving_obstacle_interval=moving_obstacle_interval,
    )
    renderer = SimulationRenderer(controller)
    visual = VisualSessionState.from_controller(
        controller, speed=speed, presentation_mode=presentation,
    )
    running = True
    accumulator = 0.0

    def reset() -> None:
        nonlocal controller, accumulator
        controller = SimulationController(
            scenario=scenario, seed=seed, model_path=model_path,
            moving_obstacle_count=moving_obstacle_count,
            moving_obstacle_interval=moving_obstacle_interval,
        )
        renderer.controller = controller
        visual.reset_for(controller)
        accumulator = 0.0

    def apply_action(action: str) -> bool:
        nonlocal running
        if action == "quit":
            running = False
        elif action == "start":
            visual.show_intro = False
            visual.show_guide = False
            visual.show_rl_glimpse = False
            visual.paused = False
        elif action == "pause":
            if visual.show_intro:
                visual.show_intro = False
                visual.paused = False
            else:
                visual.paused = not visual.paused
        elif action == "reset":
            reset()
        elif action == "view":
            visual.toggle_view()
        elif action == "sensors":
            visual.show_sensors = not visual.show_sensors
        elif action == "path":
            visual.show_path = not visual.show_path
        elif action == "edit":
            visual.edit_obstacles = not visual.edit_obstacles
            visual.notification = (
                "Obstacle edit mode: click a map cell to add or remove a wall."
                if visual.edit_obstacles else "Obstacle edit mode disabled."
            )
            visual.notification_seconds = 3.0
        elif action == "dynamic":
            if not controller.moving_obstacles:
                created = controller.spawn_moving_obstacles(1)
                controller.moving_obstacles_enabled = bool(created)
                visual.notification = (
                    "Autonomous hazard added; its motion will trigger safe replanning."
                    if created else "No safe location is available for a moving hazard."
                )
            else:
                controller.moving_obstacles_enabled = not controller.moving_obstacles_enabled
                state = "enabled" if controller.moving_obstacles_enabled else "paused"
                visual.notification = f"Autonomous moving obstacles {state}."
            visual.notification_seconds = 3.0
        elif action == "guide":
            visual.show_guide = not visual.show_guide
            visual.show_intro = False
            visual.show_rl_glimpse = False
            visual.paused = visual.show_guide or visual.paused
        elif action == "rl":
            visual.show_rl_glimpse = not visual.show_rl_glimpse
            visual.show_intro = False
            visual.show_guide = False
            visual.paused = visual.show_rl_glimpse or visual.paused
        elif action == "slower":
            visual.adjust_speed(-1)
        elif action == "faster":
            visual.adjust_speed(1)
        return action == "step"

    try:
        while running:
            elapsed = renderer.clock.tick(controller.config.fps) / 1000.0
            visual.advance(elapsed)
            if not visual.paused and not controller.terminated:
                accumulator += elapsed
            single_step = False
            for event in renderer.pg.event.get():
                if event.type == renderer.pg.QUIT:
                    running = False
                elif event.type == renderer.pg.KEYDOWN:
                    key_actions = {
                        renderer.pg.K_ESCAPE: "quit",
                        renderer.pg.K_RETURN: "start",
                        renderer.pg.K_SPACE: "pause",
                        renderer.pg.K_h: "guide",
                        renderer.pg.K_l: "rl",
                        renderer.pg.K_n: "step",
                        renderer.pg.K_r: "reset",
                        renderer.pg.K_g: "view",
                        renderer.pg.K_s: "sensors",
                        renderer.pg.K_p: "path",
                        renderer.pg.K_o: "edit",
                        renderer.pg.K_d: "dynamic",
                        renderer.pg.K_MINUS: "slower",
                        renderer.pg.K_KP_MINUS: "slower",
                        renderer.pg.K_EQUALS: "faster",
                        renderer.pg.K_PLUS: "faster",
                        renderer.pg.K_KP_PLUS: "faster",
                    }
                    action = key_actions.get(event.key)
                    if action:
                        single_step = apply_action(action) or single_step
                elif event.type == renderer.pg.MOUSEBUTTONDOWN and event.button == 1:
                    cell = renderer.map_cell_at(event.pos) if visual.edit_obstacles else None
                    if cell is not None:
                        visual.notify_map_edit(controller.toggle_dynamic_obstacle(cell))
                    else:
                        action = renderer.action_at(event.pos)
                        if action:
                            single_step = apply_action(action) or single_step

            tick_seconds = 1.0 / (controller.config.tick_hz * visual.speed)
            should_tick = (
                not visual.animating
                and not controller.terminated
                and ((not visual.paused and accumulator >= tick_seconds) or single_step)
            )
            if should_tick:
                controller.step()
                visual.begin_transition(
                    controller.robot,
                    controller.heading,
                    duration=min(0.22, tick_seconds * 0.85),
                )
                accumulator = 0.0
            renderer.draw(visual)
            if controller.terminated:
                visual.paused = True
    finally:
        renderer.close()
    return controller.metrics.to_dict()
