from random import gauss

import pygame
from pygame import Vector2

from constants import H, W, YELLOW
from engine import Object, SquareParticle
from engine.assets import tilemap
from engine.object import SpriteObject
from engine.particles import clamp
from engine.pygame_input import Axis
from engine.utils import from_polar


class Player(SpriteObject):
    MAX_SPEED = 4
    SIZE = pygame.Vector2(17, 13) * 2
    JET1 = pygame.Vector2(9, 23) * 2
    JET2 = pygame.Vector2(20, 23) * 2
    GUN1 = Vector2(8, 14) * 2 + (1, 0)
    GUN2 = Vector2(22, 14) * 2 + (1, 0)

    def __init__(self, pos):
        image_offset = 2 * pygame.Vector2(-7, -11)
        image = tilemap("spaceships", 0, 0)
        image = pygame.transform.scale(
            image, (2 * image.get_width(), 2 * image.get_height())
        )

        super().__init__(pos, image, image_offset, self.SIZE)

    def move_horizontally(self, value: Axis):
        self.vel.x = value.value * self.MAX_SPEED

    def move_vertically(self, value: Axis):
        self.vel.y = value.value * self.MAX_SPEED

    def fire(self, state):
        state.add(Bullet(self.GUN1 + self.sprite_pos, -90))
        state.add(Bullet(self.GUN2 + self.sprite_pos, -90))

    def logic(self, state):
        if self.vel.length() > self.MAX_SPEED:
            self.vel.scale_to_length(self.MAX_SPEED)

        for jet in (self.JET1, self.JET2):
            state.particles.add(
                SquareParticle(YELLOW)
                .builder()
                .at(jet + self.pos + self.image_offset, gauss(90, 10))
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
    def __init__(self, number, pos):
        super().__init__(pos)
        self.timer = 0
        self.number = number

    def logic(self, state):
        self.timer += 1

    def draw(self, gfx):
        f = (self.timer // 6) % 600
        x = f % 100
        y = f // 100

        frame = tilemap(f"planet{self.number}", x, y, 100)
        gfx.blit(frame, center=self.pos)


class Bullet(SpriteObject):
    SPEED = 5
    SIZE = (1, 1)

    def __init__(self, pos, angle):
        img = tilemap("sprites", 0, 0, 16)
        rect = img.get_bounding_rect()
        img = img.subsurface(rect)

        vel = from_polar(self.SPEED, angle)
        w, h = img.get_size()

        pos += from_polar(h, angle) + from_polar(w / 2, angle - 90) - vel
        super().__init__(pos, img, (0, 0), img.get_size(), vel)

    def logic(self, state):
        super().logic(state)

        screen = pygame.Rect(0, 0, W, H).inflate(32, 32)
        if not screen.collidepoint(*self.pos):
            self.alive = False
