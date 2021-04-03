from glob import glob
from random import gauss, randint, randrange, uniform

import pygame
from pygame import Vector2

from behaviors import EnemyBehavior, HorizontalBehavior, StationaryMultipleShooter
from constants import ANIMATIONS, H, W, YELLOW
from engine import Animation, Object, SquareParticle
from engine.assets import tilemap
from engine.object import SpriteObject
from engine.particles import clamp
from engine.pygame_input import Axis
from engine.utils import angle_towards, from_polar, vec2int


class Player(SpriteObject):
    SCALE = 2

    MAX_SPEED = 4
    SIZE = pygame.Vector2(17, 13) * SCALE
    OFFSET = pygame.Vector2(-7, -11)
    JET1 = pygame.Vector2(9, 23)
    JET2 = pygame.Vector2(20, 23)
    GUN1 = Vector2(8, 14)
    GUN2 = Vector2(22, 14)

    def __init__(self, pos):
        image = tilemap("spaceships", 0, 0)

        super().__init__(pos, image, self.OFFSET, self.SIZE)

    def move_horizontally(self, value: Axis):
        self.vel.x = value.value * self.MAX_SPEED

    def move_vertically(self, value: Axis):
        self.vel.y = value.value * self.MAX_SPEED

    def fire(self, state):
        state.add(Bullet(self.sprite_to_screen(self.GUN1) + (1, 0), (0, -1)))
        state.add(Bullet(self.sprite_to_screen(self.GUN2) + (1, 0), (0, -1)))

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

        self.pos.x = clamp(self.pos.x, 0, W - self.size.x)
        self.pos.y = clamp(self.pos.y, 0, H - self.size.y)


class Planet(Object):
    Z = -1
    TOTAL_PLANETS = len(glob(str(ANIMATIONS) + "/planet*.json"))

    def __init__(self, number, pos, speed=2):
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
                pos = uniform(0, W), y
            else:
                pos = uniform(0, W), uniform(-H / 2, H)

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

        if self.pos.y > H + self.size.y:

            number = randrange(self.TOTAL_PLANETS)
            positions = [planet.pos for planet in state.get_all(Planet)]
            # planet can be none if it can't place it, so I keep the old planet alive until I can place it.
            planet = Planet.random_planet(number, positions, -H / 2)

            if planet is not None:
                self.alive = False
                state.add(planet)

    def draw(self, gfx):
        frame = self.animation.image()
        gfx.blit(frame, center=self.pos)


class Bullet(SpriteObject):
    SPEED = 5
    SIZE = (1, 1)

    def __init__(self, pos, direction):
        img = tilemap("sprites", 0, 0, 16)
        rect = img.get_bounding_rect()
        img = img.subsurface(rect)

        vel = pygame.Vector2(direction)
        vel.scale_to_length(self.SPEED)
        w, h = img.get_size()

        angle = -vel.angle_to((1, 0))
        print(angle, direction)
        pos += from_polar(h, angle) + from_polar(w / 2, angle + 90) - vel
        super().__init__(pos, img, (0, 0), img.get_size(), vel, 90 - angle)

    def logic(self, state):
        super().logic(state)

        screen = pygame.Rect(0, 0, W, H).inflate(32, 32)
        if not screen.collidepoint(*self.pos):
            self.alive = False


class Enemy(SpriteObject):
    SCALE = 2

    OFFSET = (-8, -9)
    SIZE = Vector2(17, 17) * SCALE
    GUN = (16, 18)

    def __init__(self, pos):
        image = tilemap("spaceships", 0, 1, 32)
        super().__init__(pos, image, self.OFFSET, self.SIZE)
        self.behabvior = StationaryMultipleShooter(self)

    def logic(self, state):
        super().logic(state)
        self.behabvior.logic(state)

        angle_towards_player = 90 + (state.player.pos - self.pos).angle_to((1, 0))

        self.rotation = angle_towards(self.rotation, angle_towards_player, 2)

    def fire(self, state, direction=(0, 1)):
        state.add(Bullet(self.sprite_to_screen(self.GUN), direction))

    def draw(self, gfx):
        super().draw(gfx)
        gfx.surf.set_at(vec2int(self.sprite_to_screen(self.GUN)), "red")


class DrawnVector(Object):
    def __init__(self, anchor, vec, color="red", scale=20):
        super().__init__(anchor)
        self.anchor = anchor
        self.color = color
        self.vec = vec
        self.scale = scale

    def draw(self, gfx):
        pygame.draw.line(
            gfx.surf, self.color, self.anchor, self.anchor + self.vec * self.scale
        )
