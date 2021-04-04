from random import gauss, random, uniform

import pygame

from constants import *
from engine import LineParticle, SquareParticle
from engine.assets import tilemap
from engine.object import Object, SpriteObject
from engine.utils import from_polar, vec2int


class BaseBullet:
    def __init__(self, owner, damage=100):
        self.owner = owner
        self.damage = damage

    def logic(self, state):
        if self.owner is state.player:
            from enemies import Enemy

            for enemy in state.get_all(Enemy):
                if self.handle_collision(enemy, state):
                    break
        else:
            self.handle_collision(state.player, state)

    def handle_collision(self, other, state) -> bool:
        return False


class Bullet(SpriteObject, BaseBullet):
    Z = 1
    SPEED = 5
    SIZE = (1, 1)

    def __init__(self, pos, direction, owner, damage=100):
        BaseBullet.__init__(self, owner, damage)

        img = tilemap("sprites", 0, 0, 16)
        rect = img.get_bounding_rect()
        img = img.subsurface(rect)

        vel = pygame.Vector2(direction)
        vel.scale_to_length(self.SPEED)
        w, h = img.get_size()

        angle = -vel.angle_to((1, 0))
        pos += from_polar(h, angle) + from_polar(w / 2, angle + 90) - vel
        SpriteObject.__init__(self, pos, img, (0, 0), img.get_size(), vel, 90 - angle)

    def logic(self, state: "State"):
        SpriteObject.logic(self, state)
        BaseBullet.logic(self, state)

        screen = WORLD.inflate(32, 32)
        if not screen.collidepoint(*self.pos):
            self.alive = False

    def handle_collision(self, object, state):
        if object.rect.collidepoint(self.pos):
            object.hit(self)
            self.alive = False
            for _ in range(12):
                state.particles.add(
                    LineParticle(gauss(8, 2), YELLOW)
                    .builder()
                    .at(
                        self.pos, gauss(270 - self.rotation, 20)
                    )  # the angle is 90-self.rotation
                    .velocity(gauss(5, 1))
                    .sized(uniform(1, 3))
                    .living(10)
                    .anim_fade()
                    .build()
                )
            return True
        return False


class Laser(Object, BaseBullet):
    Z = 1

    def __init__(
        self,
        owner,
        target,
        follow_player_duration=60,
        preshoot_duration=40,
        laser_duration=20,
        damage=100,
    ):
        Object.__init__(self, owner.sprite_to_screen(owner.GUN))
        BaseBullet.__init__(self, owner, damage)
        self.target = target
        self.angle = owner.angle

        self.timer = 0
        self.follow_player_end = follow_player_duration
        self.preshoot_end = preshoot_duration + self.follow_player_end
        self.laser_duration = laser_duration + self.preshoot_end

    def logic(self, state):
        super().logic(state)

        self.timer += 1

        # Keep in sync with the shooter
        if not self.owner.alive:
            self.alive = False
        self.pos = self.owner.sprite_to_screen(self.owner.GUN)
        if self.timer < self.follow_player_end:
            self.angle = self.owner.angle
        else:
            self.owner.angle = self.angle

        # Shooting
        if self.timer > self.preshoot_end:
            state.particles.add(
                LineParticle(20)
                .builder()
                .at(self.pos, self.angle)
                .velocity(30)
                .living(40)
                .hsv(uniform(0, 360), 0.8, 1)
                .build()
            )

            if self.owner is state.player:
                from enemies import Enemy

                for enemy in state.get_all(Enemy):
                    self.handle_collision(enemy, state)
            else:
                self.handle_collision(state.player, state)

        # End
        if self.timer > self.laser_duration:
            self.alive = False

    def handle_collision(self, object, state):
        start = self.pos
        end = self.pos + from_polar(1000, self.angle)

        if p := object.rect.clipline((start, end)):
            object.hit(self)
            start, end = p
            for _ in range(6):
                state.particles.add(
                    SquareParticle()
                    .builder()
                    .at(
                        start + random() * (pygame.Vector2(end) - start),
                        gauss(self.angle, 10),
                    )
                    .velocity(gauss(1, 0.1))
                    .sized(uniform(1, 5))
                    .living(30)
                    .hsv(gauss(20, 20), gauss(1, 0.1))
                    .anim_fade()
                    .build()
                )
            return True
        return False

    def draw(self, gfx):
        if self.timer < self.preshoot_end:
            d = from_polar(3, self.angle)
            for i in range(200):
                p = vec2int(self.pos + d * i)
                gfx.surf.set_at(p, RED)
