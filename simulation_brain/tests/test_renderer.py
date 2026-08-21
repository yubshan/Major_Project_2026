import os

import pytest

from simulation_brain.controller import SimulationController


def test_pygame_renderer_smoke(monkeypatch):
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    monkeypatch.setenv("SDL_AUDIODRIVER", "dummy")
    pytest.importorskip("pygame")
    from simulation_brain.renderer import SimulationRenderer

    controller = SimulationController("open-room", seed=2)
    controller.step()
    renderer = SimulationRenderer(controller)
    renderer.draw()
    renderer.close()
