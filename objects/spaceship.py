from random import gauss, random

import pygame

from constants import WORLD, YELLOW
from engine import App, LineParticle
from engine.object import Entity
from engine.utils import chrange, clamp_length, from_polar, part_perp_to, random_in_rect


__all__ = ["SpaceShip"]


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


class SpaceShip(Entity):
    GUN = (16, 18)
    MAX_THRUST = 0.2

    def __init__(
        self,
        pos,
        image: pygame.Surface,
        offset=(0, 0),
        size=(1, 1),
        vel=(0, 0),
        rotation=0,
        max_life=1000,
    ):
        super().__init__(pos, image, offset, size, vel, rotation, max_life)

        self.max_speed = 3
        self.bullet_speed = 10
        self.bullet_damage = 100
        self.crit_chance = 0.01
        self.crit_mult = 3

        self.fire_chance = 0.05
        self.fire_dmg = 0.1
        self.fire_duration = 2 * 60

        self.regen = 0
        self.nb_bullets = 1
        self.shield = False

        self.debuffs = set()

    def force_to_move_towards(self, goal):
        direction = goal - self.pos
        direction.scale_to_length(self.max_speed)

        perp = part_perp_to(direction, self.vel)
        return perp

    def force_slow_down_around(self, point, radius=60):
        slow_force = pygame.Vector2()
        dist = self.pos.distance_to(point)
        if dist < radius:
            slow_force = -self.vel * chrange(
                radius - dist, (0, radius), (0, self.MAX_THRUST * 2), 2
            )

        return slow_force

    def force_to_accelerate(self):
        if self.vel.length() < self.max_speed:
            return self.vel * self.MAX_THRUST
        return pygame.Vector2()

    def force_to_slow_down(self, target=0.0):
        if self.vel.length() < target:
            return pygame.Vector2()
        return -self.vel.normalize() * self.MAX_THRUST

    def force_to_avoid_walls(self, radius):
        p = self.pos

        wall = [
            p.x - WORLD.left,
            p.y - WORLD.top,
            WORLD.right - self.size.x - p.x,
            WORLD.bottom - self.size.y - p.y,
        ]
        normals = [(1, 0), (0, 1), (-1, 0), (0, -1)]

        force = pygame.Vector2()
        for dist, normal in zip(wall, normals):
            normal = pygame.Vector2(normal)
            if dist < radius:
                normal.scale_to_length(2 * radius / max(1, dist) * self.MAX_THRUST)
                force += normal

        return force

    def force_to_avoid(self, pos, radius):
        p = self.pos
        distance = pos - p
        dist = distance.length()

        if dist > radius:
            return pygame.Vector2()

        norm = chrange(dist, (0, radius), (0, self.MAX_THRUST * 2), flipped=True)
        distance.scale_to_length(norm)
        return -distance

    def force_to_stay_close(self, pos, radius):
        p = self.pos
        distance = pos - p
        dist = distance.length()

        if dist < radius:
            return pygame.Vector2()

        dist = min(dist, 2 * radius)

        norm = chrange(dist, (radius, 2 * radius), (0, self.MAX_THRUST * 2))
        distance.scale_to_length(norm)
        return distance

    def force_to_stay_up(self, up=0):
        dist = self.pos.y - up

        dist = max(0, dist)
        return (
            pygame.Vector2(0, -1)
            * self.MAX_THRUST
            * chrange(dist, (0, WORLD.height - up), (0, 1))
        )

    def go_to(self, goal=None, precision=30):

        # Go to a random start location
        if goal is None:
            margin = 15
            rect = WORLD.inflate(-2 * margin, -2 * margin)
            rect.height = WORLD.height / 2 - 2 * margin
            goal = random_in_rect(rect)

        while self.pos.distance_to(goal) > precision:
            p = self.pos

            thrust = self.force_to_move_towards(goal)
            thrust += self.force_to_accelerate() * 0.1
            thrust += self.force_slow_down_around(goal, 60)
            thrust += self.force_to_avoid_walls(30)

            clamp_length(thrust, self.MAX_THRUST)

            self.vel += thrust

            yield

    def hover_around(self, duration):
        from . import Enemy

        state = App.current_state()
        player = state.player

        for _ in range(int(duration)):
            thrust = pygame.Vector2()
            # dont go too close to the player
            thrust += self.force_to_avoid(player.pos, 100) * 0.3
            # don't go too far either
            thrust += self.force_to_stay_close(player.pos, 300)
            thrust += self.force_to_slow_down(self.max_speed / 5) * 0.1
            thrust += self.force_to_stay_up(WORLD.height / 4)

            thrust += self.force_to_avoid_walls(30)

            # Avoid other enemies
            for enemy in state.get_all(Enemy):
                if enemy is not self:
                    thrust += self.force_to_avoid(enemy.pos, 50)

            self.vel += clamp_length(thrust, self.MAX_THRUST)
            yield

    def slow_down_and_stop(self):
        # Stopped
        while self.vel.length() != 0:
            self.vel -= self.vel.normalize() * min(self.MAX_THRUST, self.vel.length())
            yield

    def charge_to_player(self):
        direction = self.state.player.pos - self.pos
        direction.scale_to_length(self.MAX_THRUST * 3)
        self.max_speed *= 4
        rotation = self.rotation
        while WORLD.colliderect(self.rect):
            self.vel += direction
            self.rotation = rotation
            self.state.particles.add(self.get_charge_particle(1))
            yield

    def get_charge_particle(self, t):
        direction = self.state.player.pos - self.pos
        angle = -direction.angle_to((1, 0))
        angle = gauss(angle, 10) + 180

        return (
            LineParticle(chrange(t, (0, 1), (2, 15)), YELLOW)
            .builder()
            .at(self.center + from_polar(self.size.length() / 2, angle), angle,)
            .living(10)
            .velocity(chrange(t, (0, 1), (0.5, 3)))
            .anim_fade()
            .build()
        )

    def logic(self, state):
        super().logic(state)

        to_remove = set()
        for debuff in self.debuffs:
            debuff.apply(self)
            if debuff.done:
                to_remove.add(debuff)
        self.debuffs.difference_update(to_remove)


class HorizontalBehavior(SpaceShip):
    def script(self):

        fire_cooldown = Cooldown(20)
        start = True
        enemy = self
        direction = 1  # or -1
        while True:
            if (
                start
                or self.pos.x + enemy.vel.x < WORLD.left
                or self.pos.x + enemy.vel.x + enemy.size.x > WORLD.right
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
