"""Small optional Pygame dashboard for live curriculum training."""

from __future__ import annotations


class TrainingDashboard:
    """Closing the window disables drawing but deliberately does not stop training."""

    def __init__(self, enabled: bool = False):
        self.enabled = enabled
        self._pygame = None
        self._screen = None
        if enabled:
            try:
                import pygame
                pygame.init()
                self._pygame = pygame
                self._screen = pygame.display.set_mode((840, 480))
                pygame.display.set_caption("Simulation Brain — PPO Curriculum")
            except Exception:
                self.enabled = False

    def update(self, stage: str, records: list[dict], total_timesteps: int) -> None:
        if not self.enabled or self._pygame is None or self._screen is None:
            return
        pygame = self._pygame
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.display.quit()
                self.enabled = False
                return
        screen = self._screen
        screen.fill((15, 23, 34))
        font = pygame.font.SysFont("sans", 22)
        small = pygame.font.SysFont("sans", 17)
        recent = records[-20:]
        rescued = sum(bool(row.get("rescued")) for row in recent)
        rescue_rate = rescued / max(1, len(recent))
        latest = records[-1] if records else {}
        lines = (
            ("House Rescue PPO Curriculum", font, (85, 214, 190)),
            (f"Stage: {stage}", small, (235, 241, 247)),
            (f"Total timesteps: {total_timesteps:,}", small, (235, 241, 247)),
            (f"Episode reward: {float(latest.get('episode_reward', 0)):.2f}", small, (235, 241, 247)),
            (f"Rolling rescue rate (20): {rescue_rate:.0%}", small, (235, 241, 247)),
            (f"Collisions: {latest.get('collisions', 0)}", small, (255, 174, 102)),
            (f"Detection / rescue steps: {latest.get('detection_step', '—')} / {latest.get('steps', '—')}", small, (235, 241, 247)),
            (f"Coverage: {float(latest.get('coverage_pct', 0)):.1f}%", small, (235, 241, 247)),
        )
        y = 28
        for message, face, color in lines:
            screen.blit(face.render(message, True, color), (30, y))
            y += 47 if face is font else 35

        rewards = [float(row.get("episode_reward", 0)) for row in records[-100:]]
        if len(rewards) > 1:
            lo, hi = min(rewards), max(rewards)
            span = max(1.0, hi - lo)
            points = [
                (390 + i * 420 / (len(rewards) - 1), 420 - (value - lo) * 300 / span)
                for i, value in enumerate(rewards)
            ]
            pygame.draw.lines(screen, (85, 214, 190), False, points, 3)
            screen.blit(small.render("Episode reward (last 100)", True, (169, 186, 201)), (390, 80))
        pygame.display.flip()

    def close(self) -> None:
        if self._pygame is not None:
            self._pygame.quit()
        self.enabled = False
