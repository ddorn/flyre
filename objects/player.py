from functools import partial
from random import gauss, random

import pygame
from pygame import Vector2

from constants import WORLD, YELLOW
from engine import App, Entity, ImageParticle, SquareParticle
from engine.assets import font, tilemap
from engine.pygame_input import Axis
from engine.utils import clamp, clamp_length, from_polar
from objects import Bullet, SpaceShip
from objects.bullets import DebuffBullet
from objects.skilltree import build_skill_tree, FireDebuff, RegenDebuff


class Player(SpaceShip):
    SCALE = 2
    MAX_THRUST = 0.5

    SIZE = pygame.Vector2(17, 13) * SCALE
    OFFSET = pygame.Vector2(-7, -11)
    JET1 = pygame.Vector2(14, 22)
    JET2 = pygame.Vector2(15, 22)
    GUN = Vector2(15, 5)
    GUN_LEFT = Vector2(11, 11)
    GUN_RIGHT = Vector2(19, 11)
    GUN_FAR_LEFT = Vector2(8, 14)
    GUN_FAR_RIGHT = Vector2(22, 14)

    INVICIBILITY_DURATION = 30

    def __init__(self, pos):
        image = tilemap("spaceships", 0, 0)

        self.score = 0
        self.skill_tree = build_skill_tree()

        super().__init__(pos, image, self.OFFSET, self.SIZE)
        self.max_speed = 5
        self.debuffs.add(RegenDebuff(100000000, 0.01))

    def move_horizontally(self, axis: Axis):
        self.vel.x += axis.value * self.MAX_THRUST * 2

    def move_vertically(self, axis: Axis):
        self.vel.y += axis.value * self.MAX_THRUST * 2

    def fire(self, state):

        guns = []
        if self.nb_bullets % 2 == 1:
            guns.append(self.GUN)
        if self.nb_bullets > 1:
            guns.extend([self.GUN_LEFT, self.GUN_RIGHT])
        if self.nb_bullets > 3:
            guns.extend([self.GUN_FAR_LEFT, self.GUN_FAR_RIGHT])

        for pos in guns:
            if random() < self.fire_chance:
                bullet = partial(
                    DebuffBullet,
                    FireDebuff(self.fire_duration, self.fire_dmg * self.bullet_damage),
                )
            else:
                bullet = Bullet

            crit = random() < self.crit_chance
            state.add(
                bullet(
                    self.sprite_to_screen(pos) + (1, 0),
                    (0, -1),
                    self,
                    self.bullet_damage * (1 if not crit else self.crit_mult),
                    self.bullet_speed,
                    crit,
                )
            )

    def hit(self, bullet):
        super().hit(bullet)
        if not self.invincible:
            App.current_state().do_shake(3)

    def logic(self, state):

        l = self.vel.length()
        if l > 0:
            self.vel *= 1 - min(1, self.MAX_THRUST / l)

        clamp_length(self.vel, self.max_speed)

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
