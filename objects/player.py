from random import gauss, random

import pygame
from pygame import Vector2

from constants import WORLD, YELLOW
from engine import App, Entity, ImageParticle, SquareParticle
from engine.assets import font, tilemap
from engine.pygame_input import Axis
from engine.utils import clamp
from objects import Bullet, SpaceShip


class Player(SpaceShip):
    SCALE = 2

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
        self.max_speed = 4

    def move_horizontally(self, value: Axis):
        self.vel.x = value.value * self.max_speed

    def move_vertically(self, value: Axis):
        self.vel.y = value.value * self.max_speed

    def fire(self, state):

        for pos in (self.GUN1, self.GUN2):
            crit = random() < self.crit_chance
            state.add(
                Bullet(
                    self.sprite_to_screen(pos) + (1, 0),
                    (0, -1),
                    self,
                    self.bullet_damage * (1 if not crit else self.crit_mult),
                    self.bullet_speed,
                    crit,
                )
            )

    def hit(self, bullet):
        if not self.invincible:
            App.current_state().do_shake(3)
            self.damage(bullet.damage)

    def logic(self, state):
        if self.vel.length() > self.max_speed:
            self.vel.scale_to_length(self.max_speed)

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
