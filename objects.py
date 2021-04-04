from glob import glob
from random import choice, gauss, randint, uniform

import pygame
from pygame import Vector2

from bullets import Bullet
from constants import ANIMATIONS, WORLD, YELLOW
from engine import (
    Animation,
    App,
    ImageParticle,
    Object,
    SquareParticle,
)
from engine.assets import font, tilemap
from engine.object import Entity
from engine.particles import clamp
from engine.pygame_input import Axis
from engine.utils import random_in_rect


class Player(Entity):
    SCALE = 2

    MAX_SPEED = 4
    SIZE = pygame.Vector2(17, 13) * SCALE
    OFFSET = pygame.Vector2(-7, -11)
    JET1 = pygame.Vector2(14, 22)
    JET2 = pygame.Vector2(15, 22)
    GUN1 = Vector2(8, 14)
    GUN2 = Vector2(22, 14)

    INVICIBILITY_DURATION = 30

    def __init__(self, pos):
        image = tilemap("spaceships", 0, 0)

        self.score = 0

        super().__init__(pos, image, self.OFFSET, self.SIZE)

    def move_horizontally(self, value: Axis):
        self.vel.x = value.value * self.MAX_SPEED

    def move_vertically(self, value: Axis):
        self.vel.y = value.value * self.MAX_SPEED

    def fire(self, state):
        state.add(Bullet(self.sprite_to_screen(self.GUN1) + (1, 0), (0, -1), self))
        state.add(Bullet(self.sprite_to_screen(self.GUN2) + (1, 0), (0, -1), self))

    def hit(self, bullet):
        if not self.invincible:
            App.current_state().do_shake(3)
            self.damage(bullet.damage)

    def logic(self, state):
        if self.vel.length() > self.MAX_SPEED:
            self.vel.scale_to_length(self.MAX_SPEED)

        for jet in (self.JET1, self.JET2):
            state.particles.add(
                SquareParticle(YELLOW)
                .builder()
                .at(self.sprite_to_screen(jet), gauss(90, 10))
                .sized(4)
                .living(5)
                .constant_force(self.vel / 2)
                .velocity(gauss(4, 0.6),)
                .anim_fade()
                .build()
            )

        super().logic(state)

        self.pos.x = clamp(self.pos.x, WORLD.left, WORLD.right - self.size.x)
        self.pos.y = clamp(self.pos.y, WORLD.top, WORLD.bottom - self.size.y)

        state.debug.point(*self.center)

    def draw(self, gfx):
        super().draw(gfx)
        score = font(20).render(str(self.score), False, YELLOW)
        gfx.blit(score, topleft=WORLD.topleft + Vector2(10, 7))

    def did_kill(self, enemy):
        bonus = 100
        self.score += bonus

        surf = font(20).render(str(bonus), False, YELLOW)
        App.current_state().particles.add(
            ImageParticle(surf)
            .builder()
            .at(enemy.pos, -90)
            .velocity(1)
            .sized(10)
            .living(60)
            .acceleration(-1 / 60)
            .build()
        )


class Planet(Object):
    Z = -1
    TOTAL_PLANETS = len(glob(str(ANIMATIONS) + "/planet*.json"))

    def __init__(self, number, pos, speed=2):
        self.number = number
        self.animation = Animation(f"planet{number}", speed)

        super().__init__(
            pos, (self.animation.tile_size, self.animation.tile_size), vel=(0, 0.5)
        )

    @classmethod
    def random_planet(cls, number, avoid_positions, y=None, max_trials=1000):
        done = False
        trials = 0
        while not done:
            trials += 1
            if y is not None:
                pos = uniform(WORLD.left, WORLD.right), y
            else:
                pos = random_in_rect(WORLD, (0, 1), (-1 / 2, 1))

            # Any position is too close
            for p in avoid_positions:
                if p.distance_to(pos) < 200:
                    break
            else:
                done = True

            if trials > max_trials:
                return None

        speed = randint(2, 5)
        return Planet(number, pos, speed)

    def logic(self, state):
        super().logic(state)
        self.animation.logic()

        if self.pos.y > WORLD.bottom + self.size.y:

            numbers_taken = [planet.number for planet in state.get_all(Planet)]
            number = choice(
                [i for i in range(self.TOTAL_PLANETS) if i not in numbers_taken]
            )
            positions = [planet.pos for planet in state.get_all(Planet)]
            # planet can be none if it can't place it, so I keep the old planet alive until I can place it.
            planet = Planet.random_planet(number, positions, WORLD.top - 200)

            if planet is not None:
                self.alive = False
                state.add(planet)

    def draw(self, gfx):
        frame = self.animation.image()
        gfx.blit(frame, center=self.pos)


class Debug(Object):
    Z = 1000000000

    def __init__(self):
        super().__init__((0, 0))
        self.points = []
        self.vectors = []

    def point(self, x, y, color="red"):
        self.points.append((x, y, color))
        return (x, y)

    def vector(self, vec, anchor, color="red", scale=1):
        self.vectors.append((Vector2(anchor), Vector2(vec) * scale, color))
        return vec

    def draw(self, gfx):
        for (x, y, color) in self.points:
            pygame.draw.circle(gfx.surf, color, (x, y), 2)

        for (anchor, vec, color) in self.vectors:
            pygame.draw.line(gfx.surf, color, anchor, anchor + vec)

        self.points.clear()
        self.vectors.clear()
