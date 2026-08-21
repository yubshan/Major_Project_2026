"""Pygame dashboard for ground truth, perception, decisions, and metrics."""

from __future__ import annotations

from shared.coordinate_system import FREE, OCCUPIED, UNKNOWN


class SimulationRenderer:
    def __init__(self, controller):
        try:
            import pygame
        except ImportError as exc:
            raise RuntimeError("Pygame is required for --mode visual") from exc
        self.pg = pygame
        self.controller = controller
        self.cell = controller.config.cell_pixels
        map_px = 50 * self.cell
        self.width = map_px * 2 + controller.config.dashboard_width
        self.height = max(map_px, 720)
        pygame.init()
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Project Drishya — Simulation Brain")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("monospace", 17)
        self.small = pygame.font.SysFont("monospace", 14)

    def _draw_grid(self, grid, origin_x: int, title: str, show_victim: bool = False) -> None:
        colors = {FREE: (220, 225, 220), OCCUPIED: (48, 52, 60), UNKNOWN: (105, 110, 120)}
        self.screen.blit(self.font.render(title, True, (235, 235, 240)), (origin_x + 8, 8))
        top = 34
        for row in range(grid.shape[0]):
            for col in range(grid.shape[1]):
                rect = self.pg.Rect(origin_x + col * self.cell, top + row * self.cell, self.cell, self.cell)
                self.pg.draw.rect(self.screen, colors[int(grid[row, col])], rect)
                if self.cell >= 10:
                    self.pg.draw.rect(self.screen, (80, 84, 90), rect, 1)
        if show_victim:
            vr, vc = self.controller.scenario.victim
            center = (origin_x + vc * self.cell + self.cell // 2, top + vr * self.cell + self.cell // 2)
            self.pg.draw.circle(self.screen, (245, 75, 75), center, max(3, self.cell // 3))

        rr, rc = self.controller.robot
        center = (origin_x + rc * self.cell + self.cell // 2, top + rr * self.cell + self.cell // 2)
        self.pg.draw.circle(self.screen, (35, 125, 245), center, max(4, self.cell // 2 - 1))

    def _draw_path(self, origin_x: int) -> None:
        top = 34
        path = self.controller.blackboard.get("navigation/planned_path", [])
        for row, col in path:
            center = (origin_x + col * self.cell + self.cell // 2, top + row * self.cell + self.cell // 2)
            self.pg.draw.circle(self.screen, (250, 190, 45), center, max(2, self.cell // 4))
        target = self.controller.blackboard.get("navigation/target_waypoint")
        if target:
            row, col = target
            rect = self.pg.Rect(origin_x + col * self.cell, top + row * self.cell, self.cell, self.cell)
            self.pg.draw.rect(self.screen, (80, 210, 130), rect, 2)

    def _line(self, text: str, x: int, y: int, color=(220, 220, 225), small=False) -> int:
        font = self.small if small else self.font
        self.screen.blit(font.render(text[:48], True, color), (x, y))
        return y + (18 if small else 23)

    def draw(self, paused: bool = False) -> None:
        self.screen.fill((26, 28, 34))
        map_px = 50 * self.cell
        self._draw_grid(self.controller.ground_truth, 0, "GROUND TRUTH", show_victim=True)
        self._draw_grid(self.controller.occupancy.data, map_px, "ROBOT PERCEPTION")
        self._draw_path(map_px)

        x, y = map_px * 2 + 20, 24
        y = self._line("SIMULATION BRAIN", x, y, (90, 200, 255))
        y = self._line(f"Scenario: {self.controller.scenario.name}", x, y)
        y = self._line(f"Seed: {self.controller.seed}", x, y)
        y = self._line(f"State: {'PAUSED' if paused else 'RUNNING'}", x, y)
        y += 12
        metrics = self.controller.metrics.to_dict()
        for key in ("steps", "coverage_pct", "replans", "collisions", "victim_detections", "rescued"):
            value = metrics[key]
            if isinstance(value, float):
                value = f"{value:.2f}"
            y = self._line(f"{key}: {value}", x, y, small=True)
        y += 12
        trace = self.controller.blackboard.get("decision/trace", {})
        y = self._line("DECISION TRACE", x, y, (255, 200, 90))
        y = self._line(str(trace.get("selected_action", "-")), x, y)
        for part in str(trace.get("status", "-")).split(" "):
            y = self._line(part, x, y, small=True)
        y += 10
        y = self._line("Reason:", x, y)
        reason = str(trace.get("reason", "-"))
        for index in range(0, len(reason), 43):
            y = self._line(reason[index:index + 43], x, y, small=True)
        y += 16
        self._line("SPACE pause | N step | ESC quit", x, y, (165, 170, 180), small=True)
        self.pg.display.flip()

    def close(self) -> None:
        self.pg.quit()

