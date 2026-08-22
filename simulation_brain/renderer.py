"""Presentation-ready Pygame dashboard for Simulation Brain."""

from __future__ import annotations

import math
from typing import Iterable

from modules.decision_logic.contracts import (
    DETECTION_RESULT, PATH_STATUS, PROXIMITY, SIMULATION_MAP_EDIT, now_ms,
)
from shared.coordinate_system import FREE, GRID_HEIGHT, GRID_WIDTH, OCCUPIED, UNKNOWN
from simulation_brain.visual_state import VisualPose, VisualSessionState


class SimulationRenderer:
    """Render one large map, a rescue rover, and a compact explainability panel."""

    COLORS = {
        "background": (20, 25, 34), "panel": (29, 36, 48), "panel_alt": (36, 44, 58),
        "border": (61, 74, 94), "text": (231, 236, 243), "muted": (152, 164, 181),
        "accent": (65, 190, 239), "free": (205, 215, 210), "occupied": (52, 59, 69),
        "unknown": (96, 105, 119), "path": (250, 190, 48), "target": (66, 214, 139),
        "victim": (241, 80, 86), "sensor": (72, 206, 255), "tof": (155, 112, 255),
        "visited": (66, 151, 236), "success": (55, 204, 123), "warning": (255, 184, 77),
        "danger": (245, 86, 92),
    }

    def __init__(self, controller, window_size: tuple[int, int] | None = None):
        try:
            import pygame
        except ImportError as exc:
            raise RuntimeError("Pygame is required for --mode visual") from exc
        self.pg = pygame
        self.controller = controller
        pygame.init()
        if window_size is None:
            info = pygame.display.Info()
            display_width, display_height = info.current_w or 1280, info.current_h or 800
            width = max(760, min(1320, display_width - 40))
            height = max(600, min(860, display_height - 60))
        else:
            width, height = window_size
        self.width, self.height = int(width), int(height)
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Project Drishya — Rescue Rover")
        self.clock = pygame.time.Clock()

        self.dashboard_width = min(controller.config.dashboard_width, max(292, int(self.width * 0.34)))
        cell_from_height = max(7, (self.height - 128) // GRID_HEIGHT)
        cell_from_width = max(7, (self.width - self.dashboard_width - 70) // GRID_WIDTH)
        self.cell = min(controller.config.cell_pixels, cell_from_height, cell_from_width)
        self.map_pixels = self.cell * GRID_WIDTH
        self.map_origin = (24, 68)
        self.dashboard_x = self.map_origin[0] + self.map_pixels + 24
        self.dashboard_rect = pygame.Rect(
            self.dashboard_x, 18, self.width - self.dashboard_x - 18, self.height - 36
        )
        self.title_font = pygame.font.SysFont("dejavusans", 24, bold=True)
        self.heading_font = pygame.font.SysFont("dejavusans", 17, bold=True)
        self.font = pygame.font.SysFont("dejavusans", 14)
        self.small = pygame.font.SysFont("dejavusans", 12)
        self.tiny = pygame.font.SysFont("dejavusans", 11)
        self.button_rects: dict[str, object] = {}
        self._fallback_visual = VisualSessionState.from_controller(controller)

    def display_grid(self, visual: VisualSessionState):
        return self.controller.ground_truth if visual.view_mode == "truth" else self.controller.occupancy.data

    def victim_visible(self, visual: VisualSessionState) -> bool:
        if visual.view_mode == "truth":
            return True
        detection = self.controller.blackboard.get(DETECTION_RESULT, {})
        return detection.get("confidence", 0.0) >= self.controller.config.victim_confirm_threshold

    @staticmethod
    def rover_heading_vector(heading: float) -> tuple[float, float]:
        radians = math.radians(heading)
        return math.cos(radians), -math.sin(radians)

    def _cell_center(self, row: float, col: float) -> tuple[int, int]:
        return (
            round(self.map_origin[0] + (col + 0.5) * self.cell),
            round(self.map_origin[1] + (row + 0.5) * self.cell),
        )

    def _text(self, text: object, x: int, y: int, *, color=None, font=None) -> None:
        surface = (font or self.font).render(str(text), True, color or self.COLORS["text"])
        self.screen.blit(surface, (x, y))

    @staticmethod
    def _wrap(text: str, max_chars: int) -> list[str]:
        lines, current = [], ""
        for word in text.split():
            candidate = f"{current} {word}".strip()
            if len(candidate) <= max_chars:
                current = candidate
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
        return lines or [""]

    def _draw_header(self, visual: VisualSessionState) -> None:
        title = self.title_font.render("PROJECT DRISHYA", True, self.COLORS["accent"])
        self.screen.blit(title, (24, 18))
        subtitle = "ROBOT PERCEPTION" if visual.view_mode == "perception" else "GROUND TRUTH — PRESENTATION VIEW"
        if self.controller.terminated:
            badge = "COMPLETE"
            badge_color = self.COLORS["success"] if self.controller.metrics.rescued else self.COLORS["warning"]
        else:
            badge_color = self.COLORS["success"] if not visual.paused else self.COLORS["warning"]
            badge = "RUNNING" if not visual.paused else "PAUSED"
        rect = self.pg.Rect(self.map_origin[0] + self.map_pixels - 82, 20, 82, 28)
        subtitle_x = 24 + title.get_width() + 18
        subtitle_surface = self.small.render(subtitle, True, self.COLORS["muted"])
        if subtitle_x + subtitle_surface.get_width() + 12 < rect.x:
            self.screen.blit(subtitle_surface, (subtitle_x, 25))
        self.pg.draw.rect(self.screen, badge_color, rect, border_radius=8)
        label = self.small.render(badge, True, (18, 25, 32))
        self.screen.blit(label, label.get_rect(center=rect.center))

    def _draw_map(self, visual: VisualSessionState) -> None:
        grid = self.display_grid(visual)
        colors = {FREE: self.COLORS["free"], OCCUPIED: self.COLORS["occupied"], UNKNOWN: self.COLORS["unknown"]}
        x0, y0 = self.map_origin
        border = self.pg.Rect(x0 - 2, y0 - 2, self.map_pixels + 4, self.map_pixels + 4)
        self.pg.draw.rect(self.screen, self.COLORS["border"], border, width=2, border_radius=3)
        for row in range(GRID_HEIGHT):
            for col in range(GRID_WIDTH):
                rect = self.pg.Rect(x0 + col * self.cell, y0 + row * self.cell, self.cell, self.cell)
                self.pg.draw.rect(self.screen, colors[int(grid[row, col])], rect)
                if self.cell >= 11:
                    self.pg.draw.rect(self.screen, (126, 135, 142), rect, 1)

    def _draw_visited(self, visual: VisualSessionState) -> None:
        radius = max(1, self.cell // 5)
        for row, col in visual.visited:
            self.pg.draw.circle(self.screen, self.COLORS["visited"], self._cell_center(row, col), radius)

    def _draw_moving_obstacles(self) -> None:
        for obstacle_id, (row, col) in self.controller.moving_obstacles.items():
            outer = self.pg.Rect(
                self.map_origin[0] + col * self.cell,
                self.map_origin[1] + row * self.cell,
                self.cell,
                self.cell,
            )
            inner = outer.inflate(-max(2, self.cell // 4), -max(2, self.cell // 4))
            self.pg.draw.rect(self.screen, (244, 132, 55), outer, border_radius=2)
            self.pg.draw.rect(self.screen, (255, 210, 100), inner, 1, border_radius=2)
            if self.cell >= 10:
                self.pg.draw.line(self.screen, (90, 48, 32), outer.topleft, outer.bottomright, 1)
                self.pg.draw.line(self.screen, (90, 48, 32), outer.topright, outer.bottomleft, 1)

    def _draw_detection_radius(self, pose: VisualPose) -> None:
        radius = int(self.controller.config.victim_detection_range_cells * self.cell)
        center = self._cell_center(pose.row, pose.col)
        layer = self.pg.Surface((radius * 2 + 4, radius * 2 + 4), self.pg.SRCALPHA)
        self.pg.draw.circle(layer, (80, 205, 255, 18), (radius + 2, radius + 2), radius)
        self.pg.draw.circle(layer, (80, 205, 255, 65), (radius + 2, radius + 2), radius, 1)
        self.screen.blit(layer, (center[0] - radius - 2, center[1] - radius - 2))

    def _draw_sensors(self, visual: VisualSessionState, pose: VisualPose) -> None:
        if not visual.show_sensors:
            return
        packet = self.controller.blackboard.get(PROXIMITY, {})
        start = self._cell_center(pose.row, pose.col)
        for cells in packet.get("tof_rays", []):
            if cells:
                self.pg.draw.line(self.screen, self.COLORS["tof"], start, self._cell_center(*cells[-1]), 1)
        for cells in packet.get("rays", {}).values():
            if cells:
                self.pg.draw.line(self.screen, self.COLORS["sensor"], start, self._cell_center(*cells[-1]), 2)

    def _draw_path_and_target(self, visual: VisualSessionState) -> None:
        if not visual.show_path:
            return
        path = self.controller.blackboard.get("navigation/planned_path", [])
        if path:
            points = [self._cell_center(*self.controller.robot)] + [self._cell_center(*cell) for cell in path]
            if len(points) > 1:
                self.pg.draw.lines(self.screen, self.COLORS["path"], False, points, max(2, self.cell // 4))
        target = self.controller.blackboard.get("navigation/target_waypoint")
        if target:
            center = self._cell_center(*target)
            radius = max(5, self.cell // 2)
            self.pg.draw.circle(self.screen, self.COLORS["target"], center, radius, 2)
            self.pg.draw.line(self.screen, self.COLORS["target"], (center[0] - radius, center[1]), (center[0] + radius, center[1]), 1)
            self.pg.draw.line(self.screen, self.COLORS["target"], (center[0], center[1] - radius), (center[0], center[1] + radius), 1)

    def _draw_victim(self, visual: VisualSessionState) -> None:
        if not self.victim_visible(visual):
            return
        center = self._cell_center(*self.controller.scenario.victim)
        radius = max(5, int(self.cell * 0.55))
        self.pg.draw.circle(self.screen, (255, 230, 225), center, radius)
        self.pg.draw.circle(self.screen, self.COLORS["victim"], center, radius, 2)
        self.pg.draw.circle(self.screen, self.COLORS["victim"], (center[0], center[1] - radius // 3), max(2, radius // 4))
        self.pg.draw.line(self.screen, self.COLORS["victim"], (center[0], center[1]), (center[0], center[1] + radius // 2), 2)

    def _status_color(self) -> tuple[int, int, int]:
        behavior = self.controller.blackboard.get("decision/state", {}).get("active_behavior", "")
        if behavior in {"EmergencyStop", "SafetyGate"}:
            return self.COLORS["danger"]
        if behavior == "VictimConfirmation":
            return self.COLORS["warning"]
        if self.controller.terminated and self.controller.metrics.rescued:
            return self.COLORS["success"]
        return self.COLORS["accent"]

    def _draw_rover(self, pose: VisualPose) -> None:
        size = max(26, int(self.cell * 2.35))
        surface = self.pg.Surface((size, size), self.pg.SRCALPHA)
        cy = size // 2
        body = self.pg.Rect(int(size * 0.22), int(size * 0.27), int(size * 0.56), int(size * 0.46))
        wheel_w, wheel_h = max(3, size // 7), max(5, size // 4)
        for y in (int(size * 0.18), int(size * 0.58)):
            self.pg.draw.rect(surface, (24, 29, 36), (int(size * 0.19), y, wheel_h, wheel_w), border_radius=2)
            self.pg.draw.rect(surface, (24, 29, 36), (int(size * 0.58), y, wheel_h, wheel_w), border_radius=2)
        self.pg.draw.rect(surface, (38, 131, 166), body, border_radius=max(3, size // 9))
        self.pg.draw.rect(surface, (108, 220, 235), body, 2, border_radius=max(3, size // 9))
        front_x = body.right - 2
        self.pg.draw.rect(surface, (174, 121, 255), (front_x, cy - size // 8, max(3, size // 10), size // 4), border_radius=2)
        for offset in (-size // 8, size // 8):
            self.pg.draw.circle(surface, (91, 225, 255), (front_x, cy + offset), max(2, size // 16))
        self.pg.draw.line(surface, (220, 228, 235), (cy, cy), (cy, int(size * 0.15)), 2)
        self.pg.draw.arc(surface, (220, 228, 235), (cy - size // 8, 1, size // 4, size // 4), 0.2, 2.9, 1)
        self.pg.draw.circle(surface, self._status_color(), (cy, cy), max(3, size // 10))
        self.pg.draw.polygon(surface, (255, 224, 100), [
            (int(size * 0.9), cy), (int(size * 0.73), cy - size // 9), (int(size * 0.73), cy + size // 9)
        ])
        rotated = self.pg.transform.rotozoom(surface, pose.heading, 1.0)
        self.screen.blit(rotated, rotated.get_rect(center=self._cell_center(pose.row, pose.col)))

    def _human_message(self, visual: VisualSessionState) -> str:
        if visual.notification:
            return visual.notification
        map_event = self.controller.blackboard.get(SIMULATION_MAP_EDIT, {})
        if (
            isinstance(map_event, dict)
            and map_event.get("reason") == "moving_obstacle_moved"
            and now_ms() - map_event.get("timestamp_ms", 0) <= 1_500
        ):
            return (
                f"Moving obstacle {map_event.get('id')} shifted to {map_event.get('cell')}; "
                "Dijkstra checked the route again."
            )
        if self.controller.terminated:
            return {
                "victim_rescued": "Victim reached safely. Mission complete.",
                "victim_unreachable": "Victim confirmed, but every safe approach is blocked.",
                "map_fully_explored": "Exploration complete. No reachable mission target remains.",
                "step_limit": "Time limit reached. Robot stopped safely.",
            }.get(self.controller.metrics.termination_reason, "Mission stopped safely.")
        behavior = self.controller.blackboard.get("decision/state", {}).get("active_behavior", "")
        return {
            "RLExplore": "Exploring the nearest useful frontier.",
            "NavigateToTarget": "Following the collision-checked Dijkstra path.",
            "VictimConfirmation": "Victim signal confirmed; preparing a safe route.",
            "EmergencyStop": "Unsafe obstacle detected; movement stopped.",
            "SafetyGate": "Safety gate is holding the robot.",
            "Idle": "Robot is idle and waiting for a mission.",
        }.get(behavior, "Reading sensors and selecting the next safe action.")

    def _card(self, rect, label: str, value: object, accent=None) -> None:
        self.pg.draw.rect(self.screen, self.COLORS["panel_alt"], rect, border_radius=8)
        self.pg.draw.rect(self.screen, self.COLORS["border"], rect, 1, border_radius=8)
        self._text(label.upper(), rect.x + 9, rect.y + 6, color=self.COLORS["muted"], font=self.tiny)
        value_surface = self.heading_font.render(str(value), True, accent or self.COLORS["text"])
        value_font = self.heading_font if value_surface.get_width() <= rect.width - 18 else self.small
        self._text(value, rect.x + 9, rect.y + 23, color=accent or self.COLORS["text"], font=value_font)

    def _draw_dashboard(self, visual: VisualSessionState) -> None:
        rect = self.dashboard_rect
        self.pg.draw.rect(self.screen, self.COLORS["panel"], rect, border_radius=12)
        self.pg.draw.rect(self.screen, self.COLORS["border"], rect, 1, border_radius=12)
        x, y = rect.x + 16, rect.y + 14
        self._text("RESCUE ROVER", x, y, color=self.COLORS["accent"], font=self.title_font)
        y += 34
        self._text(
            f"{self.controller.scenario.name} • seed {self.controller.seed} • edits {self.controller.metrics.dynamic_obstacle_changes} • moves {self.controller.metrics.moving_obstacle_moves}",
            x, y, color=self.COLORS["muted"], font=self.tiny,
        )
        y += 30
        state = self.controller.blackboard.get("decision/state", {})
        path_status = self.controller.blackboard.get(PATH_STATUS, {})
        metrics = self.controller.metrics.to_dict()
        mission_value = (
            "RESCUED" if self.controller.metrics.rescued
            else "STOPPED" if self.controller.terminated
            else state.get("mission_state", "run").upper()
        )
        values = (
            ("Mission", mission_value, self._status_color()),
            ("Behavior", state.get("active_behavior", "Sensing"), None),
            ("Policy", metrics["policy_source"].upper(), None),
            ("Path cost", path_status.get("cost", "—"), self.COLORS["path"]),
            ("Coverage", f"{metrics['coverage_pct']:.1f}%", None),
            ("Detections", metrics["victim_detections"], None),
            ("Replans", metrics["replans"], None),
            ("Collisions", metrics["collisions"], self.COLORS["success"] if not metrics["collisions"] else self.COLORS["danger"]),
        )
        gap, card_height = 8, 50
        card_width = (rect.width - 32 - gap) // 2
        for index, (label, value, accent) in enumerate(values):
            row, col = divmod(index, 2)
            card = self.pg.Rect(x + col * (card_width + gap), y + row * (card_height + gap), card_width, card_height)
            self._card(card, label, value, accent)
        y += 4 * (card_height + gap) + 3
        self._text("CURRENT DECISION", x, y, color=self.COLORS["warning"], font=self.small)
        y += 20
        for line in self._wrap(self._human_message(visual), max(24, (rect.width - 32) // 8))[:3]:
            self._text(line, x, y, font=self.small)
            y += 18
        self._draw_controls(visual, x, max(y + 8, rect.bottom - 142))
        self._text("Keys: Space/N/R/G/S/P/O/D  •  +/- speed", x, rect.bottom - 20, color=self.COLORS["muted"], font=self.tiny)

    def _draw_controls(self, visual: VisualSessionState, x: int, y: int) -> None:
        controls = (
            ("pause", "Run" if visual.paused else "Pause"), ("step", "Step"),
            ("reset", "Reset"), ("view", "Truth" if visual.view_mode == "perception" else "Perception"),
            ("sensors", f"Sensors {'On' if visual.show_sensors else 'Off'}"),
            ("path", f"Path {'On' if visual.show_path else 'Off'}"),
            ("edit", f"Edit {'On' if visual.edit_obstacles else 'Off'}"),
            ("dynamic", f"Moving {'On' if self.controller.moving_obstacles_enabled else 'Off'}"),
            ("slower", "Speed -"), ("faster", f"Speed + {visual.speed:g}x"),
        )
        available, gap = self.dashboard_rect.width - 32, 6
        columns = 5 if self.dashboard_rect.width >= 420 else 3
        rows = math.ceil(len(controls) / columns)
        y = max(y, self.dashboard_rect.bottom - rows * 34 - 35)
        button_width = (available - (columns - 1) * gap) // columns
        self.button_rects = {}
        for index, (action, label) in enumerate(controls):
            row, col = divmod(index, columns)
            rect = self.pg.Rect(x + col * (button_width + gap), y + row * 34, button_width, 28)
            self.button_rects[action] = rect
            self.pg.draw.rect(self.screen, (48, 60, 78), rect, border_radius=6)
            self.pg.draw.rect(self.screen, self.COLORS["border"], rect, 1, border_radius=6)
            text = self.tiny.render(label, True, self.COLORS["text"])
            self.screen.blit(text, text.get_rect(center=rect.center))

    def _draw_legend(self) -> None:
        y = self.map_origin[1] + self.map_pixels + 13
        items: Iterable[tuple[str, tuple[int, int, int]]] = (
            ("Free", self.COLORS["free"]), ("Obstacle", self.COLORS["occupied"]),
            ("Unknown", self.COLORS["unknown"]), ("Dijkstra path", self.COLORS["path"]),
            ("Sensor rays", self.COLORS["sensor"]), ("Victim", self.COLORS["victim"]),
            ("Moving hazard", (244, 132, 55)),
        )
        x = self.map_origin[0]
        for label, color in items:
            item_width = max(70, len(label) * 7 + 28)
            if x + item_width > self.map_origin[0] + self.map_pixels:
                x = self.map_origin[0]
                y += 18
            self.pg.draw.circle(self.screen, color, (x + 5, y + 6), 5)
            self._text(label, x + 14, y, color=self.COLORS["muted"], font=self.tiny)
            x += item_width

    def _draw_completion(self, visual: VisualSessionState) -> None:
        if not self.controller.terminated or visual.animating:
            return
        x, y = self.map_origin
        overlay = self.pg.Surface((self.map_pixels, self.map_pixels), self.pg.SRCALPHA)
        overlay.fill((12, 18, 26, 178))
        self.screen.blit(overlay, (x, y))
        success = self.controller.metrics.rescued
        color = self.COLORS["success"] if success else self.COLORS["warning"]
        title = "VICTIM RESCUED" if success else self.controller.metrics.termination_reason.replace("_", " ").upper()
        title_surface = self.title_font.render(title, True, color)
        center_x, center_y = x + self.map_pixels // 2, y + self.map_pixels // 2
        self.screen.blit(title_surface, title_surface.get_rect(center=(center_x, center_y - 20)))
        subtitle = self.font.render("Press R to replay this scenario", True, self.COLORS["text"])
        self.screen.blit(subtitle, subtitle.get_rect(center=(center_x, center_y + 20)))

    def action_at(self, position: tuple[int, int]) -> str | None:
        for action, rect in self.button_rects.items():
            if rect.collidepoint(position):
                return action
        return None

    def map_cell_at(self, position: tuple[int, int]) -> tuple[int, int] | None:
        x, y = position
        col = (x - self.map_origin[0]) // self.cell
        row = (y - self.map_origin[1]) // self.cell
        if 0 <= row < GRID_HEIGHT and 0 <= col < GRID_WIDTH:
            return int(row), int(col)
        return None

    def _draw_edit_overlay(self, visual: VisualSessionState) -> None:
        if visual.last_edited_cell is not None:
            row, col = visual.last_edited_cell
            rect = self.pg.Rect(
                self.map_origin[0] + col * self.cell,
                self.map_origin[1] + row * self.cell,
                self.cell,
                self.cell,
            )
            color = self.COLORS["danger"] if visual.last_edit_occupied else self.COLORS["success"]
            self.pg.draw.rect(self.screen, color, rect, max(2, self.cell // 4))
        if visual.edit_obstacles:
            cell = self.map_cell_at(self.pg.mouse.get_pos())
            if cell is not None:
                row, col = cell
                rect = self.pg.Rect(
                    self.map_origin[0] + col * self.cell,
                    self.map_origin[1] + row * self.cell,
                    self.cell,
                    self.cell,
                )
                self.pg.draw.rect(self.screen, self.COLORS["warning"], rect, 2)

    def draw(self, visual: VisualSessionState | None = None, paused: bool | None = None) -> None:
        visual = visual or self._fallback_visual
        if paused is not None:
            visual.paused = paused
        self.screen.fill(self.COLORS["background"])
        pose = visual.interpolated_pose()
        self._draw_header(visual)
        self._draw_map(visual)
        map_clip = self.pg.Rect(*self.map_origin, self.map_pixels, self.map_pixels)
        self.screen.set_clip(map_clip)
        self._draw_moving_obstacles()
        self._draw_visited(visual)
        self._draw_detection_radius(pose)
        self._draw_sensors(visual, pose)
        self._draw_path_and_target(visual)
        self._draw_victim(visual)
        self._draw_edit_overlay(visual)
        self._draw_rover(pose)
        self.screen.set_clip(None)
        self._draw_legend()
        self._draw_dashboard(visual)
        self._draw_completion(visual)
        self.pg.display.flip()

    def close(self) -> None:
        self.pg.quit()
