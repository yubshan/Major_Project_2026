"""Visual and headless simulation runners."""

from __future__ import annotations

import json

from simulation_brain.controller import SimulationController


def run_headless(
    scenario: str, seed: int, episodes: int, max_steps: int | None = None,
    model_path: str | None = None,
) -> list[dict]:
    results = []
    for episode in range(episodes):
        controller = SimulationController(
            scenario=scenario, seed=seed + episode, model_path=model_path
        )
        metrics = controller.run(max_steps=max_steps)
        metrics.update({"episode": episode, "seed": seed + episode, "scenario": scenario})
        results.append(metrics)
        print(json.dumps(metrics, sort_keys=True))
    return results


def run_visual(scenario: str, seed: int, model_path: str | None = None) -> dict:
    from simulation_brain.renderer import SimulationRenderer

    controller = SimulationController(scenario=scenario, seed=seed, model_path=model_path)
    renderer = SimulationRenderer(controller)
    paused = False
    running = True
    accumulator = 0.0
    tick_seconds = 1.0 / controller.config.tick_hz
    try:
        while running:
            elapsed = renderer.clock.tick(controller.config.fps) / 1000.0
            accumulator += elapsed
            single_step = False
            for event in renderer.pg.event.get():
                if event.type == renderer.pg.QUIT:
                    running = False
                elif event.type == renderer.pg.KEYDOWN:
                    if event.key == renderer.pg.K_ESCAPE:
                        running = False
                    elif event.key == renderer.pg.K_SPACE:
                        paused = not paused
                    elif event.key == renderer.pg.K_n:
                        single_step = True
            if (not paused and accumulator >= tick_seconds) or single_step:
                controller.step()
                accumulator = 0.0
            renderer.draw(paused=paused or controller.terminated)
            if controller.terminated:
                paused = True
    finally:
        renderer.close()
    return controller.metrics.to_dict()
