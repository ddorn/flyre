from functools import lru_cache
from glob import glob
from random import gauss, randint, randrange, uniform

import pygame
from pygame import Vector2

from behaviors import EnemyBehavior, HorizontalBehavior, StationaryMultipleShooter
from constants import ANIMATIONS, H, RED, W, WORLD, YELLOW
from engine import (
    Animation,
    App,
    ImageParticle,
    LineParticle,
    Object,
    ShardParticle,
    SquareParticle,
)
from engine.assets import font, tilemap
from engine.object import SpriteObject
from engine.particles import clamp
from engine.pygame_input import Axis
from engine.utils import angle_towards, from_polar, random_in_rect, vec2int


class Entity(SpriteObject):
    """An object with heath and a sprite."""

    INVICIBILITY_DURATION = 0

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
        super().__init__(pos, image, offset, size, vel, rotation)
        self.max_life = max_life
        self.life = max_life
        self.last_hit = 100000000

    def damage(self, amount):
        if self.invincible:
            return

        self.last_hit = 0

        self.life -= amount
        if self.life < 0:
            self.life = 0

        surf = font(20).render(str(amount), False, RED)

        App.current_state().particles.add(
            ImageParticle(surf)
            .builder()
            .at(self.center, 90)
            .velocity(1)
            .sized(10)
            .anim_fade()
            .build()
        )

    def logic(self, state):
        super().logic(state)

        self.last_hit += 1

        if self.life <= 0:
            self.alive = False

    def draw(self, gfx):
        if self.last_hit < 3:
            gfx.surf.blit(
                self.red_image(self.image),
                self.image.get_rect(center=self.sprite_center),
            )
            return

        if self.invincible and self.last_hit % 6 > 3:
            return  # no blit

        super().draw(gfx)

    @staticmethod
    @lru_cache(1000)
    def red_image(image: pygame.Surface):
        img = image.copy()
        mask = pygame.mask.from_surface(img)
        img = mask.to_surface(setcolor=RED)
        img.set_colorkey(0)
        return img

    @property
    def invincible(self):
        return self.last_hit < self.INVICIBILITY_DURATION


class Player(Entity):
    SCALE = 2

    MAX_SPEED = 4
    SIZE = pygame.Vector2(17, 13) * SCALE
    OFFSET = pygame.Vector2(-7, -11)
    JET1 = pygame.Vector2(9, 23)
    JET2 = pygame.Vector2(20, 23)
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


class Enemy(Entity):
    SCALE = 2

    OFFSET = (-8, -9)
    SIZE = Vector2(17, 17) * SCALE
    GUN = (16, 18)

    def __init__(self, pos):
        image = tilemap("spaceships", randrange(0, 3), 1, 32)
        super().__init__(pos, image, self.OFFSET, self.SIZE, rotation=180)
        self.behabvior = StationaryMultipleShooter(self)

    def logic(self, state):
        super().logic(state)
        self.behabvior.logic(state)

        angle_towards_player = -90 + (state.player.pos - self.pos).angle_to((1, 0))

        self.rotation = angle_towards(self.rotation, angle_towards_player, 2)

    def fire(self, state, direction=(0, 1)):
        state.add(Bullet(self.sprite_to_screen(self.GUN), direction, self))

    def hit(self, bullet):
        self.damage(bullet.damage)

    def draw(self, gfx):
        super().draw(gfx)
        # gfx.surf.set_at(vec2int(self.sprite_to_screen(self.GUN)), "red")

    def on_death(self, state):
        state.add(Enemy((uniform(WORLD.left, WORLD.right), -30)))

        state.player.did_kill(self)


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

            number = randrange(self.TOTAL_PLANETS)
            positions = [planet.pos for planet in state.get_all(Planet)]
            # planet can be none if it can't place it, so I keep the old planet alive until I can place it.
            planet = Planet.random_planet(number, positions, WORLD.top - 200)

            if planet is not None:
                self.alive = False
                state.add(planet)

    def draw(self, gfx):
        frame = self.animation.image()
        gfx.blit(frame, center=self.pos)


class Bullet(SpriteObject):
    SPEED = 5
    SIZE = (1, 1)

    def __init__(self, pos, direction, owner, damage=100):
        self.owner = owner
        self.damage = damage

        img = tilemap("sprites", 0, 0, 16)
        rect = img.get_bounding_rect()
        img = img.subsurface(rect)

        vel = pygame.Vector2(direction)
        vel.scale_to_length(self.SPEED)
        w, h = img.get_size()

        angle = -vel.angle_to((1, 0))
        pos += from_polar(h, angle) + from_polar(w / 2, angle + 90) - vel
        super().__init__(pos, img, (0, 0), img.get_size(), vel, 90 - angle)

    def logic(self, state: "State"):
        super().logic(state)

        screen = WORLD.inflate(32, 32)
        if not screen.collidepoint(*self.pos):
            self.alive = False

        if self.owner is state.player:
            for enemy in state.get_all(Enemy):
                self.handle_collision(enemy, state)

        else:
            self.handle_collision(state.player, state)

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
