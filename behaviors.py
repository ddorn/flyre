from random import gauss, random, uniform

import pygame

from constants import DEBUG, H, W
from engine.utils import chrange


class Cooldown:
    def __init__(self, delay):
        self.delay = delay
        self.timer = 0

    def tick(self, fire_probability):
        self.timer += 1

        if self.timer > self.delay and random() < fire_probability:
            self.timer = 0
            return True
        return False


class EnemyBehavior:
    def __init__(self, enemy):
        self.enemy = enemy
        self.generator = self.script()
        self.state = None

    def script(self):
        yield

    def logic(self, state):
        self.state = state
        try:
            next(self.generator)
        except StopIteration:
            pass


class HorizontalBehavior(EnemyBehavior):
    def script(self):

        fire_cooldown = Cooldown(20)
        start = True
        enemy = self.enemy
        direction = 1  # or -1
        while True:
            if (
                start
                or self.enemy.pos.x + enemy.vel.x < 0
                or self.enemy.pos.x + enemy.vel.x + enemy.size.x > W
            ):
                start = False
                direction *= -1
                enemy.vel.x = gauss(2, 0.3) * direction

            if abs(enemy.pos.x - self.state.player.pos.x) < 20:
                if fire_cooldown.tick(0.1):
                    enemy.fire(self.state)
            else:
                fire_cooldown.tick(0)

            yield


class StationaryMultipleShooter(EnemyBehavior):
    def script(self):
        enemy = self.enemy
        from objects import DrawnVector

        if DEBUG:
            self.state.add(DrawnVector(enemy.pos, enemy.vel))
            direction_draw = self.state.add(
                DrawnVector((100, 100), enemy.vel, "orange")
            )
            goal_draw = self.state.add(DrawnVector((0, 0), enemy.vel, "green", scale=1))
            perp_draw = self.state.add(DrawnVector((100, 100), enemy.vel, "pink"))
        speed = gauss(2, 0.3)
        enemy.vel.x = speed

        slow_frames = 0

        while True:
            # Go to a random start location
            goal = pygame.Vector2(uniform(W / 4, W * 3 / 4), uniform(30, H / 4))

            while enemy.pos.distance_to(goal) > 20:
                direction = goal - enemy.pos
                direction.scale_to_length(speed)

                perp = direction - enemy.vel.normalize() * enemy.vel.normalize().dot(
                    direction
                )
                enemy.vel += perp * 0.1

                dist = enemy.pos.distance_to(goal)
                slow_down_radius = 60
                if dist < slow_down_radius:
                    enemy.vel.scale_to_length(
                        speed * (0.2 + 0.8 * dist / slow_down_radius) ** (0.5)
                    )

                if slow_frames > 0:
                    slow_frames -= 1
                    enemy.vel.scale_to_length(
                        speed * chrange(-slow_frames, (-30, 0), (0.2, 1))
                    )

                if DEBUG:
                    goal_draw.vec = goal
                    perp_draw.vec = perp
                    direction_draw.vec = direction

                yield

            for _ in range(3):
                enemy.fire(self.state, self.state.player.pos - enemy.pos)
                yield from range(8)

            slow_frames = 30
