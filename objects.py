from random import gauss

import pygame

from engine.assets import image, tilemap
from constants import W, H, YELLOW
from engine import Object, Particle, SquareParticle
from engine.particles import clamp
from engine.pygame_input import Axis
from engine.utils import load_img


class Player(Object):
    MAX_SPEED = 4
    SIZE = pygame.Vector2(17, 13) * 2
    JET1 = pygame.Vector2(9, 23) * 2
    JET2 = pygame.Vector2(20, 23) * 2

    def __init__(self, pos):
        super().__init__(pos, self.SIZE)

        self.image_offset = 2 * pygame.Vector2(-7, -11)
        self.image = tilemap("spaceships", 0, 0)
        self.image = pygame.transform.scale(self.image, (2 * self.image.get_width(), 2 * self.image.get_height()))

    def move_horizontally(self, value: Axis):
        self.vel.x = value.value * self.MAX_SPEED

    def move_vertically(self, value: Axis):
        self.vel.y = value.value * self.MAX_SPEED

    def logic(self, state):
        if self.vel.length() > self.MAX_SPEED:
            self.vel.scale_to_length(self.MAX_SPEED)

        for jet in (self.JET1, self.JET2):
            state.particles.add(
                SquareParticle(YELLOW).builder()
                    .at(jet + self.pos + self.image_offset, gauss(90, 10))
                    .sized(4)
                    .living(5)
                    .constant_force(self.vel / 2)
                    .velocity(gauss(4, 0.6), )
                    .anim_fade()
                .build()
            )

        super().logic(state)

        self.pos.x = clamp(self.pos.x, 0, W - self.size.x)
        self.pos.y = clamp(self.pos.y, 0, H - self.size.y)

    def draw(self, gfx):
        gfx.surf.blit(self.image, self.image.get_rect(topleft=self.pos + self.image_offset))



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

